import { Plus } from "lucide-react";
import type { Connector } from "@/lib/types";
import { ConnectorCard } from "@/components/connectors/ConnectorCard";
import { StaggerItem } from "@/components/ui/StaggerItem";

interface ConnectorGridProps {
  connectors: Connector[];
  onTest: (id: string) => Promise<{ connected: boolean; detail: string | null }>;
  onSync: (id: string) => Promise<{ queued: boolean }>;
  onDelete: (id: string) => Promise<void>;
  onAuthorize: (id: string) => Promise<void>;
  onConfigure: (connector: Connector) => void;
  onAddNew: () => void;
}

export function ConnectorGrid({ connectors, onTest, onSync, onDelete, onAuthorize, onConfigure, onAddNew }: ConnectorGridProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {connectors.map((connector, i) => (
        <StaggerItem key={connector.id} index={i}>
          <ConnectorCard
            connector={connector}
            onTest={onTest}
            onSync={onSync}
            onDelete={onDelete}
            onAuthorize={onAuthorize}
            onConfigure={onConfigure}
          />
        </StaggerItem>
      ))}
      <StaggerItem index={connectors.length}>
        <button
          type="button"
          onClick={onAddNew}
          className="flex min-h-[148px] w-full flex-col items-center justify-center gap-2 rounded-md border border-dashed border-line-strong text-ink-faint transition-all duration-200 hover:-translate-y-0.5 hover:border-route hover:bg-route-soft/30 hover:text-route active:translate-y-0"
        >
          <Plus className="h-5 w-5 transition-transform duration-200 group-hover:rotate-90" strokeWidth={1.75} />
          <span className="text-sm">Connect a source</span>
        </button>
      </StaggerItem>
    </div>
  );
}
