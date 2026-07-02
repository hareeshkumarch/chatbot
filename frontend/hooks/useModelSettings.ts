"use client";

import { useCallback, useEffect, useState } from "react";
import type { ModelCatalog, ProviderInfo, TaskRoutingInfo } from "@/lib/types";
import { listModelCatalog, listProviders, listTaskRouting } from "@/lib/api";

export function useModelSettings() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [catalog, setCatalog] = useState<ModelCatalog | null>(null);
  const [taskRouting, setTaskRouting] = useState<TaskRoutingInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const [providerList, taskList, modelCatalog] = await Promise.all([listProviders(), listTaskRouting(), listModelCatalog()]);
      setProviders(providerList);
      setTaskRouting(taskList);
      setCatalog(modelCatalog);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load model settings");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { providers, catalog, taskRouting, isLoading, error, refresh };
}
