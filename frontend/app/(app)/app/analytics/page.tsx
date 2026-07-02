"use client";

import { useState } from "react";
import Link from "next/link";
import { RefreshCw } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { MetricsGrid } from "@/components/analytics/MetricsGrid";
import { QueryVolumeChart } from "@/components/analytics/QueryVolumeChart";
import { CostTrendChart } from "@/components/analytics/CostTrendChart";
import { ConfidenceTrendChart } from "@/components/analytics/ConfidenceTrendChart";
import { ProviderCostChart } from "@/components/analytics/ProviderCostChart";
import { ModelUsageChart } from "@/components/analytics/ModelUsageChart";
import { RetrievalStrategyChart } from "@/components/analytics/RetrievalStrategyChart";
import { CapabilityBreakdownChart } from "@/components/analytics/CapabilityBreakdownChart";
import { TaskTokenBreakdownChart } from "@/components/analytics/TaskTokenBreakdownChart";
import { Skeleton } from "@/components/ui/Skeleton";
import { Dropdown } from "@/components/ui/Dropdown";
import { ErrorState } from "@/components/ui/ErrorState";
import { Card } from "@/components/ui/Card";
import { useAnalytics } from "@/hooks/useAnalytics";
import { useModelSettings } from "@/hooks/useModelSettings";
import { cn, formatRelativeTime } from "@/lib/utils";

const RANGE_OPTIONS = [
  { value: "7", label: "Last 7 days" },
  { value: "30", label: "Last 30 days" },
  { value: "90", label: "Last 90 days" },
];

const EMPTY_METRICS = {
  total_queries: 0,
  prompt_tokens: 0,
  completion_tokens: 0,
  total_tokens: 0,
  avg_tokens_per_query: 0,
  total_cost_usd: 0,
  avg_latency_ms: 0,
  avg_confidence: 0,
  cache_hit_rate: 0,
  by_provider: [],
  by_model: [],
  by_day: [],
  by_retrieval_strategy: [],
  by_capability: [],
  by_task: [],
};

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <p className="font-mono text-[11px] uppercase tracking-wide text-ink-faint">{children}</p>;
}

export default function AnalyticsPage() {
  const [days, setDays] = useState("7");
  const { metrics, isLoading, isRefreshing, lastUpdated, error, refresh } = useAnalytics(Number(days));
  const { catalog } = useModelSettings();
  const data = metrics ?? EMPTY_METRICS;
  const isEmpty = data.total_queries === 0;

  return (
    <div className="flex h-full flex-1 flex-col overflow-y-auto">
      <Topbar
        title="Analytics"
        description="Usage, cost, models, and answer quality across your workspace"
        actions={
          <div className="flex items-center gap-2">
            {lastUpdated && (
              <span className="hidden font-mono text-[11px] text-ink-faint lg:inline">
                Updated {formatRelativeTime(lastUpdated.toISOString())}
              </span>
            )}
            <button
              type="button"
              onClick={() => void refresh()}
              disabled={isLoading || isRefreshing}
              aria-label="Refresh analytics"
              title="Refresh analytics"
              className="flex h-8 w-8 items-center justify-center rounded-md border border-line bg-surface text-ink-muted transition-colors hover:border-line-strong hover:text-ink disabled:opacity-50"
            >
              <RefreshCw className={cn("h-3.5 w-3.5", isRefreshing && "animate-spin-smooth")} strokeWidth={1.75} />
            </button>
            <Dropdown value={days} onChange={setDays} options={RANGE_OPTIONS} className="w-40" />
          </div>
        }
      />
      <div className="flex flex-col gap-6 p-4 md:p-8">
        {isLoading ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, index) => (
              <Skeleton key={index} className="h-20" />
            ))}
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={refresh} />
        ) : (
          <>
            {isEmpty && (
              <Card className="border-dashed p-4">
                <p className="text-sm text-ink">No queries in this period yet.</p>
                <p className="mt-1 text-sm text-ink-muted">
                  Start a conversation in{" "}
                  <Link href="/app" className="text-route hover:underline">
                    Chat
                  </Link>{" "}
                  to populate usage, cost, and model breakdowns below. Charts stay visible so you can see what will appear.
                </p>
              </Card>
            )}

            <MetricsGrid metrics={data} />

            <div className="flex flex-col gap-3">
              <SectionLabel>Models &amp; providers</SectionLabel>
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <ModelUsageChart data={data.by_model} catalog={catalog} />
                <ProviderCostChart data={data.by_provider} />
              </div>
            </div>

            <div className="flex flex-col gap-3">
              <SectionLabel>Volume &amp; spend</SectionLabel>
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <QueryVolumeChart data={data.by_day} />
                <CostTrendChart data={data.by_day} />
              </div>
            </div>

            <div className="flex flex-col gap-3">
              <SectionLabel>Answer quality</SectionLabel>
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <ConfidenceTrendChart data={data.by_day} />
                <RetrievalStrategyChart data={data.by_retrieval_strategy} />
              </div>
            </div>

            <div className="flex flex-col gap-3">
              <SectionLabel>Task breakdown</SectionLabel>
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <CapabilityBreakdownChart data={data.by_capability} />
                <TaskTokenBreakdownChart data={data.by_task} />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
