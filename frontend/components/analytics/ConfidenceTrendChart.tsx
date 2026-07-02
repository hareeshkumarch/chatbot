"use client";

import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DashboardMetrics } from "@/lib/types";
import { Card } from "@/components/ui/Card";

export function ConfidenceTrendChart({ data }: { data: DashboardMetrics["by_day"] }) {
  const formatted = data.filter((point) => point.queries > 0).map((point) => ({ ...point, label: point.date.slice(5) }));

  return (
    <Card className="p-4">
      <p className="mb-3 font-mono text-xs uppercase tracking-wide text-ink-faint">Answer confidence trend</p>
      <div className="h-56">
        {formatted.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-ink-faint">No grounded answers in this window</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={formatted} margin={{ top: 4, right: 12, bottom: 0, left: -12 }}>
              <CartesianGrid vertical={false} stroke="#DCE0DA" />
              <XAxis dataKey="label" tick={{ fontSize: 11, fontFamily: "var(--font-plex-mono)", fill: "#8A9390" }} axisLine={{ stroke: "#DCE0DA" }} tickLine={false} />
              <YAxis
                domain={[0, 1]}
                tick={{ fontSize: 11, fontFamily: "var(--font-plex-mono)", fill: "#8A9390" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value: number) => `${Math.round(value * 100)}%`}
                width={40}
              />
              <ReferenceLine y={0.7} stroke="#C4432B" strokeDasharray="3 3" strokeOpacity={0.5} />
              <Tooltip
                contentStyle={{ borderRadius: 4, borderColor: "#DCE0DA", fontSize: 12, fontFamily: "var(--font-inter)" }}
                formatter={(value) => [`${Math.round(Number(value) * 100)}%`, "Avg confidence"]}
                cursor={{ stroke: "#DCE0DA" }}
              />
              <Line type="monotone" dataKey="avg_confidence" stroke="#1B8C6F" strokeWidth={2} dot={{ r: 3, fill: "#1B8C6F" }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  );
}
