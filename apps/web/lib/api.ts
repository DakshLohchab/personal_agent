import type {
  AIResponse,
  AgentRunResult,
  DecisionMemory,
  DecisionInterpretation,
  LifeState,
  MemoryRecord,
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
  run: (
    interpretation: DecisionInterpretation,
    background = false,
    memoryContext: DecisionMemory[] = [],
  ) =>
    request<AgentRunResult>("/api/v1/ai/run", {
      method: "POST",
      body: JSON.stringify({
        decision: interpretation.objective,
        interpretation,
        background,
        memory_context: memoryContext,
      }),
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
  memories: async () => {
    const records = await request<Array<Record<string, unknown>>>("/api/v1/memories", {
      method: "GET",
    });
    return records.map((record) => ({
      memory_id: String(record.id),
      memory_type: String(record.memory_type),
      content: String(record.content),
      status: String(record.status) as MemoryRecord["status"],
      expires_at: (record.expires_at as string | null | undefined) ?? null,
      last_confirmed_at: (record.last_confirmed_at as string | null | undefined) ?? null,
      provenance: {
        type: String(record.provenance_type ?? "user_input"),
        reference: (record.provenance_ref as string | null | undefined) ?? null,
        label: String(record.provenance_type ?? "user_input"),
      },
      retrieval_reason: "",
    }));
  },
  approveMemory: (memoryId: string) =>
    request<MemoryRecord>(`/api/v1/memories/${memoryId}/approve`, { method: "POST" }),
  updateMemory: (memoryId: string, content: string) =>
    request<MemoryRecord>(`/api/v1/memories/${memoryId}`, {
      method: "PATCH",
      body: JSON.stringify({ content }),
    }),
  forgetMemory: (memoryId: string) =>
    request<void>(`/api/v1/memories/${memoryId}`, { method: "DELETE" }),
  relevantMemories: (decision_context: string) =>
    request<DecisionMemory[]>("/api/v1/memories/relevant", {
      method: "POST",
      body: JSON.stringify({ decision_context, limit: 10 }),
    }),
};
