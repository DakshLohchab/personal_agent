import type {
  AIResponse,
  AgentRunResult,
  DecisionInterpretation,
  LifeState,
  Scenario,
} from "./types";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : "The API request failed.");
  }
  return response.json() as Promise<T>;
}

export const api = {
  interpret: (decision: string, context?: string) =>
    request<AIResponse>("/api/v1/ai/interpret", {
      method: "POST",
      body: JSON.stringify({ decision, context }),
    }),
  run: (interpretation: DecisionInterpretation, background = false) =>
    request<AgentRunResult>("/api/v1/ai/run", {
      method: "POST",
      body: JSON.stringify({ decision: interpretation.objective, interpretation, background }),
    }),
  runStatus: (jobId: string) => request<AgentRunResult>(`/api/v1/ai/run/${jobId}`, { method: "GET" }),
  simulate: (life_state: LifeState, scenario: Scenario) =>
    request<unknown>("/api/v1/simulations", {
      method: "POST",
      body: JSON.stringify({ life_state, scenario }),
    }),
  sensitivity: (payload: unknown) =>
    request<unknown>("/api/v1/sensitivity", { method: "POST", body: JSON.stringify(payload) }),
  breakpoint: (payload: unknown) =>
    request<unknown>("/api/v1/breakpoints", { method: "POST", body: JSON.stringify(payload) }),
};

