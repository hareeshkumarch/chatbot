import { ShieldCheck, Coins, Gauge } from "lucide-react";
import { Reveal } from "@/components/landing/Reveal";
import { LANDING_SHELL } from "@/lib/constants/landing";

const POINTS = [
  {
    icon: ShieldCheck,
    title: "Every answer is checked",
    description: "A verification pass compares the answer against the retrieved context and flags anything unsupported instead of guessing.",
  },
  {
    icon: Coins,
    title: "Cost you can actually see",
    description: "Planning, synthesis, and verification are separate model calls — each one tracked, so the cost per question is the real number.",
  },
  {
    icon: Gauge,
    title: "A dashboard, not a guess",
    description: "Query volume, spend, confidence trends, and which agents ran, broken down by day and by task.",
  },
];

export function TrustSection() {
  return (
    <section className="border-b border-line py-14 md:py-16">
      <div className={LANDING_SHELL}>
        <Reveal>
          <p className="font-mono text-xs uppercase tracking-wide text-route">Observability</p>
          <h2 className="mt-3 font-display text-3xl tracking-tight text-ink md:text-4xl">Nothing about it is a black box.</h2>
        </Reveal>
        <div className="mt-12 grid grid-cols-1 gap-10 sm:grid-cols-3">
          {POINTS.map((point, index) => {
            const Icon = point.icon;
            return (
              <Reveal key={point.title} delay={index * 80}>
                <div className="group">
                  <div className="flex h-11 w-11 items-center justify-center rounded-full bg-route-soft transition-transform duration-200 group-hover:scale-105">
                    <Icon className="h-5 w-5 text-route" strokeWidth={1.75} />
                  </div>
                  <p className="mt-4 font-display text-lg text-ink">{point.title}</p>
                  <p className="mt-2 text-sm leading-relaxed text-ink-muted">{point.description}</p>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
