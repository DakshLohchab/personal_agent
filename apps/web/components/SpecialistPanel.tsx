import type { AgentResponse } from "@/lib/types";

export function SpecialistPanel({ agents }: { agents: Record<string, AgentResponse> }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {Object.values(agents).map((agent) => (
        <details key={agent.agent_name} className="rounded-xl border border-line p-4">
          <summary className="cursor-pointer font-semibold">{agent.agent_name}</summary>
          <div className="mt-3 space-y-2 text-sm text-ink/75">
            {agent.findings.map((finding, index) => (
              <p key={`${agent.agent_name}-${index}`}>
                <span className="mr-2 rounded-full bg-cream px-2 py-1 text-xs uppercase text-moss">
                  {finding.category}
                </span>
                {finding.statement}
              </p>
            ))}
            {agent.evidence.map((evidence) => (
              <a
                key={evidence.url}
                className="block truncate text-moss underline"
                href={evidence.url}
                rel="noreferrer"
                target="_blank"
              >
                {evidence.title ?? evidence.url}
              </a>
            ))}
            {agent.error && <p className="text-ember">{agent.error}</p>}
          </div>
        </details>
      ))}
    </div>
  );
}
