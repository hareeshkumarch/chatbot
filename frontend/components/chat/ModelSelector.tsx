"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { Bot, Cpu } from "lucide-react";
import { useModelSettings } from "@/hooks/useModelSettings";
import { useChatStore } from "@/store/chatStore";
import { modelLabel, providerIcon, providerLabel, TIER_LABELS } from "@/lib/constants/models";
import { cn } from "@/lib/utils";

export function ModelSelector() {
  const provider = useChatStore((state) => state.provider);
  const model = useChatStore((state) => state.model);
  const setProvider = useChatStore((state) => state.setProvider);
  const setModel = useChatStore((state) => state.setModel);
  const { catalog } = useModelSettings();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const configuredProviders = useMemo(() => catalog?.providers.filter((entry) => entry.configured) ?? [], [catalog]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const activeModelId = useMemo(() => {
    if (!provider) return null;
    const entry = configuredProviders.find((item) => item.provider === provider);
    return model ?? entry?.default_model ?? null;
  }, [provider, model, configuredProviders]);

  const buttonLabel = useMemo(() => {
    if (!provider || !activeModelId) return "Auto route";
    return modelLabel(catalog, provider, activeModelId);
  }, [provider, activeModelId, catalog]);

  const buttonDetail = useMemo(() => {
    if (!provider || !activeModelId) return "Best provider per task";
    return providerLabel(provider);
  }, [provider, activeModelId]);

  const selectAuto = () => {
    setProvider(null);
    setModel(null);
    setOpen(false);
  };

  const selectModel = (nextProvider: string, nextModel: string) => {
    setProvider(nextProvider);
    setModel(nextModel);
    setOpen(false);
  };

  const isAuto = !provider;

  if (configuredProviders.length === 0) {
    return (
      <Link
        href="/app/settings"
        className="flex h-9 items-center gap-2 rounded-sm border border-line px-3 text-xs text-ink-muted hover:border-line-strong hover:text-ink"
      >
        <Bot className="h-3.5 w-3.5" strokeWidth={1.75} />
        Add model key
      </Link>
    );
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex h-9 max-w-[11rem] items-center gap-2 rounded-sm border border-line px-3 text-left hover:border-line-strong"
      >
        {isAuto ? <Cpu className="h-3.5 w-3.5 shrink-0 text-ink-muted" strokeWidth={1.75} /> : provider && providerIcon(provider) ? (
          (() => {
            const Icon = providerIcon(provider)!;
            return <Icon className="h-3.5 w-3.5 shrink-0 text-ink" />;
          })()
        ) : (
          <Bot className="h-3.5 w-3.5 shrink-0 text-ink-muted" strokeWidth={1.75} />
        )}
        <span className="min-w-0 flex-1">
          <span className="block truncate text-xs text-ink">{buttonLabel}</span>
          <span className="block truncate font-mono text-[10px] text-ink-faint">{buttonDetail}</span>
        </span>
      </button>

      {open && (
        <div className="animate-slide-fade-in absolute bottom-full right-0 z-30 mb-1 w-80 rounded-md border border-line bg-surface shadow-lg">
          <div className="border-b border-line px-3 py-2">
            <p className="text-xs font-medium text-ink">Choose a model</p>
            <p className="text-[11px] text-ink-muted">Auto picks the best provider per task. Or pin a specific model.</p>
          </div>

          <div className="max-h-80 overflow-y-auto p-2">
            <button
              type="button"
              onClick={selectAuto}
              className={cn(
                "flex w-full items-start gap-2 rounded-sm px-2 py-2 text-left hover:bg-surface-sunken",
                isAuto && "bg-route-soft",
              )}
            >
              <Cpu className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-muted" strokeWidth={1.75} />
              <span>
                <span className="block text-xs font-medium text-ink">Auto route</span>
                <span className="block text-[11px] text-ink-muted">Routes each step to the fastest configured provider</span>
              </span>
            </button>

            {configuredProviders.map((entry) => {
              const Icon = providerIcon(entry.provider);
              return (
                <div key={entry.provider} className="mt-2">
                  <div className="flex items-center gap-2 px-2 py-1">
                    {Icon && <Icon className="h-3.5 w-3.5 text-ink" />}
                    <p className="text-[11px] font-medium uppercase tracking-wide text-ink-faint">{providerLabel(entry.provider)}</p>
                  </div>
                  <div className="flex flex-col gap-0.5">
                    {entry.models.map((modelOption) => {
                      const selected = provider === entry.provider && activeModelId === modelOption.id;
                      return (
                        <button
                          key={modelOption.id}
                          type="button"
                          onClick={() => selectModel(entry.provider, modelOption.id)}
                          className={cn(
                            "flex w-full items-center justify-between rounded-sm px-2 py-1.5 text-left hover:bg-surface-sunken",
                            selected && "bg-route-soft",
                          )}
                        >
                          <span className="min-w-0">
                            <span className="block truncate text-xs text-ink">{modelOption.label}</span>
                            <span className="block truncate font-mono text-[10px] text-ink-faint">{modelOption.id}</span>
                          </span>
                          <span className="ml-2 flex shrink-0 flex-col items-end gap-0.5">
                            <span className="rounded-sm bg-surface-sunken px-1.5 py-0.5 font-mono text-[10px] text-ink-muted">
                              {TIER_LABELS[modelOption.tier] ?? modelOption.tier}
                            </span>
                            {modelOption.is_default && (
                              <span className="font-mono text-[10px] text-route">default</span>
                            )}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="border-t border-line px-3 py-2">
            <Link href="/app/settings" className="text-[11px] text-route hover:underline" onClick={() => setOpen(false)}>
              View all models &amp; defaults in Settings
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
