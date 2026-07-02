import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { HeroDemo } from "@/components/landing/HeroDemo";
import { LANDING_SHELL } from "@/lib/constants/landing";

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-line">
      <div className="pointer-events-none absolute inset-0 opacity-[0.35] [background-image:radial-gradient(circle_at_1px_1px,#C3C9C1_1px,transparent_0)] [background-size:28px_28px] [mask-image:radial-gradient(ellipse_70%_60%_at_50%_0%,#000_40%,transparent_100%)]" />

      <div className={`relative grid grid-cols-1 items-center gap-6 py-12 md:py-16 lg:grid-cols-2 lg:gap-8 ${LANDING_SHELL}`}>
        <div>
          <p className="animate-hero-rise inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 font-mono text-[11px] uppercase tracking-wide text-ink-muted" style={{ animationDelay: "0ms" }}>
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-signal-pulse rounded-full bg-live" />
            </span>
            Built for teams and agents
          </p>
          <h1 className="mt-5 font-display text-4xl leading-[1.05] tracking-tight text-ink md:text-6xl">
            <span className="animate-hero-rise block" style={{ animationDelay: "70ms" }}>
              Ask once.
            </span>
            <span className="animate-hero-rise block" style={{ animationDelay: "180ms" }}>
              Answered from
            </span>
            <span className="animate-hero-rise block text-route" style={{ animationDelay: "290ms" }}>
              every source.
            </span>
          </h1>
          <p className="animate-hero-rise mt-6 text-base leading-relaxed text-ink-muted md:text-lg lg:max-w-none" style={{ animationDelay: "420ms" }}>
            One planner routes each question across your documents, database, connected tools, and the live web —
            in parallel — then answers with citations, verified against what it actually retrieved.
          </p>
          <div className="animate-hero-rise mt-8 flex flex-wrap items-center gap-3" style={{ animationDelay: "540ms" }}>
            <Link
              href="/app"
              className="group flex items-center gap-1.5 rounded-md bg-ink px-5 py-3 text-sm font-medium text-canvas transition-all hover:opacity-90"
            >
              Launch app
              <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" strokeWidth={2} />
            </Link>
            <a
              href="#capabilities"
              className="rounded-md border border-line px-5 py-3 text-sm font-medium text-ink transition-colors hover:border-line-strong"
            >
              See what it can do
            </a>
          </div>
          <p className="animate-hero-rise mt-5 font-mono text-[11px] text-ink-faint" style={{ animationDelay: "640ms" }}>
            No login required · 15 connectors · 6 model providers
          </p>
        </div>

        <div className="animate-hero-rise" style={{ animationDelay: "300ms" }}>
          <HeroDemo />
        </div>
      </div>
    </section>
  );
}
