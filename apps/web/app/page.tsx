"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import { Comparison } from "@/components/Comparison";
import { ScenarioGraph } from "@/components/ScenarioGraph";
import { SpecialistPanel } from "@/components/SpecialistPanel";
import { Timeline } from "@/components/Timeline";
import { api } from "@/lib/api";
import type { AgentRunResult, DecisionInterpretation } from "@/lib/types";

const FuturePaths = dynamic(
  () => import("@/components/FuturePaths").then((module) => module.FuturePaths),
  {
    ssr: false,
    loading: () => <div className="future-paths__fallback">Loading immersive overview…</div>,
  },
);

const defaultDecision = "I have ₹50,000. Should I buy a laptop, take a trip, or save the money?";

function Progress({ state }: { state: string }) {
  return (
    <div aria-live="polite" className="rounded-xl bg-[#eef1e9] px-4 py-3 text-sm text-moss">
      {state}
    </div>
  );
}

export default function HomePage() {
  const [decision, setDecision] = useState(defaultDecision);
  const [context, setContext] = useState("");
  const [interpretation, setInterpretation] = useState<DecisionInterpretation | null>(null);
  const [result, setResult] = useState<AgentRunResult | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [whatIf, setWhatIf] = useState("5000");

  const interpret = useMutation({
    mutationFn: () => api.interpret(decision, context || undefined),
    onSuccess: (response) => setInterpretation(response.interpretation),
  });
  const run = useMutation({
    mutationFn: (request: DecisionInterpretation) => api.run(request),
    onSuccess: setResult,
  });
  const status = useQuery({
    queryKey: ["run", result?.run_id],
    queryFn: () => api.runStatus(result!.run_id),
    enabled: Boolean(result?.status === "queued" || result?.status === "running"),
    refetchInterval: (query) =>
      query.state.data?.status === "completed" || query.state.data?.status === "failed"
        ? false
        : 1200,
  });
  const displayedResult = status.data?.status === "completed" ? status.data : result;
  const selectedOutput = useMemo(
    () =>
      displayedResult?.simulation_outputs.find((item) => item.option_name === selected) ??
      displayedResult?.simulation_outputs[0],
    [displayedResult, selected],
  );

  const rerunWhatIf = () => {
    if (!interpretation || !selectedOutput) return;
    const updated: DecisionInterpretation = {
      ...interpretation,
      candidate_options: interpretation.candidate_options.map((option) =>
        option.name === selectedOutput.option_name && option.scenario
          ? {
              ...option,
              scenario: {
                ...option.scenario,
                parent_id: option.scenario.id,
                id: `${option.scenario.id}-what-if`,
                name: `${option.scenario.name} · What If`,
                deltas: { ...option.scenario.deltas, cash: whatIf },
              },
            }
          : option,
      ),
    };
    setInterpretation(updated);
    run.mutate(updated);
  };

  return (
    <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
      <header className="mb-12 flex items-start justify-between">
        <div>
          <p className="mb-4 text-xs font-bold uppercase tracking-[.28em] text-moss">Life Sandbox</p>
          <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-6xl">
            Explore the futures before you decide.
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-ink/65">
            Turn a real-life choice into transparent scenarios, deterministic outcomes, and
            trade-offs you can actually inspect.
          </p>
        </div>
        <span className="hidden rounded-full border border-line px-4 py-2 text-sm text-moss sm:block">
          Numerical truth stays deterministic
        </span>
      </header>

      <section className="panel grid gap-8 p-5 sm:p-8 lg:grid-cols-[1fr_320px]">
        <div>
          <label className="mb-3 block text-sm font-semibold text-moss" htmlFor="decision">
            What are you deciding?
          </label>
          <textarea
            className="min-h-32 w-full resize-y rounded-xl border border-line bg-paper p-4 text-lg"
            id="decision"
            onChange={(event) => setDecision(event.target.value)}
            value={decision}
          />
          <label className="mt-4 block text-sm font-semibold text-moss" htmlFor="context">
            Optional context
          </label>
          <textarea
            className="mt-2 min-h-20 w-full resize-y rounded-xl border border-line bg-paper p-3 text-sm"
            id="context"
            onChange={(event) => setContext(event.target.value)}
            placeholder="Add income, expenses, goals, time constraints, or horizon details."
            value={context}
          />
          <button
            className="mt-4 rounded-full bg-ink px-6 py-3 font-semibold text-white transition hover:bg-moss disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!decision.trim() || interpret.isPending}
            onClick={() => interpret.mutate()}
            type="button"
          >
            {interpret.isPending ? "Interpreting…" : "Explore Futures"}
          </button>
          {interpret.error && <p className="mt-3 text-sm text-ember">{interpret.error.message}</p>}
        </div>
        <aside className="rounded-xl bg-[#eef1e9] p-5 text-sm text-ink/70">
          <p className="font-semibold text-moss">Start with what you know</p>
          <p className="mt-2">You can add finances, goals, commitments, or constraints after the first interpretation.</p>
        </aside>
      </section>

      {interpretation && (
        <section className="panel mt-8 p-5 sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-[.2em] text-moss">Interpretation</p>
              <label className="mt-2 block text-sm font-semibold text-moss" htmlFor="objective">
                Objective
              </label>
              <input
                className="mt-1 w-full rounded-lg border border-line bg-paper p-3 text-2xl font-semibold"
                id="objective"
                onChange={(event) =>
                  setInterpretation({ ...interpretation, objective: event.target.value })
                }
                value={interpretation.objective}
              />
            </div>
            <button
              className="rounded-full bg-moss px-5 py-2.5 font-semibold text-white disabled:opacity-50"
              disabled={run.isPending}
              onClick={() => {
                if (interpretation) run.mutate(interpretation);
              }}
              type="button"
            >
              {run.isPending ? "Preparing…" : "Confirm and compare"}
            </button>
          </div>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Options", interpretation.candidate_options.map((option) => option.name).join(", ") || "None"],
              ["Goals", interpretation.goals.join(", ") || "None recorded"],
              ["Constraints", interpretation.constraints.join(", ") || "None recorded"],
              ["Assumptions", interpretation.proposed_assumptions.join(", ") || "None recorded"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-line p-4">
                <p className="text-xs uppercase tracking-wider text-moss">{label}</p>
                <p className="mt-2 text-sm">{value}</p>
              </div>
            ))}
          </div>
          {interpretation.clarification_questions.length > 0 && (
            <p className="mt-5 text-sm text-ember">{interpretation.clarification_questions.join(" ")}</p>
          )}
          {run.error && <p className="mt-4 text-sm text-ember">{run.error.message}</p>}
        </section>
      )}

      {result && (
        <section className="mt-8 space-y-8">
          <Progress state={displayedResult?.status === "completed" ? "Comparison ready" : "Analyzing and simulating…"} />
          {displayedResult?.status === "failed" && (
            <div className="panel p-6 text-ember">The run could not be completed. Please retry safely.</div>
          )}
          {displayedResult?.simulation_outputs.length ? (
            <>
              <section className="panel p-4 sm:p-6">
                <div className="mb-4 flex items-end justify-between">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[.2em] text-moss">The futures</p>
                    <h2 className="mt-2 text-2xl font-semibold">See how each path unfolds</h2>
                  </div>
                  <p className="hidden text-sm text-ink/60 sm:block">Select a branch to inspect it</p>
                </div>
                <ScenarioGraph result={displayedResult} selected={selected} onSelect={setSelected} />
              </section>
              <section className="panel p-4 sm:p-6">
                <div className="mb-4">
                  <p className="text-xs font-bold uppercase tracking-[.2em] text-moss">Future paths</p>
                  <h2 className="mt-2 text-2xl font-semibold">A cinematic overview of what could unfold</h2>
                  <p className="mt-2 text-sm text-ink/60">
                    Select a path here or in the detailed graph. Both views use the same backend results.
                  </p>
                </div>
                <FuturePaths outputs={displayedResult.simulation_outputs} selected={selected} onSelect={setSelected} />
              </section>
              <section className="panel p-5 sm:p-7">
                <h2 className="mb-4 text-2xl font-semibold">Compare futures</h2>
                <Comparison outputs={displayedResult.simulation_outputs} />
              </section>
              {selectedOutput && (
                <section className="grid gap-8 lg:grid-cols-[1.2fr_.8fr]">
                  <div className="panel p-5 sm:p-7">
                    <p className="text-xs font-bold uppercase tracking-[.2em] text-moss">Timeline</p>
                    <h2 className="mt-2 text-2xl font-semibold">{selectedOutput.option_name}</h2>
                    <Timeline states={selectedOutput.result.monthly_states} />
                  </div>
                  <div className="panel p-5 sm:p-7">
                    <p className="text-xs font-bold uppercase tracking-[.2em] text-ember">What If?</p>
                    <h2 className="mt-2 text-2xl font-semibold">Change one assumption</h2>
                    <label className="mt-5 block text-sm" htmlFor="what-if">
                      One-time cash adjustment (backend rerun)
                    </label>
                    <input
                      className="mt-2 w-full rounded-lg border border-line bg-paper p-3"
                      id="what-if"
                      inputMode="decimal"
                      onChange={(event) => setWhatIf(event.target.value)}
                      value={whatIf}
                    />
                    <button className="mt-4 rounded-full border border-ink px-5 py-2.5 font-semibold" onClick={rerunWhatIf} type="button">
                      Recompute branch
                    </button>
                  </div>
                </section>
              )}
              <section className="panel p-5 sm:p-7">
                <p className="text-xs font-bold uppercase tracking-[.2em] text-moss">Analysis</p>
                <h2 className="mb-5 mt-2 text-2xl font-semibold">What each specialist noticed</h2>
                <SpecialistPanel agents={displayedResult.specialist_results} />
              </section>
            </>
          ) : null}
        </section>
      )}
    </main>
  );
}
