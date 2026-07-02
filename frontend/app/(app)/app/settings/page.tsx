"use client";

import { useState } from "react";
import { Topbar } from "@/components/layout/Topbar";
import { Skeleton } from "@/components/ui/Skeleton";
import { ApiKeysPanel } from "@/components/settings/ApiKeysPanel";
import { ModelsPanel } from "@/components/settings/ModelsPanel";
import { useApiKeys } from "@/hooks/useApiKeys";
import { useModelSettings } from "@/hooks/useModelSettings";
import { useIntelligenceCapabilities } from "@/hooks/useIntelligenceCapabilities";
import { useToastStore } from "@/store/toastStore";
import { LANDING_SHELL } from "@/lib/constants/landing";
import { cn } from "@/lib/utils";

type SettingsTab = "keys" | "models";

const TABS: { id: SettingsTab; label: string }[] = [
  { id: "keys", label: "API keys" },
  { id: "models", label: "Models" },
];

export default function SettingsPage() {
  const [tab, setTab] = useState<SettingsTab>("keys");
  const pushToast = useToastStore((state) => state.push);
  const { fields, isLoading: isLoadingApiKeys, isSaving, save } = useApiKeys();
  const { catalog, isLoading: isLoadingModels, refresh: refreshModels } = useModelSettings();
  const { capabilities, isLoading: isLoadingCapabilities, refresh: refreshCapabilities } = useIntelligenceCapabilities();

  const handleApiKeysSaved = async () => {
    await Promise.all([refreshModels(), refreshCapabilities()]);
    pushToast("API keys saved", "live");
    setTab("models");
  };

  const isLoading = tab === "keys" ? isLoadingApiKeys : isLoadingModels || isLoadingCapabilities;

  return (
    <div className="flex h-full flex-1 flex-col overflow-y-auto">
      <Topbar title="Settings" description="Connect providers and see what models are available" />

      <div className={cn("flex-1 py-4 md:py-8", LANDING_SHELL)}>
        <div className="mb-6 flex max-w-md gap-1 rounded-md border border-line bg-surface-sunken p-1">
          {TABS.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setTab(item.id)}
              className={cn(
                "flex-1 rounded-sm px-3 py-2 text-sm transition-colors",
                tab === item.id ? "bg-surface text-ink shadow-sm" : "text-ink-muted hover:text-ink",
              )}
            >
              {item.label}
            </button>
          ))}
        </div>

        {isLoading ? (
          <Skeleton className="h-72" />
        ) : tab === "keys" ? (
          <ApiKeysPanel fields={fields} isSaving={isSaving} onSave={save} onSaved={handleApiKeysSaved} />
        ) : (
          <ModelsPanel catalog={catalog} capabilities={capabilities} />
        )}
      </div>
    </div>
  );
}
