import type { SimulationOutput } from "@/lib/types";

export function Comparison({ outputs }: { outputs: SimulationOutput[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <caption className="sr-only">Comparison of backend simulation results</caption>
        <thead>
          <tr className="border-b border-line text-moss">
            <th className="px-3 py-3">Future</th>
            <th className="px-3 py-3">Ending cash</th>
            <th className="px-3 py-3">Minimum cash</th>
            <th className="px-3 py-3">Spend</th>
            <th className="px-3 py-3">Time used</th>
            <th className="px-3 py-3">Violations</th>
          </tr>
        </thead>
        <tbody>
          {outputs.map((item) => (
            <tr key={item.option_name} className="border-b border-line/70">
              <th className="px-3 py-3 font-semibold">{item.option_name}</th>
              <td className="px-3 py-3">₹{item.result.metrics.ending_cash}</td>
              <td className="px-3 py-3">₹{item.result.metrics.minimum_cash}</td>
              <td className="px-3 py-3">₹{item.result.metrics.total_spend}</td>
              <td className="px-3 py-3">{item.result.metrics.total_time_used}h</td>
              <td className="px-3 py-3">{item.result.constraint_violations.length}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
