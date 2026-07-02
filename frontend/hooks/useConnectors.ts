"use client";

import { useCallback, useEffect, useState } from "react";
import type { Connector, ConnectorTypeInfo } from "@/lib/types";
import {
  createConnector as apiCreateConnector,
  deleteConnector as apiDeleteConnector,
  getAuthorizeUrl,
  listConnectorTypes,
  listConnectors,
  syncConnector as apiSyncConnector,
  testConnector as apiTestConnector,
  updateConnector as apiUpdateConnector,
  updateConnectorCredentials as apiUpdateConnectorCredentials,
} from "@/lib/api";

export function useConnectors() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [types, setTypes] = useState<ConnectorTypeInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [connectorList, typeList] = await Promise.all([listConnectors(), listConnectorTypes()]);
      setConnectors(connectorList);
      setTypes(typeList);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load connectors");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const createConnector = useCallback(
    async (payload: { type: string; name: string; config?: Record<string, unknown>; credentials?: Record<string, unknown> }) => {
      const created = await apiCreateConnector(payload);
      setConnectors((prev) => [created, ...prev]);
      return created;
    },
    [],
  );

  const updateConnector = useCallback(async (connectorId: string, payload: { name?: string; config?: Record<string, unknown> }) => {
    const updated = await apiUpdateConnector(connectorId, payload);
    setConnectors((prev) => prev.map((c) => (c.id === connectorId ? updated : c)));
    return updated;
  }, []);

  const updateCredentials = useCallback(async (connectorId: string, credentials: Record<string, unknown>) => {
    const updated = await apiUpdateConnectorCredentials(connectorId, credentials);
    setConnectors((prev) => prev.map((c) => (c.id === connectorId ? updated : c)));
    return updated;
  }, []);

  const startOAuth = useCallback(async (connectorId: string) => {
    const { authorize_url: authorizeUrl } = await getAuthorizeUrl(connectorId);
    window.location.href = authorizeUrl;
  }, []);

  const testConnector = useCallback(async (connectorId: string) => {
    return apiTestConnector(connectorId);
  }, []);

  const syncConnector = useCallback(async (connectorId: string) => {
    const result = await apiSyncConnector(connectorId);
    setConnectors((prev) => prev.map((c) => (c.id === connectorId ? { ...c, status: "syncing" } : c)));
    return result;
  }, []);

  const removeConnector = useCallback(async (connectorId: string) => {
    await apiDeleteConnector(connectorId);
    setConnectors((prev) => prev.filter((c) => c.id !== connectorId));
  }, []);

  return {
    connectors,
    types,
    isLoading,
    error,
    refresh,
    createConnector,
    updateConnector,
    updateCredentials,
    startOAuth,
    testConnector,
    syncConnector,
    removeConnector,
  };
}
