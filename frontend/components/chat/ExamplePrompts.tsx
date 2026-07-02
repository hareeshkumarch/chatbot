"use client";

import { FileText, TrendingUp, Newspaper, LineChart } from "lucide-react";

interface ExamplePrompt {
  label: string;
  prompt: string;
  icon: typeof FileText;
}

const EXAMPLES: ExamplePrompt[] = [
  { label: "Ask your documents", prompt: "Summarize the key points from my uploaded documents", icon: FileText },
  { label: "Check a stock", prompt: "What's Apple's stock price and market cap right now?", icon: LineChart },
  { label: "Catch up on news", prompt: "What's the latest news on the semiconductor industry?", icon: Newspaper },
  { label: "See what's trending", prompt: "How has interest in electric vehicles trended this year?", icon: TrendingUp },
];

export function ExamplePrompts({ onSelect }: { onSelect: (prompt: string) => void }) {
  return (
    <div className="grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
      {EXAMPLES.map((example, i) => {
        const Icon = example.icon;
        return (
          <button
            key={example.label}
            type="button"
            onClick={() => onSelect(example.prompt)}
            style={{ animationDelay: `${i * 70}ms` }}
            className="group animate-rise-in flex flex-col items-start gap-2 rounded-md border border-line bg-surface p-3 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-route hover:bg-route-soft hover:shadow-[0_6px_18px_-10px_rgba(47,62,224,0.4)] active:translate-y-0"
          >
            <Icon className="h-4 w-4 text-route transition-transform duration-200 group-hover:scale-110" strokeWidth={1.75} />
            <span className="text-xs font-medium text-ink">{example.label}</span>
            <span className="text-xs text-ink-faint">{example.prompt}</span>
          </button>
        );
      })}
    </div>
  );
}
