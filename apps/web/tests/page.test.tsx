import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import HomePage from "../app/page";
import { interpretation, output, runResult } from "./fixtures";

vi.mock("next/dynamic", () => ({
  default: () => function DynamicFuturePaths() {
    return <div aria-label="Interactive overview of possible futures" />;
  },
}));

vi.mock("../components/ScenarioGraph", () => ({
  ScenarioGraph: ({ result, onSelect }: { result: ReturnType<typeof runResult>; onSelect: (name: string) => void }) => (
    <div aria-label="Scenario graph">
      {result.simulation_outputs.map((item) => (
        <button key={item.option_name} type="button" onClick={() => onSelect(item.option_name)}>
          {item.option_name}
        </button>
      ))}
    </div>
  ),
}));

const fetchMock = vi.fn();

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <HomePage />
    </QueryClientProvider>,
  );
}

function response(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));
}

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

describe("decision composer and golden flow", () => {
  it("submits decision and optional context, shows loading, success, and safe errors", async () => {
    const user = userEvent.setup();
    fetchMock.mockImplementation(() => response({ interpretation }));
    renderPage();

    const decision = screen.getByLabelText("What are you deciding?");
    const context = screen.getByLabelText("Optional context");
    await user.clear(decision);
    await user.type(decision, "Should I save?");
    await user.type(context, "My rent is stable.");
    await user.click(screen.getByRole("button", { name: "Explore Futures" }));
    expect(await screen.findByRole("button", { name: "Confirm and compare" })).toBeInTheDocument();

    const request = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(request).toEqual({ decision: "Should I save?", context: "My rent is stable." });

    fetchMock.mockReset();
    fetchMock.mockImplementation(() => Promise.reject(new Error("Network unavailable")));
    await user.click(screen.getByRole("button", { name: "Explore Futures" }));
    expect(await screen.findByText("Network unavailable")).toBeInTheDocument();
    expect(screen.queryByText(/stack|NEBIUS_API_KEY|TOKENHARBOR_API_KEY/i)).not.toBeInTheDocument();
  });

  it("allows supported interpretation edits and sends the edited objective to the run", async () => {
    const user = userEvent.setup();
    fetchMock
      .mockImplementationOnce(() => response({ interpretation }))
      .mockImplementationOnce(() => response(runResult("completed")));
    renderPage();
    await user.click(screen.getByRole("button", { name: "Explore Futures" }));
    const objective = await screen.findByLabelText("Objective");
    await user.clear(objective);
    await user.type(objective, "Prioritize saving");
    expect(objective).toHaveValue("Prioritize saving");
    expect(screen.getByText("Laptop price")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Confirm and compare" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const request = JSON.parse(fetchMock.mock.calls[1][1].body as string);
    expect(request.interpretation.objective).toBe("Prioritize saving");
  });

  it("handles synchronous results and displays exact backend financial values", async () => {
    const user = userEvent.setup();
    fetchMock
      .mockImplementationOnce(() => response({ interpretation }))
      .mockImplementationOnce(() =>
        response(runResult("completed", [output("Save money", "71000"), output("Buy laptop", "65000")])),
      );
    renderPage();
    await user.click(screen.getByRole("button", { name: "Explore Futures" }));
    await user.click(await screen.findByRole("button", { name: "Confirm and compare" }));
    expect(await screen.findByText("₹71000")).toBeInTheDocument();
    expect(screen.getByText("Comparison ready")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Compare futures" })).toBeInTheDocument();
    expect(screen.getByText("Finance")).toBeInTheDocument();
    expect(screen.getByText("Time")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Buy laptop" }));
    expect(screen.getByRole("heading", { name: "Buy laptop" })).toBeInTheDocument();
    expect(screen.getByLabelText("Cash and time timeline")).toBeInTheDocument();
  });

  it("polls an asynchronous job until completion without fake progress", async () => {
    const user = userEvent.setup();
    let resolveStatus!: (value: Response | PromiseLike<Response>) => void;
    const pendingStatus = new Promise<Response>((resolve) => {
      resolveStatus = resolve;
    });
    fetchMock
      .mockImplementationOnce(() => response({ interpretation }))
      .mockImplementationOnce(() => response(runResult("running")))
      .mockImplementationOnce(() => pendingStatus);
    renderPage();
    await user.click(screen.getByRole("button", { name: "Explore Futures" }));
    await user.click(await screen.findByRole("button", { name: "Confirm and compare" }));
    expect(await screen.findByText("Analyzing and simulating…")).toBeInTheDocument();
    resolveStatus(await response(runResult("completed", [output("Save money", "65000")])));
    expect(await screen.findByText("₹65000", {}, { timeout: 3000 })).toBeInTheDocument();
    expect(screen.getByText("Comparison ready")).toBeInTheDocument();
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("renders a safe failed run response", async () => {
    const user = userEvent.setup();
    fetchMock
      .mockImplementationOnce(() => response({ interpretation }))
      .mockImplementationOnce(() => response(runResult("failed")));
    renderPage();
    await user.click(screen.getByRole("button", { name: "Explore Futures" }));
    await user.click(await screen.findByRole("button", { name: "Confirm and compare" }));
    expect(await screen.findByText("The run could not be completed. Please retry safely.")).toBeInTheDocument();
    expect(screen.queryByText(/provider|credential|stack trace/i)).not.toBeInTheDocument();
  });

  it("renders a safe polling failure", async () => {
    const user = userEvent.setup();
    fetchMock
      .mockImplementationOnce(() => response({ interpretation }))
      .mockImplementationOnce(() => response(runResult("running")))
      .mockImplementationOnce(() => Promise.reject(new Error("status endpoint unavailable")));
    renderPage();
    await user.click(screen.getByRole("button", { name: "Explore Futures" }));
    await user.click(await screen.findByRole("button", { name: "Confirm and compare" }));
    expect(await screen.findByText("We could not check the run status. Please retry safely.")).toBeInTheDocument();
    expect(screen.queryByText(/status endpoint unavailable|stack trace|credential/i)).not.toBeInTheDocument();
  });

  it("reruns a supported What-If variable and replaces the display with backend truth", async () => {
    const user = userEvent.setup();
    fetchMock
      .mockImplementationOnce(() => response({ interpretation }))
      .mockImplementationOnce(() => response(runResult("completed", [output("Save money", "71000")])))
      .mockImplementationOnce(() => response(runResult("completed", [output("Save money · What If", "65000")])));
    renderPage();
    await user.click(screen.getByRole("button", { name: "Explore Futures" }));
    await user.click(await screen.findByRole("button", { name: "Confirm and compare" }));
    await screen.findByText("₹71000");
    const whatIf = screen.getByLabelText("One-time cash adjustment (backend rerun)");
    await user.clear(whatIf);
    await user.type(whatIf, "9000");
    await user.click(screen.getByRole("button", { name: "Recompute branch" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    const rerunRequest = JSON.parse(fetchMock.mock.calls[2][1].body as string);
    expect(rerunRequest.interpretation.candidate_options[1].scenario.deltas.cash).toBe("9000");
    expect(await screen.findByText("₹65000")).toBeInTheDocument();
    expect(screen.queryByText("₹71000")).not.toBeInTheDocument();
  });
});
