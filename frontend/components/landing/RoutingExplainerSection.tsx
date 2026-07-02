import { Workflow } from "lucide-react";
import { Reveal } from "@/components/landing/Reveal";
import { LANDING_SHELL } from "@/lib/constants/landing";

const PLAN_STEPS = [
  { capability: "finance", parameter: "TSLA" },
  { capability: "news", parameter: "Tesla" },
];

const LLM_CALLS = [
  { task: "query_planning", provider: "Groq", tokens: 222 },
  { task: "synthesis", provider: "Anthropic", tokens: 736 },
  { task: "verification", provider: "Groq", tokens: 188 },
];

export function RoutingExplainerSection() {
  return (
    <section id="routing" className="scroll-mt-16 border-b border-line bg-surface-sunken py-14 md:py-16">
      <div className={`grid grid-cols-1 items-center gap-8 md:grid-cols-2 md:gap-10 ${LANDING_SHELL}`}>
        <Reveal>
          <p className="font-mono text-xs uppercase tracking-wide text-route">How it works</p>
          <h2 className="mt-3 font-display text-3xl tracking-tight text-ink md:text-4xl">The plan is visible, not a black box.</h2>
          <p className="mt-5 text-base leading-relaxed text-ink-muted">
            A question gets broken into steps before anything runs. Independent steps execute concurrently, get
            synthesized into one answer, and checked against the retrieved context before it reaches you. Every
            response shows exactly which sources ran and what each model call cost.
          </p>
        </Reveal>
        <Reveal delay={150}>
          <div className="rounded-md border border-line bg-surface p-5 transition-shadow duration-300 hover:shadow-md">
          <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">You asked</p>
          <p className="mt-1.5 text-sm text-ink">&ldquo;What&apos;s Tesla&apos;s stock price and any recent news about them?&rdquo;</p>

          <div className="mt-5 border-t border-line pt-5">
            <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Plan</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {PLAN_STEPS.map((step) => (
                <span key={step.capability} className="rounded-sm bg-route-soft px-2 py-0.5 font-mono text-xs text-route">
                  {step.capability}: {step.parameter}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-5 border-t border-line pt-5">
            <div className="mb-2 flex items-center gap-1.5 font-mono text-xs uppercase tracking-wide text-ink-faint">
              <Workflow className="h-3 w-3" strokeWidth={1.75} />
              LLM calls
            </div>
            <div className="flex flex-col gap-1">
              {LLM_CALLS.map((call) => (
                <div key={call.task} className="flex items-center justify-between font-mono text-xs text-ink-muted">
                  <span>
                    {call.task} · {call.provider}
                  </span>
                  <span>{call.tokens} tok</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-5 flex items-center justify-between border-t border-line pt-5 font-mono text-xs text-ink-faint">
            <span>2 steps · 1146 tokens</span>
            <span className="text-live">&lt;$0.01</span>
          </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
