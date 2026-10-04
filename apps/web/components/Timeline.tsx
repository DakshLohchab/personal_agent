"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MonthlyState } from "@/lib/types";

export function Timeline({ states }: { states: MonthlyState[] }) {
  const data = states.map((state) => ({
    month: `M${state.month}`,
    cash: Number(state.ending_cash),
    time: Number(state.time_used_hours),
  }));
  return (
    <div aria-label="Cash and time timeline" className="h-72 w-full">
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#d9ded5" />
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="cash" stroke="#426454" strokeWidth={3} dot={false} />
          <Line type="monotone" dataKey="time" stroke="#c9694b" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
      <p className="sr-only">
        The chart displays backend-provided ending cash and time used by month.
      </p>
    </div>
  );
}
