import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Comparison } from "../components/Comparison";

describe("Comparison", () => {
  it("renders exact backend decimal strings", () => {
    render(
      <Comparison
        outputs={[
          {
            option_name: "Save",
            tool_name: "simulate_scenario",
            result: {
              monthly_states: [],
              metrics: {
                ending_cash: "71000.125",
                minimum_cash: "63000",
                total_spend: "24000",
                total_time_used: "0",
              },
              uncertainty: null,
              constraint_violations: [],
            },
          },
        ]}
      />,
    );
    expect(screen.getByText("₹71000.125")).toBeInTheDocument();
  });
});
