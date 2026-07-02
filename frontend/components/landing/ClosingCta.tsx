import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Logo, LogoMark } from "@/components/icons/Logo";
import { Reveal } from "@/components/landing/Reveal";
import { LANDING_SHELL } from "@/lib/constants/landing";

export function ClosingCta() {
  return (
    <section className="border-b border-line py-16 md:py-20">
      <Reveal className={`flex flex-col items-center text-center ${LANDING_SHELL}`}>
        <LogoMark className="h-10 w-10" animated />
        <h2 className="mt-6 font-display text-3xl tracking-tight text-ink md:text-4xl">Ask it something real.</h2>
        <p className="mt-4 max-w-md text-base text-ink-muted">
          No setup wall. Add your documents and connectors when you're ready.
        </p>
        <Link
          href="/app"
          className="group mt-8 flex items-center gap-1.5 rounded-sm bg-ink px-6 py-3 text-sm font-medium text-canvas transition-opacity hover:opacity-90"
        >
          Launch app
          <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" strokeWidth={2} />
        </Link>
      </Reveal>
    </section>
  );
}

export function LandingFooter() {
  return (
    <footer className="py-10">
      <div className={`flex flex-col items-center justify-between gap-4 text-center sm:flex-row sm:text-left ${LANDING_SHELL}`}>
        <Logo markClassName="h-6 w-6" textClassName="text-sm" />
        <p className="font-mono text-xs text-ink-faint">Default Workspace</p>
      </div>
    </footer>
  );
}
