import { FileText, FileCode, File } from "lucide-react";
import { Reveal } from "@/components/landing/Reveal";
import { LANDING_SHELL } from "@/lib/constants/landing";

const FORMATS = [
  { icon: File, label: "PDF", description: "Typeset with reportlab, tables and charts embedded, ready to send." },
  { icon: FileText, label: "Word", description: "A real .docx with native headings, tables, and images — editable." },
  { icon: FileCode, label: "HTML", description: "A standalone page styled to match, chart and all, no dependencies." },
];

export function ReportsSection() {
  return (
    <section id="reports" className="scroll-mt-16 border-b border-line bg-surface-sunken py-14 md:py-16">
      <div className={LANDING_SHELL}>
        <Reveal>
          <p className="font-mono text-xs uppercase tracking-wide text-route">Reports</p>
          <h2 className="mt-3 font-display text-3xl tracking-tight text-ink md:text-4xl">
            Turn a question into a document, not just an answer.
          </h2>
          <p className="mt-4 max-w-3xl text-base leading-relaxed text-ink-muted">
            The same planner that answers a chat question can structure a full report from it — sections, tables from
            your data, and charts generated from whatever numbers came back. One click, three formats.
          </p>
        </Reveal>
        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-3">
          {FORMATS.map((format, index) => {
            const Icon = format.icon;
            return (
              <Reveal key={format.label} delay={index * 80}>
                <div className="group rounded-md border border-line bg-surface p-6 transition-all duration-200 hover:-translate-y-1 hover:border-route hover:shadow-sm">
                  <Icon className="h-6 w-6 text-route" strokeWidth={1.75} />
                  <p className="mt-4 font-display text-lg text-ink">{format.label}</p>
                  <p className="mt-2 text-sm leading-relaxed text-ink-muted">{format.description}</p>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
