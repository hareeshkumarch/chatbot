"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DashboardMetrics } from "@/lib/types";
import { Card } from "@/components/ui/Card";

export function QueryVolumeChart({ data }: { data: DashboardMetrics["by_day"] }) {
  const formatted = data.map((point) => ({ ...point, label: point.date.slice(5) }));

  return (
    <Card className="p-4">
      <p className="mb-3 font-mono text-xs uppercase tracking-wide text-ink-faint">Queries per day</p>
      <div className="h-56">
        {formatted.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-ink-faint">No queries in this window</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={formatted} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
              <CartesianGrid vertical={false} stroke="#DCE0DA" />
              <XAxis dataKey="label" tick={{ fontSize: 11, fontFamily: "var(--font-plex-mono)", fill: "#8A9390" }} axisLine={{ stroke: "#DCE0DA" }} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fontFamily: "var(--font-plex-mono)", fill: "#8A9390" }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip
                contentStyle={{ borderRadius: 4, borderColor: "#DCE0DA", fontSize: 12, fontFamily: "var(--font-inter)" }}
                cursor={{ fill: "#E7E9FC" }}
                formatter={(value, name, item) => {
                  if (name === "queries") return [value, "Queries"];
                  const row = item.payload as (typeof formatted)[number];
                  return [`${row.tokens} total (${row.prompt_tokens} in / ${row.completion_tokens} out)`, "Tokens"];
                }}
              />
              <Bar dataKey="queries" fill="#2F3EE0" radius={[2, 2, 0, 0]} maxBarSize={28} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  );
}
