"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ContentChart } from "@/lib/types";

export function MessageChart({ chart }: { chart: ContentChart }) {
  const data = chart.labels.map((label, index) => {
    const row: Record<string, string | number> = { label };
    for (const [seriesName, values] of Object.entries(chart.series)) {
      row[seriesName] = values[index] ?? 0;
    }
    return row;
  });
  const seriesNames = Object.keys(chart.series);

  return (
    <div className="w-full overflow-hidden rounded-md border border-line bg-surface-sunken p-3">
      <p className="mb-2 font-mono text-[11px] uppercase tracking-wide text-ink-faint">{chart.title}</p>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          {chart.chart_type === "line" ? (
            <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -8 }}>
              <CartesianGrid vertical={false} stroke="#DCE0DA" />
              <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#8A9390" }} axisLine={{ stroke: "#DCE0DA" }} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "#8A9390" }} axisLine={false} tickLine={false} width={36} />
              <Tooltip contentStyle={{ borderRadius: 4, borderColor: "#DCE0DA", fontSize: 12 }} />
              {seriesNames.map((name, index) => (
                <Line
                  key={name}
                  type="monotone"
                  dataKey={name}
                  stroke={index === 0 ? "#2F3EE0" : "#1B8C6F"}
                  strokeWidth={2}
                  dot={{ r: 2, fill: index === 0 ? "#2F3EE0" : "#1B8C6F" }}
                />
              ))}
            </LineChart>
          ) : (
            <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -8 }}>
              <CartesianGrid vertical={false} stroke="#DCE0DA" />
              <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#8A9390" }} axisLine={{ stroke: "#DCE0DA" }} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "#8A9390" }} axisLine={false} tickLine={false} width={36} />
              <Tooltip contentStyle={{ borderRadius: 4, borderColor: "#DCE0DA", fontSize: 12 }} />
              {seriesNames.map((name, index) => (
                <Bar key={name} dataKey={name} fill={index === 0 ? "#2F3EE0" : "#1B8C6F"} radius={[2, 2, 0, 0]} />
              ))}
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
