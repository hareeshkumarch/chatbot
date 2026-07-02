import type { IntelligenceCapabilities, ModelCatalog } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { providerLabel, providerIcon } from "@/lib/constants/models";
import { cn } from "@/lib/utils";

interface ModelsPanelProps {
  catalog: ModelCatalog | null;
  capabilities: IntelligenceCapabilities | null;
}

export function ModelsPanel({ catalog, capabilities }: ModelsPanelProps) {
  const providers = catalog?.providers ?? [];
  const configured = providers.filter((entry) => entry.configured);
  const locked = providers.filter((entry) => !entry.configured);

  const webActive = capabilities ? Object.values(capabilities).some((sources) => sources.length > 0) : false;

  return (
    <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
      <Card className="p-5 md:p-6">
        <h2 className="font-display text-sm text-ink">Models</h2>
        <p className="mt-1 text-sm text-ink-muted">
          Auto route uses each provider&apos;s default. Pick a specific model from the Chat bar to pin it.
        </p>

        {configured.length === 0 ? (
          <p className="mt-6 rounded-md border border-dashed border-line bg-surface-sunken px-4 py-8 text-center text-sm text-ink-muted">
            Add an API key on the API keys tab to enable models here.
          </p>
        ) : (
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {configured.map((entry) => {
              const Icon = providerIcon(entry.provider);
              const defaultModel = entry.models.find((model) => model.is_default);
              const others = entry.models.filter((model) => !model.is_default);

              return (
                <div key={entry.provider} className="rounded-md border border-line px-4 py-3">
                  <div className="flex items-center gap-2">
                    {Icon && <Icon className="h-4 w-4 text-ink" />}
                    <p className="text-sm font-medium text-ink">{providerLabel(entry.provider)}</p>
                  </div>
                  {defaultModel && (
                    <p className="mt-2 text-sm text-ink-muted">
                      Default <span className="font-medium text-ink">{defaultModel.label}</span>
                    </p>
                  )}
                  {others.length > 0 && (
                    <p className="mt-1 text-xs leading-relaxed text-ink-faint">{others.map((model) => model.label).join(" · ")}</p>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {locked.length > 0 && (
          <p className="mt-4 text-xs text-ink-faint">Not connected: {locked.map((entry) => providerLabel(entry.provider)).join(", ")}</p>
        )}
      </Card>

      {capabilities && (
        <Card className="p-5 md:p-6">
          <h2 className="font-display text-sm text-ink">Live data</h2>
          <p className="mt-1 text-sm text-ink-muted">Enabled when web search keys are saved.</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {(
              [
                ["web_search", "Web search"],
                ["news", "News"],
                ["finance", "Markets"],
                ["trends", "Trends"],
                ["places", "Places"],
                ["direct_answer", "Cited answers"],
                ["demographics", "Demographics"],
              ] as const
            ).map(([key, label]) => {
              const active = (capabilities[key]?.length ?? 0) > 0;
              return (
                <span
                  key={key}
                  className={cn(
                    "rounded-full border px-2.5 py-1 text-xs",
                    active ? "border-route/30 bg-route-soft text-route" : "border-line text-ink-faint",
                  )}
                >
                  {label}
                </span>
              );
            })}
          </div>
          {!webActive && <p className="mt-3 text-xs text-ink-faint">Add a web search key to enable these.</p>}
        </Card>
      )}
    </div>
  );
}
