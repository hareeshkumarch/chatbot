import { FileText } from "lucide-react";
import type { Citation } from "@/lib/types";
import { truncate } from "@/lib/utils";

export function CitationList({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return null;

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {citations.map((citation) => (
        <span
          key={citation.index}
          id={`citation-${citation.index}`}
          className="inline-flex items-center gap-1.5 rounded-sm border border-line bg-surface-sunken px-2 py-1 font-mono text-xs text-ink-muted"
          title={citation.source_uri ?? undefined}
        >
          <FileText className="h-3 w-3" strokeWidth={1.75} />
          [{citation.index}] {truncate(citation.title ?? citation.source_uri ?? "source", 28)}
          {citation.page_number ? ` · p.${citation.page_number}` : ""}
        </span>
      ))}
    </div>
  );
}
