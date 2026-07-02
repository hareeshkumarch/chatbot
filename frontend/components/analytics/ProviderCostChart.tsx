"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DashboardMetrics } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { providerLabel } from "@/lib/constants/models";
import { formatNumber } from "@/lib/utils";

export function ProviderCostChart({ data }: { data: DashboardMetrics["by_provider"] }) {
  const formatted = data.map((point) => ({
    ...point,
    label: providerLabel(point.provider),
    input: point.prompt_tokens,
    output: point.completion_tokens,
  }));

  return (
    <Card className="p-4">
      <p className="mb-1 font-mono text-xs uppercase tracking-wide text-ink-faint">Tokens by provider</p>
      <p className="mb-3 text-[11px] text-ink-muted">Aggregated from every LLM call in each provider chain</p>
      <div className="h-56">
        {formatted.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-ink-faint">No provider activity yet</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={formatted} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 8 }}>
              <CartesianGrid horizontal={false} stroke="#DCE0DA" />
              <XAxis type="number" tick={{ fontSize: 11, fontFamily: "var(--font-plex-mono)", fill: "#8A9390" }} axisLine={false} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="label" width={80} tick={{ fontSize: 12, fill: "#14181A" }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ borderRadius: 4, borderColor: "#DCE0DA", fontSize: 12, fontFamily: "var(--font-inter)" }}
                cursor={{ fill: "#ECEEEA" }}
                formatter={(value, name) => [formatNumber(Number(value)), name === "input" ? "Input tokens" : "Output tokens"]}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} formatter={(value) => (value === "input" ? "Input" : "Output")} />
              <Bar dataKey="input" stackId="tokens" fill="#2F3EE0" radius={[0, 0, 0, 0]} maxBarSize={20} />
              <Bar dataKey="output" stackId="tokens" fill="#1B8C6F" radius={[0, 2, 2, 0]} maxBarSize={20} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  );
}
