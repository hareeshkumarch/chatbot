"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { DashboardMetrics } from "@/lib/types";
import { Card } from "@/components/ui/Card";

const COLORS = ["#2F3EE0", "#1B8C6F", "#C4432B", "#8A9390", "#5B6461"];

export function RetrievalStrategyChart({ data }: { data: DashboardMetrics["by_retrieval_strategy"] }) {
  const formatted = data.map((point) => ({ name: point.strategy, value: point.queries }));

  return (
    <Card className="p-4">
      <p className="mb-3 font-mono text-xs uppercase tracking-wide text-ink-faint">Retrieval strategy mix</p>
      <div className="flex h-56 items-center">
        {formatted.length === 0 ? (
          <div className="flex h-full w-full items-center justify-center text-sm text-ink-faint">No retrieval activity yet</div>
        ) : (
          <>
            <ResponsiveContainer width="55%" height="100%">
              <PieChart>
                <Pie data={formatted} dataKey="value" nameKey="name" innerRadius={45} outerRadius={70} paddingAngle={2}>
                  {formatted.map((entry, index) => (
                    <Cell key={entry.name} fill={COLORS[index % COLORS.length]} stroke="none" />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: 4, borderColor: "#DCE0DA", fontSize: 12, fontFamily: "var(--font-inter)" }} />
              </PieChart>
            </ResponsiveContainer>
            <ul className="flex flex-1 flex-col gap-1.5">
              {formatted.map((entry, index) => (
                <li key={entry.name} className="flex items-center gap-2 text-xs text-ink-muted">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                  {entry.name} · {entry.value}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </Card>
  );
}
