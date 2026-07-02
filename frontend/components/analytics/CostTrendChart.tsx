"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DashboardMetrics } from "@/lib/types";
import { Card } from "@/components/ui/Card";

export function CostTrendChart({ data }: { data: DashboardMetrics["by_day"] }) {
  const formatted = data.map((point) => ({ ...point, label: point.date.slice(5) }));

  return (
    <Card className="p-4">
      <p className="mb-3 font-mono text-xs uppercase tracking-wide text-ink-faint">Cost per day</p>
      <div className="h-56">
        {formatted.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-ink-faint">No spend in this window</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={formatted} margin={{ top: 4, right: 12, bottom: 0, left: -12 }}>
              <CartesianGrid vertical={false} stroke="#DCE0DA" />
              <XAxis dataKey="label" tick={{ fontSize: 11, fontFamily: "var(--font-plex-mono)", fill: "#8A9390" }} axisLine={{ stroke: "#DCE0DA" }} tickLine={false} />
              <YAxis
                tick={{ fontSize: 11, fontFamily: "var(--font-plex-mono)", fill: "#8A9390" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value: number) => `$${value.toFixed(2)}`}
                width={48}
              />
              <Tooltip
                contentStyle={{ borderRadius: 4, borderColor: "#DCE0DA", fontSize: 12, fontFamily: "var(--font-inter)" }}
                formatter={(value) => [`$${Number(value).toFixed(4)}`, "Cost"]}
                cursor={{ stroke: "#DCE0DA" }}
              />
              <Line type="monotone" dataKey="cost_usd" stroke="#2F3EE0" strokeWidth={2} dot={{ r: 3, fill: "#2F3EE0" }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  );
}
