"use client";

import {
  AWSIcon,
  AzureIcon,
  GoogleCloudIcon,
  SlackIcon,
  GitHubIcon,
  JiraIcon,
  ConfluenceIcon,
  NotionIcon,
  GoogleDriveIcon,
  DropboxIcon,
  ZendeskIcon,
  LinearAppIcon,
  MongoDBIcon,
  AnthropicIcon,
  OpenAIIcon,
  GeminiIcon,
  GroqIcon,
  XAIIcon,
  MoonshotIcon,
} from "@/components/icons/BrandIcons";
import { Database, Globe, MessageSquare, FileText, BarChart3, ShieldCheck, Users, Search, Route, Layers, Workflow, CheckCircle2, Package, Cloud } from "lucide-react";

type IconType = React.ComponentType<React.SVGProps<SVGSVGElement>>;

const CONNECTOR_GROUPS: { title: string; icons: IconType[] }[] = [
  { title: "Cloud storage", icons: [AWSIcon, AzureIcon, GoogleCloudIcon] },
  { title: "Team systems", icons: [SlackIcon, GitHubIcon, JiraIcon, ConfluenceIcon, NotionIcon] },
  { title: "Files and support", icons: [GoogleDriveIcon, DropboxIcon, ZendeskIcon, LinearAppIcon] },
  { title: "Databases and web", icons: [MongoDBIcon, Database, Globe] },
];

const PROVIDERS: IconType[] = [AnthropicIcon, OpenAIIcon, GeminiIcon, GroqIcon, XAIIcon, MoonshotIcon];

const PIPELINE = [
  { icon: Layers, label: "Plan" },
  { icon: Workflow, label: "Retrieve" },
  { icon: Route, label: "Route" },
  { icon: CheckCircle2, label: "Verify" },
  { icon: Package, label: "Package" },
];

const OUTPUTS = [
  { icon: MessageSquare, title: "Chat answers", detail: "cited, verified responses" },
  { icon: FileText, title: "Generated reports", detail: "PDF, Word, and HTML" },
  { icon: BarChart3, title: "Usage analytics", detail: "cost, latency, confidence" },
  { icon: ShieldCheck, title: "Governed retrieval", detail: "tenant-scoped context" },
];

function IconTile({ Icon }: { Icon: IconType }) {
  return (
    <div className="flex h-9 w-9 items-center justify-center rounded-md border border-line bg-surface transition-transform duration-200 hover:-translate-y-0.5 hover:border-route">
      <Icon className="h-4 w-4 text-ink" />
    </div>
  );
}

