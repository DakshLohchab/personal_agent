import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Comparison } from "../components/Comparison";
import { ScenarioGraph } from "../components/ScenarioGraph";
import { SpecialistPanel } from "../components/SpecialistPanel";
import { Timeline } from "../components/Timeline";
import { output, runResult, specialistResults } from "./fixtures";

describe("result components", () => {
  it("renders graph nodes, relationships, and synchronizes selection", async () => {
    const onSelect = vi.fn();
    render(<ScenarioGraph result={runResult("completed", [output("Save", "71000"), output("Trip", "65000")])} selected={null} onSelect={onSelect} />);

    expect(screen.getByLabelText("Scenario graph")).toBeInTheDocument();
    expect(screen.getByTestId("rf__node-Save")).toHaveTextContent("Save");
    expect(screen.getByTestId("rf__node-Trip")).toHaveTextContent("Trip");
    fireEvent.click(screen.getByTestId("rf__node-Trip"));
    expect(onSelect).toHaveBeenCalledWith("Trip");
  });

  it("renders backend comparison metrics without inventing scores", () => {
    render(<Comparison outputs={[output("Save", "71000", { minimum_cash: "62000", total_spend: "3000", total_time_used: "12" })]} />);
    expect(screen.getByText("₹71000")).toBeInTheDocument();
    expect(screen.getByText("₹62000")).toBeInTheDocument();
    expect(screen.getByText("₹3000")).toBeInTheDocument();
    expect(screen.getByText("12h")).toBeInTheDocument();
    expect(screen.queryByText(/risk score|effort score|cost score/i)).not.toBeInTheDocument();
  });

  it("passes monthly backend values to the timeline visualization", () => {
    render(<Timeline states={output("Save", "71000").result.monthly_states} />);
    expect(screen.getByLabelText("Cash and time timeline")).toBeInTheDocument();
    expect(screen.getByText(/backend-provided ending cash and time used/i)).toBeInTheDocument();
  });

  it("renders readable specialist findings and supplied evidence", () => {
    render(<SpecialistPanel agents={specialistResults} />);
    for (const name of Object.keys(specialistResults)) {
      expect(screen.getByText(name)).toBeInTheDocument();
      expect(screen.getByText(`${name} finding`)).toBeInTheDocument();
      expect(screen.getByText(`${name} evidence`)).toBeInTheDocument();
    }
  });

  it("keeps partial specialist results usable and shows their safe error", () => {
    render(
      <SpecialistPanel
        agents={{
          Finance: {
            ...specialistResults.Finance,
            status: "partial",
            error: "Finance evidence was unavailable.",
          },
        }}
      />,
    );
    expect(screen.getByText("Finance finding")).toBeInTheDocument();
    expect(screen.getByText("Finance evidence was unavailable.")).toBeInTheDocument();
  });
});
