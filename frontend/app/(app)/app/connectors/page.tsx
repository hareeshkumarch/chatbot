"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Topbar } from "@/components/layout/Topbar";
import { ConnectorGrid } from "@/components/connectors/ConnectorGrid";
import { AddConnectorModal } from "@/components/connectors/AddConnectorModal";
import { ConfigureConnectorModal } from "@/components/connectors/ConfigureConnectorModal";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { useConnectors } from "@/hooks/useConnectors";
import { useToastStore } from "@/store/toastStore";
import type { Connector } from "@/lib/types";

function OAuthCallbackNotice({ onSettled }: { onSettled: () => void }) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const push = useToastStore((state) => state.push);

  useEffect(() => {
    const connected = searchParams.get("connected");
    const error = searchParams.get("error");
    if (connected) {
      push(`${connected} connected successfully`, "live");
      onSettled();
      router.replace("/connectors");
    } else if (error) {
      push(`Connection failed: ${error.replace(/_/g, " ")}`, "attn");
      router.replace("/connectors");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  return null;
}

export default function ConnectorsPage() {
  const { connectors, types, isLoading, error, refresh, createConnector, updateConnector, updateCredentials, startOAuth, testConnector, syncConnector, removeConnector } =
    useConnectors();
  const [showAddModal, setShowAddModal] = useState(false);
  const [configuring, setConfiguring] = useState<Connector | null>(null);

  const configuringTypeInfo = configuring ? (types.find((t) => t.type === configuring.type) ?? null) : null;

  return (
    <div className="flex h-full flex-1 flex-col overflow-y-auto">
      <Suspense fallback={null}>
        <OAuthCallbackNotice onSettled={refresh} />
      </Suspense>
      <Topbar title="Connectors" description="Bring in data from your cloud storage, SaaS tools, and databases" />
      <div className="p-4 md:p-8">
        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex flex-col gap-4 rounded-md border border-line bg-surface p-4">
                <div className="flex items-center gap-3">
                  <Skeleton className="h-9 w-9 rounded-sm" />
                  <div className="flex flex-1 flex-col gap-1.5">
                    <Skeleton className="h-3.5 w-2/3" />
                    <Skeleton className="h-2.5 w-1/3" />
                  </div>
                </div>
                <Skeleton className="h-2.5 w-1/2" />
                <div className="flex gap-2 border-t border-line pt-3">
                  <Skeleton className="h-5 w-12" />
                  <Skeleton className="h-5 w-12" />
                  <Skeleton className="h-5 w-16" />
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={refresh} />
        ) : (
          <ConnectorGrid
            connectors={connectors}
            onTest={testConnector}
            onSync={syncConnector}
            onDelete={removeConnector}
            onAuthorize={startOAuth}
            onConfigure={setConfiguring}
            onAddNew={() => setShowAddModal(true)}
          />
        )}
      </div>

      <AddConnectorModal open={showAddModal} onClose={() => setShowAddModal(false)} types={types} onCreate={createConnector} onAuthorizeAfterCreate={startOAuth} />
      <ConfigureConnectorModal
        connector={configuring}
        typeInfo={configuringTypeInfo}
        onClose={() => setConfiguring(null)}
        onSave={updateConnector}
        onSaveCredentials={updateCredentials}
      />
    </div>
  );
}
