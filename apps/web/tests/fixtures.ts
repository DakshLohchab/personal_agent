import type { AgentResponse, AgentRunResult, DecisionInterpretation, MonthlyState, SimulationOutput } from "../lib/types";

export const interpretation: DecisionInterpretation = {
  objective: "Choose how to use ₹50,000",
  goals: ["Build financial security"],
  constraints: ["Keep an emergency buffer"],
  commitments: ["Rent"],
  proposed_assumptions: ["Income remains stable"],
  missing_information: ["Laptop price"],
  clarification_questions: [],
  candidate_options: [
    {
      name: "Buy laptop",
      description: "Purchase a laptop",
      scenario: {
        id: "laptop",
        name: "Buy laptop",
        deltas: { cash: "-50000" },
        assumption_ids: [],
      },
    },
    {
      name: "Save money",
      description: "Keep the money in savings",
      scenario: {
        id: "save",
        name: "Save money",
        deltas: { cash: "0" },
        assumption_ids: [],
      },
    },
  ],
  current_state: null,
};

export const monthlyStates: MonthlyState[] = [
  {
    month: 1,
    starting_cash: "50000",
    income: "10000",
    essential_expenses: "4000",
    discretionary_spend: "1000",
    one_time_adjustments: "0",
    ending_cash: "55000",
    time_available_hours: "120",
    time_used_hours: "10",
    goal_progress: { security: "0.25" },
    constraint_violations: [],
  },
  {
    month: 2,
    starting_cash: "55000",
    income: "10000",
    essential_expenses: "4000",
    discretionary_spend: "0",
    one_time_adjustments: "0",
    ending_cash: "61000",
    time_available_hours: "120",
    time_used_hours: "8",
    goal_progress: { security: "0.5" },
    constraint_violations: [],
  },
];

export function output(
  option_name: string,
  ending_cash: string,
  overrides: Partial<SimulationOutput["result"]["metrics"]> = {},
): SimulationOutput {
  return {
    option_name,
    tool_name: "simulate_scenario",
    result: {
      monthly_states: monthlyStates,
      metrics: {
        ending_cash,
        minimum_cash: "45000",
        total_spend: "5000",
        total_time_used: "18",
        ...overrides,
      },
      uncertainty: { confidence: "medium" },
      constraint_violations: [],
    },
  };
}

export const specialistResults: Record<string, AgentResponse> = Object.fromEntries(
  ["Finance", "Time", "Research", "Risk", "Opportunity", "Future You", "Synthesis"].map((agent_name) => [
    agent_name,
    {
      agent_name,
      status: "completed",
      findings: [
        {
          category: "calculated",
          statement: `${agent_name} finding`,
          evidence: [],
        },
      ],
      evidence: [{ url: "https://example.com/evidence", title: `${agent_name} evidence` }],
    },
  ]),
);

export function runResult(
  status: AgentRunResult["status"],
  simulation_outputs: SimulationOutput[] = [output("Save money", "71000")],
): AgentRunResult {
  return {
    run_id: "run-1",
    status,
    specialist_results: specialistResults,
    simulation_outputs,
    evidence: [],
    final_synthesis: null,
  };
}
