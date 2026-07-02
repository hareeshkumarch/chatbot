"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="animate-fade-in flex flex-col items-center justify-center gap-4 rounded-md border border-line bg-surface px-6 py-14 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-attn-soft">
        <AlertTriangle className="h-5 w-5 text-attn" strokeWidth={1.75} />
      </span>
      <div className="max-w-sm">
        <p className="text-sm font-medium text-ink">Something went wrong</p>
        <p className="mt-1 text-sm text-ink-muted">{message ?? "We couldn't load this right now."}</p>
      </div>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          <RefreshCw className="h-3.5 w-3.5" strokeWidth={1.75} />
          Try again
        </Button>
      )}
    </div>
  );
}
