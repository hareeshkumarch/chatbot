"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DashboardMetrics, ModelCatalog } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { modelLabel, providerLabel } from "@/lib/constants/models";
import { formatNumber } from "@/lib/utils";

export function ModelUsageChart({ data, catalog }: { data: DashboardMetrics["by_model"]; catalog: ModelCatalog | null }) {
  const formatted = data.slice(0, 8).map((point) => ({
    ...point,
    label: `${providerLabel(point.provider)} · ${modelLabel(catalog, point.provider, point.model)}`,
  }));

  return (
    <Card className="p-4">
      <p className="mb-1 font-mono text-xs uppercase tracking-wide text-ink-faint">Tokens by model</p>
      <p className="mb-3 text-[11px] text-ink-muted">Total tokens consumed per model across planning, synthesis, and verification</p>
      <div className="h-56">
        {formatted.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-ink-faint">No model usage yet — send a chat message to see data here</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={formatted} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 8 }}>
              <CartesianGrid horizontal={false} stroke="#DCE0DA" />
              <XAxis type="number" tick={{ fontSize: 11, fontFamily: "var(--font-plex-mono)", fill: "#8A9390" }} axisLine={false} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="label" width={140} tick={{ fontSize: 11, fill: "#14181A" }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ borderRadius: 4, borderColor: "#DCE0DA", fontSize: 12, fontFamily: "var(--font-inter)" }}
                cursor={{ fill: "#ECEEEA" }}
                formatter={(value, _name, item) => {
                  const row = item.payload as (typeof formatted)[number];
                  return [
                    `${formatNumber(Number(value))} total (${formatNumber(row.prompt_tokens)} in / ${formatNumber(row.completion_tokens)} out)`,
                    "Tokens",
                  ];
                }}
              />
              <Bar dataKey="total_tokens" fill="#3B6FD8" radius={[0, 2, 2, 0]} maxBarSize={20} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  );
}
