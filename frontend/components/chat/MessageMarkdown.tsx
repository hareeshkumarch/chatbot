"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import type { Citation } from "@/lib/types";
import { cn } from "@/lib/utils";

function citationHref(index: number): string {
  return `#citation-${index}`;
}

function linkifyCitations(text: string): string {
  return text.replace(/\[(\d+)\]/g, (_match, index: string) => `[${index}](${citationHref(Number(index))})`);
}

const markdownComponents: Components = {
  h3: ({ children }) => <h3 className="mt-3 mb-1.5 font-display text-sm font-medium text-ink first:mt-0">{children}</h3>,
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>,
  ol: ({ children }) => <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>,
  li: ({ children }) => <li className="text-ink-muted">{children}</li>,
  strong: ({ children }) => <strong className="font-medium text-ink">{children}</strong>,
  code: ({ children }) => (
    <code className="rounded-sm bg-surface-sunken px-1 py-0.5 font-mono text-[12px] text-route">{children}</code>
  ),
  pre: ({ children }) => (
    <pre className="mb-2 overflow-x-auto rounded-md border border-line bg-surface-sunken p-3 font-mono text-[12px] last:mb-0">{children}</pre>
  ),
  table: ({ children }) => (
    <div className="mb-2 overflow-x-auto rounded-md border border-line last:mb-0">
      <table className="w-full min-w-[280px] border-collapse text-left text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="border-b border-line bg-surface-sunken">{children}</thead>,
  th: ({ children }) => <th className="px-3 py-2 font-medium text-ink">{children}</th>,
  td: ({ children }) => <td className="border-t border-line px-3 py-2 text-ink-muted">{children}</td>,
  a: ({ href, children }) => {
    if (href?.startsWith("#citation-")) {
      const index = href.replace("#citation-", "");
      return (
        <a href={href} className="font-mono text-[11px] text-route hover:underline">
          [{index}]
        </a>
      );
    }
    return (
      <a href={href} target="_blank" rel="noreferrer" className="text-route hover:underline">
        {children}
      </a>
    );
  },
};

export function MessageMarkdown({ content, className }: { content: string; className?: string }) {
  return (
    <div className={cn("prose-chat text-sm leading-relaxed text-ink", className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {linkifyCitations(content)}
      </ReactMarkdown>
    </div>
  );
}

export function scrollToCitation(citations: Citation[], index: number) {
  const element = document.getElementById(`citation-${index}`);
  element?.scrollIntoView({ behavior: "smooth", block: "nearest" });
}
