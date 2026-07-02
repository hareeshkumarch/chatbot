"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronDown } from "lucide-react";
import type { ApiKeyField } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { providerIcon, providerLabel } from "@/lib/constants/models";
import { cn } from "@/lib/utils";

const LLM_KEY_TO_PROVIDER: Record<string, string> = {
  anthropic_api_key: "anthropic",
  openai_api_key: "openai",
  gemini_api_key: "gemini",
  groq_api_key: "groq",
  xai_api_key: "grok",
  moonshot_api_key: "moonshot",
};

interface ApiKeysPanelProps {
  fields: ApiKeyField[];
  isSaving: boolean;
  onSave: (keys: Record<string, string | null>) => Promise<unknown>;
  onSaved?: () => void;
}

export function ApiKeysPanel({ fields, isSaving, onSave, onSaved }: ApiKeysPanelProps) {
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [clears, setClears] = useState<Set<string>>(new Set());
  const [showWeb, setShowWeb] = useState(false);

  useEffect(() => {
    setDrafts({});
    setClears(new Set());
  }, [fields]);

  const llmFields = useMemo(() => fields.filter((field) => field.group === "llm"), [fields]);
  const webFields = useMemo(() => fields.filter((field) => field.group === "intelligence"), [fields]);
  const configuredCount = fields.filter((field) => field.configured).length;

  const hasChanges = useMemo(() => {
    const hasDraft = Object.values(drafts).some((value) => value.trim().length > 0);
    return hasDraft || clears.size > 0;
  }, [drafts, clears]);

  const updateDraft = (key: string, value: string) => {
    setDrafts((prev) => ({ ...prev, [key]: value }));
    if (value.trim()) {
      setClears((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  };

  const handleSave = async () => {
    const keys: Record<string, string | null> = {};
    for (const field of fields) {
      if (clears.has(field.key)) {
        keys[field.key] = null;
        continue;
      }
      const draft = drafts[field.key]?.trim();
      if (draft) keys[field.key] = draft;
    }
    if (Object.keys(keys).length === 0) return;
    await onSave(keys);
    onSaved?.();
  };

  const renderLlmRow = (field: ApiKeyField) => {
    const provider = LLM_KEY_TO_PROVIDER[field.key];
    const Icon = provider ? providerIcon(provider) : null;
    const label = provider ? providerLabel(provider) : field.label;
    const cleared = clears.has(field.key);
    const configured = field.configured && !cleared;

    return (
      <div key={field.key} className="flex flex-col gap-2 rounded-md border border-line bg-canvas px-3 py-3 sm:flex-row sm:items-center sm:gap-4">
        <div className="flex min-w-[7.5rem] shrink-0 items-center gap-2">
          {Icon && <Icon className="h-4 w-4 text-ink" />}
          <span className="text-sm font-medium text-ink">{label}</span>
          <span className={cn("ml-auto h-2 w-2 rounded-full sm:ml-0", configured ? "bg-route" : "bg-line-strong")} />
        </div>
        <Input
          type={field.secret ? "password" : "text"}
          autoComplete="off"
          placeholder={configured ? "Enter new key to replace" : field.placeholder}
          value={drafts[field.key] ?? ""}
          onChange={(event) => updateDraft(field.key, event.target.value)}
          className="h-9 flex-1 font-mono text-xs"
        />
        {configured && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="shrink-0 self-start text-attn sm:self-center"
            onClick={() => {
              setClears((prev) => new Set(prev).add(field.key));
              setDrafts((prev) => ({ ...prev, [field.key]: "" }));
            }}
          >
            Remove
          </Button>
        )}
        {configured && field.masked_value && !drafts[field.key] && (
          <span className="hidden font-mono text-[10px] text-ink-faint xl:block">{field.masked_value}</span>
        )}
      </div>
    );
  };

  const renderWebRow = (field: ApiKeyField) => {
    const cleared = clears.has(field.key);
    const configured = field.configured && !cleared;

    return (
      <div key={field.key} className="grid gap-2 py-2 sm:grid-cols-[10rem_1fr_auto] sm:items-center">
        <p className="text-sm text-ink">{field.label}</p>
        <Input
          type={field.secret ? "password" : "text"}
          autoComplete="off"
          placeholder={field.placeholder}
          value={drafts[field.key] ?? ""}
          onChange={(event) => updateDraft(field.key, event.target.value)}
          className="h-9 font-mono text-xs"
        />
        <span className={cn("font-mono text-[11px]", configured ? "text-route" : "text-ink-faint")}>{configured ? "Set" : "Optional"}</span>
      </div>
    );
  };

  return (
    <>
      <Card className="p-5 md:p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-sm text-ink">API keys</h2>
            <p className="mt-1 text-sm text-ink-muted">Paste keys for the providers you want, then save at the bottom.</p>
          </div>
          <p className="font-mono text-xs text-ink-faint">{configuredCount} connected</p>
        </div>

        <div className="mt-6">
          <p className="font-mono text-[10px] uppercase tracking-wide text-ink-faint">Chat models</p>
          <div className="mt-3 grid gap-3 lg:grid-cols-2">{llmFields.map(renderLlmRow)}</div>
        </div>

        <div className="mt-6 border-t border-line pt-4">
          <button type="button" onClick={() => setShowWeb((prev) => !prev)} className="flex w-full items-center justify-between text-left">
            <div>
              <p className="text-sm text-ink">Web search &amp; live data</p>
              <p className="text-xs text-ink-muted">Optional — Tavily, Serper, Perplexity, and more</p>
            </div>
            <ChevronDown className={cn("h-4 w-4 shrink-0 text-ink-faint transition-transform", showWeb && "rotate-180")} />
          </button>
          {showWeb && <div className="mt-3 grid gap-1 lg:grid-cols-2">{webFields.map(renderWebRow)}</div>}
        </div>
      </Card>

      <div className="sticky bottom-0 z-10 -mx-4 mt-4 border-t border-line bg-canvas/95 px-4 py-4 backdrop-blur-sm md:-mx-8 md:px-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-ink-muted">{hasChanges ? "You have unsaved changes" : "Enter at least one key, then save"}</p>
          <Button type="button" disabled={!hasChanges || isSaving} onClick={handleSave}>
            {isSaving ? "Saving..." : "Save API keys"}
          </Button>
        </div>
      </div>
    </>
  );
}
