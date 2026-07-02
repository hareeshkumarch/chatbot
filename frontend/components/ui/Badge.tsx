import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Tone = "neutral" | "live" | "attn" | "route";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
  dot?: boolean;
  pulse?: boolean;
}

const toneClasses: Record<Tone, string> = {
  neutral: "bg-surface-sunken text-ink-muted",
  live: "bg-live-soft text-live",
  attn: "bg-attn-soft text-attn",
  route: "bg-route-soft text-route",
};

const dotToneClasses: Record<Tone, string> = {
  neutral: "bg-ink-faint",
  live: "bg-live",
  attn: "bg-attn",
  route: "bg-route",
};

export function Badge({ tone = "neutral", dot = false, pulse = false, className, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm px-2 py-0.5 font-mono text-xs uppercase tracking-wide",
        toneClasses[tone],
        className,
      )}
      {...props}
    >
      {dot && <span className={cn("h-1.5 w-1.5 rounded-full", dotToneClasses[tone], pulse && "animate-signal-pulse")} />}
      {children}
    </span>
  );
}
