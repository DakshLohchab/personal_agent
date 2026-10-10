"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useRef, useState } from "react";
import { Comparison } from "@/components/Comparison";
import { ScenarioGraph } from "@/components/ScenarioGraph";
import { SpecialistPanel } from "@/components/SpecialistPanel";
import { Timeline } from "@/components/Timeline";
import { api } from "@/lib/api";
import type { AgentRunResult, AIResponse, DecisionInterpretation } from "@/lib/types";

const suggestions = [
  "I have ₹50,000. Laptop, trip, or save?",
  "Should I quit my job to freelance full-time?",
  "Rent vs buy: ₹18L down payment, 7-year horizon",
];

type Dictation = {
  lang: string;
  interimResults: boolean;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};
type DictationWindow = Window & {
  SpeechRecognition?: new () => Dictation;
  webkitSpeechRecognition?: new () => Dictation;
};

export default function HomePage() {
  const [decision, setDecision] = useState("");
  const [context, setContext] = useState("");
  const [interpretation, setInterpretation] = useState<DecisionInterpretation | null>(null);
  const [aiExplanation, setAiExplanation] = useState<AIResponse["explanation"] | null>(null);
  const [clarificationAnswers, setClarificationAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<AgentRunResult | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [whatIf, setWhatIf] = useState("5000");
  const [showMemories, setShowMemories] = useState(false);
  const [showTrace, setShowTrace] = useState(false);
  const [trace, setTrace] = useState<string[]>(["Decision core ready", "Waiting for a decision"]);
  const [attachments, setAttachments] = useState<string[]>([]);
  const [composerError, setComposerError] = useState("");
  const [isListening, setIsListening] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const dictation = useRef<Dictation | null>(null);
  const queryClient = useQueryClient();
  const memories = useQuery({ queryKey: ["memories"], queryFn: api.memories, enabled: showMemories });
  const relevantMemories = useQuery({
    queryKey: ["relevant-memories", decision],
    queryFn: () => api.relevantMemories(decision),
    enabled: showMemories && decision.trim().length > 0,
  });
  const interpret = useMutation({
    mutationFn: ({ decision: query, context: details }: { decision: string; context?: string }) =>
      api.interpret(query, details || undefined),
    onMutate: () => setTrace((items) => [...items, "Structuring the decision"]),
    onSuccess: (response) => {
      setInterpretation(response.interpretation);
      setAiExplanation(response.explanation);
      setClarificationAnswers(Object.fromEntries(
        (response.interpretation.missing_field_prompts ?? []).map((prompt) => [prompt.key, ""]),
      ));
      setResult(null);
      setTrace((items) => [...items, "Interpretation ready"]);
    },
  });
  const run = useMutation({
    mutationFn: (request: DecisionInterpretation) => api.run(request, false, relevantMemories.data ?? []),
    onMutate: () => setTrace((items) => [...items, "Running deterministic scenarios", "Reviewing trade-offs"]),
    onSuccess: (response) => {
      setResult(response);
      setSelected(response.simulation_outputs[0]?.option_name ?? null);
      setTrace((items) => [...items, `Run ${response.status}`]);
    },
  });
  const approveMemory = useMutation({
    mutationFn: api.approveMemory,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["memories"] }),
  });
  const forgetMemory = useMutation({
    mutationFn: api.forgetMemory,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["memories"] }),
  });
  const runStatus = useQuery({
    queryKey: ["run", result?.run_id],
    queryFn: () => api.runStatus(result!.run_id),
    enabled: result?.status === "queued" || result?.status === "running",
    refetchInterval: (query) => query.state.data?.status === "completed" || query.state.data?.status === "failed" ? false : 1200,
  });
  const displayed = runStatus.data?.status === "completed" ? runStatus.data : result;
  const selectedOutput = useMemo(
    () => displayed?.simulation_outputs.find((item) => item.option_name === selected) ?? displayed?.simulation_outputs[0],
    [displayed, selected],
  );
  const canSimulate = Boolean(interpretation && (
    interpretation.simulation_readiness === "READY_TO_SIMULATE" ||
    (interpretation.simulation_readiness === undefined && interpretation.current_state &&
      interpretation.candidate_options.some((option) => option.scenario))
  ));
  const outcomeSummary = useMemo(() => {
    const outputs = displayed?.simulation_outputs ?? [];
    if (!outputs.length) return null;
    const highestEndingCash = outputs.reduce((best, item) =>
      Number(item.result.metrics.ending_cash) > Number(best.result.metrics.ending_cash) ? item : best,
    );
    const strongestCashFloor = outputs.reduce((best, item) =>
      Number(item.result.metrics.minimum_cash) > Number(best.result.metrics.minimum_cash) ? item : best,
    );
    const money = (value: string) => `₹${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
    return `Across ${outputs.length} modeled ${outputs.length === 1 ? "future" : "futures"}, ${highestEndingCash.option_name} has the highest projected ending cash (${money(highestEndingCash.result.metrics.ending_cash)}). ${strongestCashFloor.option_name} keeps the highest minimum cash (${money(strongestCashFloor.result.metrics.minimum_cash)}). These are financial projections; non-financial outcomes depend on what matters most to you.`;
  }, [displayed]);
  const reset = () => {
    setDecision(""); setContext(""); setInterpretation(null); setAiExplanation(null); setResult(null); setSelected(null);
    setClarificationAnswers({});
    setAttachments([]); setComposerError("");
    setTrace(["Decision core ready", "Waiting for a decision"]);
  };
  const submitDecision = () => {
    if (!decision.trim() || interpret.isPending) return;
    setInterpretation(null); setAiExplanation(null); setResult(null);
    interpret.mutate({ decision, context: context || undefined });
  };
  const continueWithAnswers = () => {
    if (!interpretation || interpret.isPending) return;
    const prompts = interpretation.missing_field_prompts ?? [];
    const missingAnswer = prompts.find((prompt) => prompt.required && !clarificationAnswers[prompt.key]?.trim());
    if (missingAnswer) {
      setComposerError(`Please answer: ${missingAnswer.label}.`);
      return;
    }
    const answers = prompts.map((prompt) => {
      const answer = clarificationAnswers[prompt.key]?.trim();
      if (!answer) return "";
      if (prompt.key === "horizon_months") return `Planning horizon: ${answer} months`;
      if (prompt.key === "monthly_income") return `Monthly income: ₹${answer}`;
      if (prompt.key === "starting_cash") return `Cash available: ₹${answer}`;
      if (prompt.key === "cash_floor") return `Emergency reserve: ₹${answer}`;
      if (prompt.key === "laptop_cost") return `Laptop price: ₹${answer}`;
      if (prompt.key === "trip_cost") return `Trip cost: ₹${answer}`;
      return `${prompt.label}: ₹${answer}`;
    }).filter(Boolean).join("\n");
    const nextContext = [context, `Answers to follow-up questions:\n${answers}`].filter(Boolean).join("\n\n");
    setContext(nextContext); setComposerError(""); setAiExplanation(null); setResult(null);
    interpret.mutate({ decision, context: nextContext });
  };
  const attachFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    const addedNames: string[] = [];
    const additions: string[] = [];
    for (const file of Array.from(files)) {
      if (!/\.(txt|md|csv|json)$/i.test(file.name)) {
        setComposerError(`${file.name}: attach a .txt, .md, .csv, or .json file.`);
        continue;
      }
      if (file.size > 40_000) {
        setComposerError(`${file.name}: text attachments must be 40 KB or smaller.`);
        continue;
      }
      additions.push(`\n\nAttached file: ${file.name}\n${await file.text()}`);
      addedNames.push(file.name);
    }
    if (additions.length) {
      setContext((current) => `${current}${additions.join("")}`.trim());
      setAttachments((current) => [...current, ...addedNames]);
      setComposerError("");
    }
    if (fileInput.current) fileInput.current.value = "";
  };
  const toggleDictation = () => {
    if (isListening) { dictation.current?.stop(); return; }
    const dictationApi = window as DictationWindow;
    const Recognition = dictationApi.SpeechRecognition ?? dictationApi.webkitSpeechRecognition;
    if (!Recognition) {
      setComposerError("Voice input is not supported in this browser. You can type or attach a text file.");
      return;
    }
    const recognition = new Recognition();
    recognition.lang = navigator.language || "en-US";
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results).map((item) => item[0]?.transcript ?? "").join(" ").trim();
      if (transcript) setDecision((current) => `${current}${current ? " " : ""}${transcript}`);
    };
    recognition.onerror = () => { setComposerError("Voice input could not start. Check microphone access and try again."); setIsListening(false); };
    recognition.onend = () => setIsListening(false);
    dictation.current = recognition;
    setComposerError(""); setIsListening(true); recognition.start();
  };
  const rerunWhatIf = () => {
    if (!interpretation || !selectedOutput) return;
    const updated: DecisionInterpretation = {
      ...interpretation,
      candidate_options: interpretation.candidate_options.map((option) =>
        option.name === selectedOutput.option_name && option.scenario
          ? { ...option, scenario: {
              ...option.scenario,
              parent_id: option.scenario.id,
              id: `${option.scenario.id}-what-if-${Date.now()}`,
              name: `${option.scenario.name} · What If`,
              deltas: { ...option.scenario.deltas, cash: whatIf },
            } }
          : option,
      ),
    };
    run.mutate(updated);
  };

  return (
    <main className="sandbox-shell">
      <aside className={`sidebar ${showMemories ? "sidebar-open" : ""}`}>
        <div className="brand-lockup"><span className="brand-orb" /><span><b>LIFE SANDBOX</b><small>DECISION INTELLIGENCE</small></span></div>
        <button className="new-decision" onClick={reset} type="button"><span>＋</span> New decision</button>
        <button className="side-action" onClick={() => setShowMemories((value) => !value)} type="button">◈ <span>Saved context</span><span className="side-chevron">{showMemories ? "−" : "+"}</span></button>
        {showMemories && <div className="memory-list">
          {memories.isLoading && <p className="muted-small">Loading saved context…</p>}
          {memories.isError && <p className="error-copy">{memories.error.message}</p>}
          {memories.data?.filter((memory) => memory.status !== "deleted").map((memory) => <article className="memory-item" key={memory.memory_id}>
            <p>{memory.content}</p><small>{memory.memory_type} · {memory.status}</small>
            <div className="memory-actions">{memory.status === "candidate" && <button onClick={() => approveMemory.mutate(memory.memory_id)} type="button">Approve</button>}<button onClick={() => forgetMemory.mutate(memory.memory_id)} type="button">Forget</button></div>
          </article>)}
          {memories.data?.filter((memory) => memory.status !== "deleted").length === 0 && <p className="muted-small">Approved context will appear here.</p>}
        </div>}
        <div className="sidebar-bottom"><span className="online-dot" /> API connected when you run a decision</div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <button aria-label="Toggle saved context" className="icon-button mobile-only" onClick={() => setShowMemories((value) => !value)} type="button">☰</button>
          <div className="breadcrumb">Workspace <span>/</span> <strong>{decision ? "Decision analysis" : "New decision"}</strong></div>
          <div className="topbar-spacer" />
          <div className={`status-pill ${interpret.isPending || run.isPending ? "status-working" : displayed ? "status-ready" : ""}`}><i />{interpret.isPending ? "interpreting" : run.isPending ? "simulating" : displayed ? displayed.status : "idle"}</div>
          <button aria-expanded={showTrace} className={`icon-button ${showTrace ? "icon-selected" : ""}`} onClick={() => setShowTrace((value) => !value)} type="button" title="Toggle live process trace">⌁</button>
        </header>

        <div className="content-scroll">
          <div className="content-column">
            {!interpretation && !displayed && <section className="welcome-block">
              <div className="hero-orb" />
              <p className="eyebrow">YOUR DECISION, MADE LEGIBLE</p>
              <h1>Explore the futures<br />before you decide.</h1>
              <p className="welcome-copy">Tell me the choice you’re facing. We’ll map the options, run each one through a deterministic model, and show the trade-offs.</p>
              <div className="suggestions">{suggestions.map((item) => <button className="suggestion" key={item} onClick={() => setDecision(item)} type="button">{item}<span>↗</span></button>)}</div>
            </section>}

            {interpretation && <section className="result-section">
              <div className="section-heading"><div><p className="eyebrow">01 / STRUCTURED INTERPRETATION</p><h2>Here’s what I understood</h2></div><span className="subtle-tag">Review before running</span></div>
              <div className="interpret-grid">
                <article className="info-tile"><small>OPTIONS</small><p>{interpretation.candidate_options.map((option) => option.name).join(" · ") || "No options identified yet"}</p></article>
                <article className="info-tile"><small>GOALS</small><p>{interpretation.goals.join(" · ") || "None recorded"}</p></article>
                <article className="info-tile"><small>CONSTRAINTS</small><p>{interpretation.constraints.join(" · ") || "None recorded"}</p></article>
                <article className="info-tile"><small>ASSUMPTIONS</small><p>{interpretation.proposed_assumptions.join(" · ") || "None proposed"}</p></article>
              </div>
              {!canSimulate && <div className="clarification-card">
                <div><p className="eyebrow">A FEW DETAILS FIRST</p><h3>I need these inputs to model your options fairly.</h3><p className="clarification-intro">Your answers are used for this comparison. You can change them and rerun later.</p></div>
                {(interpretation.missing_field_prompts ?? []).map((prompt) => <label className="clarification-field" key={prompt.key} htmlFor={`answer-${prompt.key}`}>
                  <span>{prompt.label}{prompt.required && <i>Required</i>}</span>
                  <div className="clarification-input">{prompt.field_type === "currency" && <b>₹</b>}<input id={`answer-${prompt.key}`} inputMode={prompt.field_type === "text" ? "text" : "decimal"} onChange={(event) => setClarificationAnswers((answers) => ({ ...answers, [prompt.key]: event.target.value }))} placeholder={prompt.field_type === "integer" ? "e.g. 24" : prompt.field_type === "currency" ? "Enter amount" : "Your answer"} type={prompt.field_type === "text" ? "text" : "number"} value={clarificationAnswers[prompt.key] ?? ""} /></div>
                  <small>{prompt.question}</small>
                </label>)}
                {(interpretation.missing_field_prompts ?? []).length > 0 ? <button className="primary-button" disabled={interpret.isPending} onClick={continueWithAnswers} type="button">{interpret.isPending ? "Updating the decision…" : "Continue with these answers →"}</button> : <p className="clarification-intro">{interpretation.clarification_questions.join(" ") || interpretation.missing_information.join(" · ") || "Add the missing details in the composer below, then explore again."}</p>}
                {(interpretation.missing_information.length > 0 || interpretation.clarification_questions.length > 0) && <details className="clarification-more"><summary>Why are these details needed?</summary><p>{interpretation.clarification_questions.join(" ")} {interpretation.missing_information.join(" · ")}</p></details>}
              </div>}
              {canSimulate && aiExplanation && <div className="agent-explanation"><p className="eyebrow">DECISION SUMMARY</p><p>{aiExplanation.explanation}</p>{aiExplanation.caveats.length > 0 && <small>{aiExplanation.caveats.join(" · ")}</small>}</div>}
              {run.error && <p className="error-copy">{run.error.message}</p>}
              {canSimulate && <button className="primary-button run-button" disabled={run.isPending} onClick={() => run.mutate(interpretation)} type="button">{run.isPending ? "Running scenarios…" : "Run deterministic comparison →"}</button>}
            </section>}

            {displayed && <section className="result-section">
              <div className="section-heading"><div><p className="eyebrow">02 / THE FUTURES</p><h2>Compare what could unfold</h2></div><span className="subtle-tag">{displayed.status}</span></div>
              {(displayed.status === "queued" || displayed.status === "running") && <div className="notice-card">The analysis is still running. This view will update when the backend finishes.</div>}
              {displayed.status === "failed" && <div className="notice-card notice-error">The run did not complete. Review the decision and try again.</div>}
              {displayed.status === "completed" && displayed.simulation_outputs.length === 0 && <div className="notice-card notice-error">No futures were simulated. The comparison was stopped because required inputs or valid scenarios were missing. Go back to the questions above, add the missing details, and run it again.</div>}
              {displayed.simulation_outputs.length > 0 && <>
                {outcomeSummary && <section className="final-answer"><p className="eyebrow">FINAL RESULT</p><h3>What the numbers say</h3><p>{outcomeSummary}</p>{displayed.final_synthesis?.findings.map((finding, index) => <small key={`${finding.statement}-${index}`}>{finding.statement}</small>)}</section>}
                <div className="scenario-panel"><p className="panel-label">SCENARIO MAP <span>select an option to inspect</span></p><ScenarioGraph result={displayed} selected={selected} onSelect={setSelected} /></div>
                <div className="scenario-panel"><p className="panel-label">SIDE-BY-SIDE <span>values returned by the simulator</span></p><Comparison outputs={displayed.simulation_outputs} /></div>
                {selectedOutput && <div className="detail-grid"><section className="scenario-panel"><p className="panel-label">MONTHLY PATH <span>{selectedOutput.option_name}</span></p><Timeline states={selectedOutput.result.monthly_states} /></section><section className="scenario-panel metric-list"><p className="panel-label">OUTCOME METRICS</p><div><span>Ending cash</span><b>₹{selectedOutput.result.metrics.ending_cash}</b></div><div><span>Minimum cash</span><b>₹{selectedOutput.result.metrics.minimum_cash}</b></div><div><span>Total spend</span><b>₹{selectedOutput.result.metrics.total_spend}</b></div><div><span>Time used</span><b>{selectedOutput.result.metrics.total_time_used}h</b></div><div><span>Constraint violations</span><b>{selectedOutput.result.constraint_violations.length}</b></div><label className="what-if-label" htmlFor="what-if">One-time cash adjustment</label><div className="what-if-control"><input id="what-if" inputMode="decimal" onChange={(event) => setWhatIf(event.target.value)} value={whatIf} /><button className="primary-button" disabled={run.isPending} onClick={rerunWhatIf} type="button">{run.isPending ? "Rerunning…" : "Rerun"}</button></div>{run.error && <p className="error-copy">{run.error.message}</p>}</section></div>}
                {Object.keys(displayed.specialist_results).length > 0 && <section className="scenario-panel"><p className="panel-label">SPECIALIST REVIEW <span>analysis and evidence</span></p><SpecialistPanel agents={displayed.specialist_results} /></section>}
              </>}
              {displayed.evidence.length > 0 && <div className="evidence-links"><b>Sources</b>{displayed.evidence.map((item) => <a href={item.url} key={item.url} rel="noreferrer" target="_blank">{item.title ?? item.url} ↗</a>)}</div>}
            </section>}
            {(interpretation || displayed) && <button className="reset-link" onClick={reset} type="button">＋ Start another decision</button>}
          </div>
        </div>
        <div className="composer-dock">
          <section className="decision-card composer-card">
            <label className="sr-only" htmlFor="decision">What are you deciding?</label>
            <textarea aria-label="What are you deciding?" id="decision" onChange={(event) => setDecision(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey && decision.trim()) { event.preventDefault(); submitDecision(); } }} placeholder="Tell me the decision you’re facing…" value={decision} />
            {attachments.length > 0 && <div className="attachment-chips" aria-label="Attached files">{attachments.map((name, index) => <span key={`${name}-${index}`}>▤ {name}</span>)}</div>}
            <input accept=".txt,.md,.csv,.json,text/plain,text/csv,application/json" className="sr-only" multiple onChange={(event) => void attachFiles(event.target.files)} ref={fileInput} type="file" />
            <div className="composer-toolbar">
              <button className="composer-tool" onClick={() => fileInput.current?.click()} type="button" title="Attach a text, CSV, or JSON file">＋ Attach file</button>
              <button aria-pressed={isListening} className={`composer-tool ${isListening ? "listening" : ""}`} onClick={toggleDictation} type="button" title="Use voice input">{isListening ? "■ Stop listening" : "◉ Speak"}</button>
              <details className="context-disclosure"><summary>Add context</summary><textarea aria-label="Optional context" onChange={(event) => setContext(event.target.value)} placeholder="Income, goals, constraints, time horizon…" value={context} /></details>
              <span className="composer-hint">Enter to explore · Shift+Enter for a new line</span>
              <button className="primary-button" disabled={!decision.trim() || interpret.isPending} onClick={submitDecision} type="button">{interpret.isPending ? "Interpreting…" : interpretation ? "Explore →" : "Explore futures →"}</button>
            </div>
            {composerError && <p className="error-copy" role="status">{composerError}</p>}
            {interpret.error && <p className="error-copy">{interpret.error.message}</p>}
          </section>
        </div>
        {showTrace && <aside className="trace-rail"><div className="trace-heading"><i /> LIVE PROCESS TRACE</div><div className="trace-entries">{trace.map((entry, index) => <div className="trace-entry" key={`${entry}-${index}`}><time>{new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time><span>{entry}</span></div>)}</div><p>Only events from this session are shown.</p></aside>}
      </section>
    </main>
  );
}
