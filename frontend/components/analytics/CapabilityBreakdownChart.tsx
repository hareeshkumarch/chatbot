"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DashboardMetrics } from "@/lib/types";
import { Card } from "@/components/ui/Card";

export function CapabilityBreakdownChart({ data }: { data: DashboardMetrics["by_capability"] }) {
  const formatted = data.map((point) => ({ name: point.capability, count: point.count }));

  return (
    <Card className="p-4">
      <p className="mb-3 font-mono text-xs uppercase tracking-wide text-ink-faint">Agents used per question</p>
      {formatted.length === 0 ? (
        <div className="flex h-56 items-center justify-center text-sm text-ink-faint">No plan activity yet</div>
      ) : (
        <ResponsiveContainer width="100%" height={224}>
          <BarChart data={formatted} layout="vertical" margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#DCE0DA" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 11, fill: "#8A9390" }} axisLine={false} tickLine={false} allowDecimals={false} />
            <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 11, fill: "#5B6461" }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ borderRadius: 4, borderColor: "#DCE0DA", fontSize: 12 }} cursor={{ fill: "#ECEEEA" }} />
            <Bar dataKey="count" fill="#2F3EE0" radius={[0, 3, 3, 0]} barSize={16} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
