import { ExternalLink, Workflow } from "lucide-react";
import type { DisplayMessage } from "@/store/chatStore";
import { formatNumber } from "@/lib/utils";

function formatCost(cost: number): string {
  if (cost === 0) return "$0.00";
  if (cost < 0.01) return "<$0.01";
  return `$${cost.toFixed(4)}`;
}

function totalTokens(message: DisplayMessage): number {
  return message.llmCalls.reduce(
    (sum, call) => sum + (call.total_tokens ?? call.prompt_tokens + call.completion_tokens),
    0,
  );
}

export function TraceDetails({ message }: { message: DisplayMessage }) {
  if (message.llmCalls.length === 0 && !message.phoenixTraceUrl) return null;

  const tokens = totalTokens(message);

  return (
    <div className="mt-2 flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2 font-mono text-[11px] text-ink-faint">
        <span className="inline-flex items-center gap-1.5">
          <Workflow className="h-3 w-3" strokeWidth={1.75} />
          {message.plan.length > 0 ? `${message.plan.length} step${message.plan.length > 1 ? "s" : ""}` : "trace"}
          {tokens > 0 && ` · ${formatNumber(tokens)} tokens`}
          {message.costUsd !== null && ` · ${formatCost(message.costUsd)}`}
        </span>
        {message.phoenixTraceUrl && (
          <a
            href={message.phoenixTraceUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-route transition-colors hover:text-ink"
          >
            View in Phoenix
            <ExternalLink className="h-3 w-3" strokeWidth={1.75} />
          </a>
        )}
      </div>
      {message.plan.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {message.plan.map((step, i) => (
            <span key={i} className="rounded-sm bg-route-soft px-2 py-0.5 font-mono text-[11px] text-route">
              {step.capability}
              {step.parameter ? `: ${step.parameter}` : ""}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
