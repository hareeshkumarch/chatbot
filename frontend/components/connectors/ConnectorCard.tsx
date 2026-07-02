"use client";

import { useState } from "react";
import { RefreshCw, Trash2, Zap, Settings2 } from "lucide-react";
import type { Connector } from "@/lib/types";
import { CONNECTOR_META } from "@/lib/constants/connectors";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatRelativeTime } from "@/lib/utils";
import { useToastStore } from "@/store/toastStore";

interface ConnectorCardProps {
  connector: Connector;
  onTest: (id: string) => Promise<{ connected: boolean; detail: string | null }>;
  onSync: (id: string) => Promise<{ queued: boolean }>;
  onDelete: (id: string) => Promise<void>;
  onAuthorize: (id: string) => Promise<void>;
  onConfigure: (connector: Connector) => void;
}

const STATUS_TONE: Record<Connector["status"], "live" | "attn" | "route" | "neutral"> = {
  connected: "live",
  syncing: "route",
  pending_auth: "neutral",
  error: "attn",
  disconnected: "neutral",
};

const STATUS_LABEL: Record<Connector["status"], string> = {
  connected: "Connected",
  syncing: "Syncing",
  pending_auth: "Needs authorization",
  error: "Error",
  disconnected: "Disconnected",
};

export function ConnectorCard({ connector, onTest, onSync, onDelete, onAuthorize, onConfigure }: ConnectorCardProps) {
  const meta = CONNECTOR_META[connector.type];
  const Icon = meta.icon;
  const [busy, setBusy] = useState(false);
  const push = useToastStore((state) => state.push);

  const handleTest = async () => {
    setBusy(true);
    try {
      const result = await onTest(connector.id);
      push(result.connected ? "Connection test passed" : `Connection test failed: ${result.detail ?? "unknown error"}`, result.connected ? "live" : "attn");
    } finally {
      setBusy(false);
    }
  };

  const handleSync = async () => {
    setBusy(true);
    try {
      await onSync(connector.id);
      push("Sync queued", "live");
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Remove ${connector.name}? This deletes its indexed content.`)) return;
    setBusy(true);
    try {
      await onDelete(connector.id);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card interactive className="group flex flex-col gap-4 p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-sm bg-surface-sunken transition-colors duration-200 group-hover:bg-route-soft">
            <Icon className="h-4.5 w-4.5 text-ink transition-transform duration-200 group-hover:scale-110" strokeWidth={1.6} />
          </div>
          <div>
            <p className="text-sm font-medium text-ink">{connector.name}</p>
            <p className="text-xs text-ink-faint">{meta.label}</p>
          </div>
        </div>
        <Badge tone={STATUS_TONE[connector.status]} dot pulse={connector.status === "syncing"}>
          {STATUS_LABEL[connector.status]}
        </Badge>
      </div>

      <p className="font-mono text-xs text-ink-faint">
        {connector.last_synced_at ? `Last synced ${formatRelativeTime(connector.last_synced_at)}` : "Never synced"}
      </p>

      <div className="flex items-center gap-1 border-t border-line pt-3">
        {connector.status === "pending_auth" ? (
          <button
            type="button"
            disabled={busy}
            onClick={() => onAuthorize(connector.id)}
            className="flex items-center gap-1.5 rounded-sm px-2 py-1 text-xs text-route hover:bg-route-soft"
          >
            <Zap className="h-3.5 w-3.5" strokeWidth={1.75} />
            Authorize
          </button>
        ) : (
          <>
            <button type="button" disabled={busy} onClick={handleTest} className="flex items-center gap-1.5 rounded-sm px-2 py-1 text-xs text-ink-muted hover:bg-surface-sunken hover:text-ink">
              <Zap className="h-3.5 w-3.5" strokeWidth={1.75} />
              Test
            </button>
            <button type="button" disabled={busy} onClick={handleSync} className="flex items-center gap-1.5 rounded-sm px-2 py-1 text-xs text-ink-muted hover:bg-surface-sunken hover:text-ink">
              <RefreshCw className="h-3.5 w-3.5" strokeWidth={1.75} />
              Sync
            </button>
          </>
        )}
        <button type="button" onClick={() => onConfigure(connector)} className="flex items-center gap-1.5 rounded-sm px-2 py-1 text-xs text-ink-muted hover:bg-surface-sunken hover:text-ink">
          <Settings2 className="h-3.5 w-3.5" strokeWidth={1.75} />
          Configure
        </button>
        <button type="button" disabled={busy} onClick={handleDelete} className="ml-auto flex items-center gap-1.5 rounded-sm px-2 py-1 text-xs text-ink-faint hover:bg-attn-soft hover:text-attn">
          <Trash2 className="h-3.5 w-3.5" strokeWidth={1.75} />
        </button>
      </div>
    </Card>
  );
}
