"use client";

import { useState } from "react";
import { FileDown, Loader2 } from "lucide-react";
import type { ReportFormat } from "@/lib/types";
import { generateReport } from "@/lib/api";
import { useToastStore } from "@/store/toastStore";

const FORMATS: { value: ReportFormat; label: string }[] = [
  { value: "pdf", label: "PDF" },
  { value: "docx", label: "Word" },
  { value: "html", label: "HTML" },
];

interface ReportGenerateButtonProps {
  query: string;
  connectorIds: string[] | null;
  provider: string | null;
  model: string | null;
}

export function ReportGenerateButton({ query, connectorIds, provider, model }: ReportGenerateButtonProps) {
  const [open, setOpen] = useState(false);
  const [pendingFormat, setPendingFormat] = useState<ReportFormat | null>(null);
  const pushToast = useToastStore((state) => state.push);

  const handleGenerate = async (format: ReportFormat) => {
    if (!query.trim()) {
      pushToast("Type a topic in the message box first", "attn");
      return;
    }
    setPendingFormat(format);
    try {
      await generateReport(query, format, connectorIds, provider, model);
      setOpen(false);
    } catch (error) {
      pushToast(error instanceof Error ? error.message : "report generation failed", "attn");
    } finally {
      setPendingFormat(null);
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex h-7 items-center gap-1.5 rounded-sm px-2 font-mono text-[11px] uppercase tracking-wide text-ink-muted hover:bg-surface-sunken hover:text-ink"
        aria-label="Generate report"
      >
        <FileDown className="h-3.5 w-3.5" strokeWidth={1.75} />
        Report
      </button>

      {open && (
        <div className="absolute bottom-full left-0 z-30 mb-2 w-48 rounded-md border border-line bg-surface p-1.5 shadow-lg">
          <p className="px-2 py-1 font-mono text-[10px] uppercase tracking-wide text-ink-faint">Generate report as</p>
          {FORMATS.map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => handleGenerate(f.value)}
              disabled={pendingFormat !== null}
              className="flex w-full items-center justify-between rounded-sm px-2 py-1.5 text-left text-sm text-ink hover:bg-route-soft hover:text-route disabled:opacity-50"
            >
              {f.label}
              {pendingFormat === f.value && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
