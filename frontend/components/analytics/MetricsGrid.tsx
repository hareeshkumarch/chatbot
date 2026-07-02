"use client";

import type { DashboardMetrics } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { StaggerItem } from "@/components/ui/StaggerItem";
import { useCountUp } from "@/hooks/useCountUp";
import { formatCurrency, formatNumber } from "@/lib/utils";

interface StatCardProps {
  label: string;
  target: number;
  format: (value: number) => string;
  index: number;
  hint?: string;
}

function StatCard({ label, target, format, index, hint }: StatCardProps) {
  const animated = useCountUp(target);
  return (
    <StaggerItem index={index} step={45}>
      <Card interactive className="p-4">
        <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">{label}</p>
        <p className="mt-2 font-display text-2xl tabular-nums text-ink">{format(animated)}</p>
        {hint && <p className="mt-1 text-[11px] text-ink-faint">{hint}</p>}
      </Card>
    </StaggerItem>
  );
}

export function MetricsGrid({ metrics }: { metrics: DashboardMetrics }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      <StatCard index={0} label="Queries" target={metrics.total_queries} format={(v) => formatNumber(Math.round(v))} />
      <StatCard
        index={1}
        label="Input tokens"
        target={metrics.prompt_tokens}
        format={(v) => formatNumber(Math.round(v))}
        hint="Sum of all LLM prompt tokens"
      />
      <StatCard
        index={2}
        label="Output tokens"
        target={metrics.completion_tokens}
        format={(v) => formatNumber(Math.round(v))}
        hint="Sum of all LLM completion tokens"
      />
      <StatCard
        index={3}
        label="Total tokens"
        target={metrics.total_tokens}
        format={(v) => formatNumber(Math.round(v))}
        hint="Input + output across every call"
      />
      <StatCard index={4} label="Total cost" target={metrics.total_cost_usd} format={(v) => formatCurrency(v)} />
      <StatCard index={5} label="Avg latency" target={metrics.avg_latency_ms} format={(v) => `${Math.round(v)}ms`} />
      <StatCard
        index={6}
        label="Tokens / query"
        target={metrics.avg_tokens_per_query}
        format={(v) => formatNumber(Math.round(v))}
      />
      <StatCard index={7} label="Avg confidence" target={metrics.avg_confidence * 100} format={(v) => `${Math.round(v)}%`} />
    </div>
  );
}
