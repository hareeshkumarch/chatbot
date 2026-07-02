"use client";

import { useCallback, useEffect, useState } from "react";
import type { ApiKeyField } from "@/lib/types";
import { getApiKeys, updateApiKeys } from "@/lib/api";

export function useApiKeys() {
  const [fields, setFields] = useState<ApiKeyField[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await getApiKeys();
      setFields(response.fields);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load API keys");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const save = useCallback(
    async (keys: Record<string, string | null>) => {
      setIsSaving(true);
      try {
        const response = await updateApiKeys(keys);
        setFields(response.fields);
        setError(null);
        return response;
      } catch (err) {
        const message = err instanceof Error ? err.message : "failed to save API keys";
        setError(message);
        throw err;
      } finally {
        setIsSaving(false);
      }
    },
    [],
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { fields, isLoading, isSaving, error, refresh, save };
}
