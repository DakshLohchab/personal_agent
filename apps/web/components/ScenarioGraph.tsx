"use client";

import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { AgentRunResult } from "@/lib/types";

export function ScenarioGraph({
  result,
  selected,
  onSelect,
}: {
  result: AgentRunResult;
  selected: string | null;
  onSelect: (option: string) => void;
}) {
  const nodes: Node[] = [
    { id: "decision", position: { x: 0, y: 130 }, data: { label: "Your decision" }, type: "input" },
    ...result.simulation_outputs.map((item, index) => ({
      id: item.option_name,
      position: { x: 260 + index * 240, y: 130 },
      data: {
        label: `${item.option_name}\n₹${item.result.metrics.ending_cash}`,
      },
      className: selected === item.option_name ? "ring-4 ring-ember" : "",
    })),
  ];
  const edges: Edge[] = result.simulation_outputs.map((item) => ({
    id: `decision-${item.option_name}`,
    source: "decision",
    target: item.option_name,
    animated: selected === item.option_name,
  }));
  const handleNodeClick: NodeMouseHandler = (_, node) => {
    if (node.id !== "decision") onSelect(node.id);
  };

  return (
    <div aria-label="Scenario graph" className="h-[360px] rounded-2xl bg-[#eef1e9]">
      <ReactFlow nodes={nodes} edges={edges} fitView onNodeClick={handleNodeClick}>
        <Background color="#cdd5c9" gap={24} />
        <Controls />
        <MiniMap />
      </ReactFlow>
      <p className="sr-only">
        Scenario graph with {result.simulation_outputs.length} candidate futures. Select a node
        to inspect its results.
      </p>
    </div>
  );
}
