export type Decimal = string;

export interface Scenario {
  id: string;
  name: string;
  parent_id?: string | null;
  deltas: Record<string, Decimal>;
  assumption_ids: string[];
}

export interface LifeState {
  start_date: string;
  horizon_months: number;
  cash: Decimal;
  monthly_income: Decimal;
  monthly_essential_expenses: Decimal;
  monthly_time_available_hours: Decimal;
  goals: unknown[];
  constraints: unknown[];
  commitments: unknown[];
  variables: unknown[];
}

export interface DecisionOption {
  name: string;
  description: string;
  scenario?: Scenario | null;
}

export interface MissingFieldPrompt {
  key: string;
  label: string;
  question: string;
  field_type: "currency" | "integer" | "text";
  required: boolean;
}

export interface DecisionInterpretation {
  objective: string;
  current_state?: LifeState | null;
  goals: string[];
  constraints: string[];
  commitments: string[];
  proposed_assumptions: string[];
  missing_information: string[];
  clarification_questions: string[];
  candidate_options: DecisionOption[];
  simulation_readiness?: "READY_TO_SIMULATE" | "NEEDS_INFORMATION";
  required_missing_fields?: string[];
  missing_field_prompts?: MissingFieldPrompt[];
}

export interface AIResponse {
  interpretation: DecisionInterpretation;
  tool_results: unknown[];
  explanation: { explanation: string; caveats: string[] };
  metadata: Record<string, unknown>;
}

export interface ConstraintViolation {
  month: number;
  constraint_id: string;
  observed: Decimal;
  limit: Decimal;
}

export interface MonthlyState {
  month: number;
  starting_cash: Decimal;
  income: Decimal;
  essential_expenses: Decimal;
  discretionary_spend: Decimal;
  one_time_adjustments: Decimal;
  ending_cash: Decimal;
  time_available_hours: Decimal;
  time_used_hours: Decimal;
  goal_progress: Record<string, Decimal>;
  constraint_violations: ConstraintViolation[];
}

export interface SimulationOutput {
  option_name: string;
  tool_name: string;
  result: {
    monthly_states: MonthlyState[];
    metrics: {
      ending_cash: Decimal;
      minimum_cash: Decimal;
      total_spend: Decimal;
      total_time_used: Decimal;
    };
    uncertainty: unknown | null;
    constraint_violations: ConstraintViolation[];
  };
}

export interface AgentResponse {
  agent_name: string;
  status: "completed" | "failed" | "partial";
  findings: Array<{
    category: "calculated" | "external_evidence" | "assumption" | "qualitative";
    statement: string;
    evidence: Array<{ url: string; title?: string | null; publisher?: string | null }>;
  }>;
  evidence: Array<{ url: string; title?: string | null; publisher?: string | null }>;
  error?: string | null;
}

export interface AgentRunResult {
  run_id: string;
  status: "queued" | "running" | "completed" | "partial" | "failed";
  specialist_results: Record<string, AgentResponse>;
  simulation_outputs: SimulationOutput[];
  evidence: Array<{ url: string; title?: string | null; publisher?: string | null }>;
  final_synthesis?: AgentResponse | null;
  memory_context?: DecisionMemory[];
}

export interface DecisionMemory {
  memory_id: string;
  memory_type: string;
  content: string;
  confidence?: number | null;
  provenance: { type: string; reference?: string | null; label: string };
  retrieval_reason: string;
  last_confirmed_at?: string | null;
}

export interface MemoryRecord extends DecisionMemory {
  status: "candidate" | "active" | "superseded" | "expired" | "deleted";
  expires_at?: string | null;
}
