import { ArchitectureDiagram } from "@/components/landing/ArchitectureDiagram";
import { Reveal } from "@/components/landing/Reveal";
import { LANDING_SHELL } from "@/lib/constants/landing";

export function ArchitectureSection() {
  return (
    <section id="architecture" className="scroll-mt-16 border-b border-line py-14 md:py-16">
      <div className={LANDING_SHELL}>
        <Reveal>
          <p className="font-mono text-xs uppercase tracking-wide text-route">The whole system</p>
          <h2 className="mt-3 font-display text-3xl tracking-tight text-ink md:text-4xl">
            One hub. Everything routes through it.
          </h2>
          <p className="mt-4 max-w-3xl text-base leading-relaxed text-ink-muted">
            Questions come in from your team, get planned and routed across connectors, models, and live sources, and
            come back verified — as answers, reports, or analytics. Every piece below is built, not planned.
          </p>
        </Reveal>
        <Reveal delay={150} className="mt-12">
          <ArchitectureDiagram />
        </Reveal>
      </div>
    </section>
  );
}
