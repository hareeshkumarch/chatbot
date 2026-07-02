"use client";

import { FileText, Trash2, AlertCircle } from "lucide-react";
import type { DocumentRecord } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { formatBytes, formatRelativeTime } from "@/lib/utils";

const STATUS_TONE: Record<DocumentRecord["status"], "live" | "attn" | "route" | "neutral"> = {
  indexed: "live",
  processing: "route",
  pending: "neutral",
  failed: "attn",
};

const STATUS_LABEL: Record<DocumentRecord["status"], string> = {
  indexed: "Indexed",
  processing: "Processing",
  pending: "Queued",
  failed: "Failed",
};

interface DocumentListProps {
  documents: DocumentRecord[];
  onDelete: (id: string) => void;
}

export function DocumentList({ documents, onDelete }: DocumentListProps) {
  if (documents.length === 0) {
    return <p className="py-10 text-center text-sm text-ink-faint">No documents yet. Upload a file to start building your knowledge base.</p>;
  }

  return (
    <div className="flex flex-col divide-y divide-line rounded-md border border-line bg-surface">
      {documents.map((doc, i) => (
        <div
          key={doc.id}
          style={{ animationDelay: `${i * 50}ms` }}
          className="animate-rise-in group flex items-center justify-between gap-4 px-4 py-3 transition-colors duration-200 hover:bg-surface-sunken/50"
        >
          <div className="flex min-w-0 items-center gap-3">
            <FileText className="h-4 w-4 shrink-0 text-ink-faint transition-colors group-hover:text-route" strokeWidth={1.6} />
            <div className="min-w-0">
              <p className="truncate text-sm text-ink">{doc.title}</p>
              <p className="font-mono text-xs text-ink-faint">
                {formatBytes(doc.size_bytes)} · {doc.chunk_count} chunks · {formatRelativeTime(doc.created_at)}
              </p>
              {doc.status === "failed" && doc.error_message && (
                <p className="mt-1 flex items-center gap-1 text-xs text-attn">
                  <AlertCircle className="h-3 w-3" strokeWidth={1.75} />
                  {doc.error_message}
                </p>
              )}
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <Badge tone={STATUS_TONE[doc.status]} dot pulse={doc.status === "processing"}>
              {STATUS_LABEL[doc.status]}
            </Badge>
            <button type="button" onClick={() => onDelete(doc.id)} aria-label="Delete document" className="text-ink-faint hover:text-attn">
              <Trash2 className="h-4 w-4" strokeWidth={1.75} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
