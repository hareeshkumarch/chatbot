"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DashboardMetrics } from "@/lib/types";
import { Card } from "@/components/ui/Card";

export function TaskTokenBreakdownChart({ data }: { data: DashboardMetrics["by_task"] }) {
  const formatted = data.map((point) => ({
    name: point.task,
    input: point.prompt_tokens,
    output: point.completion_tokens,
    total: point.total_tokens,
  }));

  return (
    <Card className="p-4">
      <p className="mb-3 font-mono text-xs uppercase tracking-wide text-ink-faint">Where tokens go</p>
      {formatted.length === 0 ? (
        <div className="flex h-56 items-center justify-center text-sm text-ink-faint">No token activity yet</div>
      ) : (
        <ResponsiveContainer width="100%" height={224}>
          <BarChart data={formatted} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#DCE0DA" vertical={false} />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#5B6461" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: "#8A9390" }} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip
              contentStyle={{ borderRadius: 4, borderColor: "#DCE0DA", fontSize: 12 }}
              cursor={{ fill: "#ECEEEA" }}
              formatter={(value, name, item) => {
                const row = item.payload as (typeof formatted)[number];
                if (name === "input" || name === "output") {
                  return [Number(value), name === "input" ? "Input tokens" : "Output tokens"];
                }
                return [row.total, "Total tokens"];
              }}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} formatter={(value) => (value === "input" ? "Input" : "Output")} />
            <Bar dataKey="input" name="input" stackId="tokens" fill="#2F3EE0" radius={[0, 0, 0, 0]} />
            <Bar dataKey="output" name="output" stackId="tokens" fill="#1B8C6F" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
