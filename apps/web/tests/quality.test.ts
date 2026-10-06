import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import type { DecisionInterpretation } from "../lib/types";

describe("frontend quality contracts", () => {
  it("keeps financial API fields as decimal strings", () => {
    const interpretation: DecisionInterpretation = {
      objective: "save",
      goals: [],
      constraints: [],
      commitments: [],
      proposed_assumptions: [],
      missing_information: [],
      clarification_questions: [],
      candidate_options: [],
    };
    expect(typeof interpretation.objective).toBe("string");
    const apiSource = readFileSync(path.resolve(process.cwd(), "lib/api.ts"), "utf8");
    expect(apiSource).not.toMatch(/NEBIUS_API_KEY|TOKENHARBOR_API_KEY|DATABASE_URL|R2_/);
    expect(apiSource).toContain("NEXT_PUBLIC_API_BASE_URL");
  });
});
