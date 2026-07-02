import { FileText, Database, Plug, Globe, Newspaper, MapPin, TrendingUp, LineChart, Users } from "lucide-react";
import { Reveal } from "@/components/landing/Reveal";
import { LANDING_SHELL } from "@/lib/constants/landing";

const CAPABILITIES = [
  { icon: FileText, title: "Your documents", description: "Cross-reference uploaded PDFs, docs, and spreadsheets with cited passages." },
  { icon: Database, title: "Your database", description: "Ask in plain language; a guarded, read-only SQL step handles the query." },
  { icon: Plug, title: "Connected tools", description: "Search Slack, GitHub, Jira, Confluence, Notion, and more directly." },
  { icon: Globe, title: "The open web", description: "Routed through Tavily, Exa, or Serper depending on what the question needs." },
  { icon: Newspaper, title: "Current news", description: "Fresh headlines and coverage, not stale training data." },
  { icon: MapPin, title: "Places nearby", description: "Local businesses and venues when a question is location-specific." },
  { icon: TrendingUp, title: "Search trends", description: "How interest in a topic has moved over time." },
  { icon: LineChart, title: "Market data", description: "Live quotes, market cap, and price history for public companies." },
  { icon: Users, title: "Demographics", description: "Population, income, and age data by US state." },
];

export function CapabilitiesSection() {
  return (
    <section id="capabilities" className="scroll-mt-16 border-b border-line py-14 md:py-16">
      <div className={LANDING_SHELL}>
        <Reveal>
          <p className="font-mono text-xs uppercase tracking-wide text-route">What you can ask</p>
          <h2 className="mt-3 font-display text-3xl tracking-tight text-ink md:text-4xl">
            Nine kinds of questions, one conversation.
          </h2>
        </Reveal>
        <div className="mt-12 grid grid-cols-1 gap-px overflow-hidden rounded-md border border-line bg-line sm:grid-cols-2 lg:grid-cols-3">
          {CAPABILITIES.map((capability, index) => {
            const Icon = capability.icon;
            return (
              <Reveal key={capability.title} delay={index * 60} className="h-full">
                <div className="group flex h-full flex-col gap-3 bg-surface p-6 transition-colors duration-200 hover:bg-route-soft/40">
                  <Icon className="h-5 w-5 text-route transition-transform duration-200 group-hover:scale-110" strokeWidth={1.75} />
                  <p className="font-display text-base text-ink">{capability.title}</p>
                  <p className="text-sm leading-relaxed text-ink-muted">{capability.description}</p>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
