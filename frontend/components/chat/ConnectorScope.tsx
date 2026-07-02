"use client";

import { useEffect, useRef, useState } from "react";
import { Plug } from "lucide-react";
import { useConnectors } from "@/hooks/useConnectors";
import { CONNECTOR_META } from "@/lib/constants/connectors";
import { cn } from "@/lib/utils";

interface ConnectorScopeProps {
  selectedIds: string[] | null;
  onChange: (ids: string[] | null) => void;
}

export function ConnectorScope({ selectedIds, onChange }: ConnectorScopeProps) {
  const { connectors } = useConnectors();
  const connected = connectors.filter((c) => c.status === "connected");
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const label = selectedIds === null ? "All connectors" : selectedIds.length === 0 ? "No connectors" : `${selectedIds.length} connector${selectedIds.length === 1 ? "" : "s"}`;

  const toggle = (id: string) => {
    const current = selectedIds ?? connected.map((c) => c.id);
    if (current.includes(id)) {
      onChange(current.filter((existing) => existing !== id));
    } else {
      onChange([...current, id]);
    }
  };

  if (connected.length === 0) return null;

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex h-9 items-center gap-2 rounded-sm border border-line px-3 text-xs text-ink-muted hover:border-line-strong"
      >
        <Plug className="h-3.5 w-3.5" strokeWidth={1.75} />
        {label}
      </button>
      {open && (
        <div className="animate-slide-fade-in absolute bottom-full z-20 mb-1 w-56 rounded-sm border border-line bg-surface p-2 shadow-md">
          <button
            type="button"
            onClick={() => onChange(null)}
            className={cn("mb-1 flex w-full items-center rounded-sm px-2 py-1.5 text-left text-xs", selectedIds === null ? "text-route" : "text-ink-muted hover:bg-surface-sunken")}
          >
            All connectors
          </button>
          <div className="my-1 border-t border-line" />
          {connected.map((connector) => {
            const Icon = CONNECTOR_META[connector.type].icon;
            const isChecked = selectedIds === null || selectedIds.includes(connector.id);
            return (
              <button
                key={connector.id}
                type="button"
                onClick={() => toggle(connector.id)}
                className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-xs text-ink hover:bg-surface-sunken"
              >
                <span className={cn("flex h-3.5 w-3.5 items-center justify-center rounded-[3px] border", isChecked ? "border-route bg-route" : "border-line-strong")}>
                  {isChecked && <span className="h-1.5 w-1.5 rounded-[1px] bg-white" />}
                </span>
                <Icon className="h-3.5 w-3.5 text-ink-muted" />
                <span className="truncate">{connector.name}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