export function ArchitectureDiagram() {
  return (
    <div className="relative w-full overflow-hidden rounded-xl border border-line bg-surface-sunken/40 p-4 md:p-6">
      <div className="pointer-events-none absolute inset-0 opacity-[0.5] [background-image:linear-gradient(#DCE0DA_1px,transparent_1px),linear-gradient(90deg,#DCE0DA_1px,transparent_1px)] [background-size:32px_32px]" />

      <div className="relative grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1.5fr_1fr]">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <Cloud className="h-3.5 w-3.5 text-route" />
            <span className="font-mono text-[11px] uppercase tracking-wide text-route">Available connectors</span>
          </div>
          {CONNECTOR_GROUPS.map((group, gi) => (
            <div
              key={group.title}
              className="animate-hero-rise rounded-lg border border-line bg-surface p-4"
              style={{ animationDelay: `${gi * 90}ms` }}
            >
              <p className="mb-3 text-sm font-medium text-ink">{group.title}</p>
              <div className="flex flex-wrap gap-2">
                {group.icons.map((Icon, i) => (
                  <IconTile key={i} Icon={Icon} />
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-5">
          <div className="animate-hero-rise rounded-lg border border-route/30 bg-route-soft/40 p-5" style={{ animationDelay: "120ms" }}>
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-route/30 bg-surface">
                <Users className="h-4 w-4 text-route" strokeWidth={1.75} />
              </div>
              <div>
                <p className="font-display text-base text-ink">Users and teams</p>
                <p className="mt-0.5 text-sm text-ink-muted">Ask once across documents, tools, data, and the web</p>
              </div>
            </div>
          </div>

          <div className="flex justify-center">
            <FlowConnector />
          </div>

          <div className="animate-hero-rise rounded-lg border border-line bg-surface p-5" style={{ animationDelay: "240ms" }}>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="font-display text-lg text-ink">Enterprise AI Hub</p>
                <p className="mt-1 max-w-xs text-sm text-ink-muted">Planner, retrieval, verification, and report generation</p>
              </div>
              <span className="flex shrink-0 items-center gap-1.5 rounded-full bg-live-soft px-3 py-1 font-mono text-[11px] text-live">
                <span className="h-1.5 w-1.5 rounded-full bg-live" />
                routed workspace
              </span>
            </div>
            <div className="mt-4 grid grid-cols-5 gap-2">
              {PIPELINE.map((step, i) => {
                const Icon = step.icon;
                return (
                  <div
                    key={step.label}
                    className="group flex flex-col items-center gap-1.5 rounded-md border border-line bg-canvas px-1 py-2.5 transition-colors hover:border-route hover:bg-route-soft/40"
                  >
                    <Icon className="h-4 w-4 text-route transition-transform duration-200 group-hover:scale-110" strokeWidth={1.75} />
                    <span className="text-[11px] text-ink-muted">{step.label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex justify-center">
            <FlowConnector reverse />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="animate-hero-rise rounded-lg border border-line bg-surface p-4" style={{ animationDelay: "320ms" }}>
              <div className="mb-1 flex items-center gap-1.5">
                <Workflow className="h-3.5 w-3.5 text-route" strokeWidth={1.75} />
                <p className="text-sm font-medium text-ink">LLM providers</p>
              </div>
              <p className="mb-3 text-xs text-ink-faint">Fallback chains by task</p>
              <div className="flex flex-wrap gap-2">
                {PROVIDERS.map((Icon, i) => (
                  <IconTile key={i} Icon={Icon} />
                ))}
              </div>
            </div>
            <div className="animate-hero-rise rounded-lg border border-line bg-surface p-4" style={{ animationDelay: "400ms" }}>
              <div className="mb-1 flex items-center gap-1.5">
                <Search className="h-3.5 w-3.5 text-route" strokeWidth={1.75} />
                <p className="text-sm font-medium text-ink">Live intelligence</p>
              </div>
              <p className="mb-3 text-xs text-ink-faint">Search, news, trends, markets</p>
              <div className="flex flex-wrap gap-1.5">
                {["Tavily", "Exa", "Serper", "Google", "Trends", "Perplexity", "Yahoo", "Census"].map((name) => (
                  <span key={name} className="rounded-sm border border-line bg-canvas px-2 py-1 font-mono text-[10px] text-ink-muted">
                    {name}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <Package className="h-3.5 w-3.5 text-route" strokeWidth={1.75} />
            <span className="font-mono text-[11px] uppercase tracking-wide text-route">What comes back</span>
          </div>
          {OUTPUTS.map((output, i) => {
            const Icon = output.icon;
            return (
              <div
                key={output.title}
                className="group animate-hero-rise flex items-start gap-3 rounded-lg border border-line bg-surface p-4 transition-all duration-200 hover:-translate-x-0.5 hover:border-route"
                style={{ animationDelay: `${i * 90 + 160}ms` }}
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-line bg-canvas transition-colors group-hover:border-route">
                  <Icon className="h-4 w-4 text-route" strokeWidth={1.75} />
                </div>
                <div>
                  <p className="text-sm font-medium text-ink">{output.title}</p>
                  <p className="mt-0.5 text-xs text-ink-muted">{output.detail}</p>
                </div>
              </div>
            );
          })}
          <div className="animate-hero-rise rounded-lg border border-live/30 bg-live-soft/40 p-4" style={{ animationDelay: "600ms" }}>
            <p className="text-sm font-medium text-live">More destinations as connectors come online</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function FlowConnector({ reverse = false }: { reverse?: boolean }) {
  return (
    <svg width="24" height="40" viewBox="0 0 24 40" fill="none" className="text-route">
      <line x1="12" y1="0" x2="12" y2="40" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.3" />
      <circle r="3" fill="currentColor">
        <animateMotion dur="1.8s" repeatCount="indefinite" path={reverse ? "M12 40 L12 0" : "M12 0 L12 40"} />
        <animate attributeName="opacity" values="0;1;1;0" dur="1.8s" repeatCount="indefinite" />
      </circle>
      <path d={reverse ? "M8 6 L12 2 L16 6" : "M8 34 L12 38 L16 34"} stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.4" fill="none" />
    </svg>
  );
}
