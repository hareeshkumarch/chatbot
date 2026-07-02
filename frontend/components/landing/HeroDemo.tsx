"use client";

import { useEffect, useReducer } from "react";
import { Check, Loader2, Sparkles } from "lucide-react";

interface Source {
  label: string;
  detail: string;
}

interface Scenario {
  question: string;
  sources: Source[];
  answer: { text: string; cite?: number }[];
  meta: { steps: number; tokens: string; cost: string };
}

const SCENARIOS: Scenario[] = [
  {
    question: "What's Tesla trading at, and any news moving it?",
    sources: [
      { label: "Market data", detail: "Yahoo Finance" },
      { label: "News", detail: "Serper" },
    ],
    answer: [
      { text: "TSLA is at " },
      { text: "$245.30, up 2.1%", cite: 0 },
      { text: " today. The move tracks coverage of the new Gigafactory expansion" },
      { text: " announced this week", cite: 1 },
      { text: "." },
    ],
    meta: { steps: 2, tokens: "1,146", cost: "$0.005" },
  },
  {
    question: "Summarize the Q2 board deck and pull revenue by region.",
    sources: [
      { label: "Documents", detail: "Q2 board deck" },
      { label: "Database", detail: "read-only SQL" },
    ],
    answer: [
      { text: "Q2 revenue was " },
      { text: "$4.2M, up 18% QoQ", cite: 0 },
      { text: ", led by enterprise. By region: " },
      { text: "NA 58%, EMEA 27%, APAC 15%", cite: 1 },
      { text: "." },
    ],
    meta: { steps: 2, tokens: "2,038", cost: "$0.011" },
  },
  {
    question: "How has interest in electric vehicles trended this year?",
    sources: [
      { label: "Trends", detail: "Google Trends" },
      { label: "Web", detail: "Exa" },
    ],
    answer: [
      { text: "Search interest is " },
      { text: "up 34% since January", cite: 0 },
      { text: ", with a spike in March around " },
      { text: "new tax-credit rules", cite: 1 },
      { text: "." },
    ],
    meta: { steps: 2, tokens: "1,472", cost: "$0.007" },
  },
];

type Stage = "typing" | "planning" | "running" | "answering" | "done";

interface State {
  scenario: number;
  stage: Stage;
  typed: number;
  sourcesRevealed: number;
  sourcesRan: number;
  answered: number;
}

type Action =
  | { type: "tick_type" }
  | { type: "start_planning" }
  | { type: "reveal_source" }
  | { type: "start_running" }
  | { type: "run_source" }
  | { type: "start_answering" }
  | { type: "tick_answer" }
  | { type: "finish" }
  | { type: "next" };

function answerLength(scenario: number): number {
  return SCENARIOS[scenario]!.answer.reduce((sum, seg) => sum + seg.text.length, 0);
}

function reducer(state: State, action: Action): State {
  const sc = SCENARIOS[state.scenario]!;
  switch (action.type) {
    case "tick_type":
      return { ...state, typed: Math.min(state.typed + 1, sc.question.length) };
    case "start_planning":
      return { ...state, stage: "planning" };
    case "reveal_source":
      return { ...state, sourcesRevealed: Math.min(state.sourcesRevealed + 1, sc.sources.length) };
    case "start_running":
      return { ...state, stage: "running" };
    case "run_source":
      return { ...state, sourcesRan: Math.min(state.sourcesRan + 1, sc.sources.length) };
    case "start_answering":
      return { ...state, stage: "answering" };
    case "tick_answer":
      return { ...state, answered: Math.min(state.answered + 1, answerLength(state.scenario)) };
    case "finish":
      return { ...state, stage: "done" };
    case "next": {
      const next = (state.scenario + 1) % SCENARIOS.length;
      return { scenario: next, stage: "typing", typed: 0, sourcesRevealed: 0, sourcesRan: 0, answered: 0 };
    }
    default:
      return state;
  }
}

const INITIAL: State = { scenario: 0, stage: "typing", typed: 0, sourcesRevealed: 0, sourcesRan: 0, answered: 0 };

export function HeroDemo() {
  const [state, dispatch] = useReducer(reducer, INITIAL);
  const sc = SCENARIOS[state.scenario]!;

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    const push = (fn: () => void, ms: number) => timers.push(setTimeout(fn, ms));

    if (state.stage === "typing") {
      if (state.typed < sc.question.length) {
        push(() => dispatch({ type: "tick_type" }), 34);
      } else {
        push(() => dispatch({ type: "start_planning" }), 500);
      }
    } else if (state.stage === "planning") {
      if (state.sourcesRevealed < sc.sources.length) {
        push(() => dispatch({ type: "reveal_source" }), 320);
      } else {
        push(() => dispatch({ type: "start_running" }), 450);
      }
    } else if (state.stage === "running") {
      if (state.sourcesRan < sc.sources.length) {
        push(() => dispatch({ type: "run_source" }), 620);
      } else {
        push(() => dispatch({ type: "start_answering" }), 400);
      }
    } else if (state.stage === "answering") {
      if (state.answered < answerLength(state.scenario)) {
        push(() => dispatch({ type: "tick_answer" }), 16);
      } else {
        push(() => dispatch({ type: "finish" }), 100);
      }
    } else if (state.stage === "done") {
      push(() => dispatch({ type: "next" }), 3200);
    }

    return () => timers.forEach(clearTimeout);
  }, [state, sc.question.length, sc.sources.length]);

  const answerText = renderAnswer(sc, state.answered);

  return (
    <div className="relative w-full">
      <div className="absolute -inset-3 -z-10 rounded-2xl bg-gradient-to-br from-route/8 via-transparent to-live/8 blur-2xl" />
      <div className="overflow-hidden rounded-xl border border-line bg-surface shadow-[0_1px_2px_rgba(20,24,26,0.04),0_12px_32px_-8px_rgba(20,24,26,0.12)]">
        <div className="flex items-center gap-2 border-b border-line px-4 py-3">
          <div className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-attn/50" />
            <span className="h-2.5 w-2.5 rounded-full bg-ink-faint/30" />
            <span className="h-2.5 w-2.5 rounded-full bg-live/50" />
          </div>
          <span className="ml-1 font-mono text-[11px] text-ink-faint">enterprise-ai / chat</span>
          <span className="ml-auto flex items-center gap-1 rounded-full bg-live-soft px-2 py-0.5 font-mono text-[10px] text-live">
            <span className="h-1.5 w-1.5 rounded-full bg-live" />
            routed
          </span>
        </div>

        <div className="p-4">
          <div className="rounded-lg bg-surface-sunken px-3.5 py-3">
            <p className="text-sm leading-relaxed text-ink">
              {sc.question.slice(0, state.typed)}
              {state.stage === "typing" && <Caret color="route" />}
            </p>
          </div>

          <div
            className="grid transition-[grid-template-rows,opacity] duration-500 ease-out"
            style={{ gridTemplateRows: state.stage === "typing" ? "0fr" : "1fr", opacity: state.stage === "typing" ? 0 : 1 }}
          >
            <div className="overflow-hidden">
              <div className="mt-3.5 flex items-center gap-2">
                <span className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wide text-ink-faint">
                  {state.stage === "planning" ? (
                    <Loader2 className="h-3 w-3 animate-spin text-route" />
                  ) : (
                    <Sparkles className="h-3 w-3 text-route" />
                  )}
                  Plan
                </span>
                <div className="h-px flex-1 bg-line" />
              </div>

              <div className="mt-2.5 flex flex-col gap-1.5">
                {sc.sources.map((source, i) => {
                  const revealed = i < state.sourcesRevealed;
                  const ran = i < state.sourcesRan;
                  const activeRunning = state.stage === "running" && i === state.sourcesRan;
                  return (
                    <div
                      key={source.label}
                      className="flex items-center gap-2.5 rounded-md border border-line bg-canvas px-3 py-2 transition-all duration-400 ease-out"
                      style={{
                        opacity: revealed ? 1 : 0,
                        transform: revealed ? "translateY(0)" : "translateY(6px)",
                      }}
                    >
                      <StatusDot ran={ran} running={activeRunning} />
                      <span className="text-xs font-medium text-ink">{source.label}</span>
                      <span className="font-mono text-[11px] text-ink-faint">{source.detail}</span>
                      {ran && <span className="ml-auto font-mono text-[10px] text-live">done</span>}
                      {activeRunning && <span className="ml-auto font-mono text-[10px] text-route">running…</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div
            className="grid transition-[grid-template-rows,opacity] duration-500 ease-out"
            style={{
              gridTemplateRows: state.stage === "answering" || state.stage === "done" ? "1fr" : "0fr",
              opacity: state.stage === "answering" || state.stage === "done" ? 1 : 0,
            }}
          >
            <div className="overflow-hidden">
              <div className="mt-3.5 flex gap-2.5 border-t border-line pt-3.5">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-route/10">
                  <Sparkles className="h-3 w-3 text-route" />
                </span>
                <p className="text-sm leading-relaxed text-ink-muted">
                  {answerText}
                  {state.stage === "answering" && <Caret color="live" />}
                </p>
              </div>

              <div
                className="mt-3.5 flex items-center justify-between border-t border-line pt-3 font-mono text-[11px] text-ink-faint transition-opacity duration-500"
                style={{ opacity: state.stage === "done" ? 1 : 0 }}
              >
                <span>
                  {sc.meta.steps} agents · {sc.meta.tokens} tokens
                </span>
                <span className="flex items-center gap-1 text-live">
                  <Check className="h-3 w-3" strokeWidth={2.5} />
                  verified · {sc.meta.cost}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function renderAnswer(sc: Scenario, count: number) {
  const out: React.ReactNode[] = [];
  let remaining = count;
  sc.answer.forEach((seg, i) => {
    if (remaining <= 0) return;
    const shown = seg.text.slice(0, remaining);
    remaining -= seg.text.length;
    if (seg.cite !== undefined) {
      out.push(
        <span key={i} className="text-ink">
          {shown}
          {remaining <= 0 ? "" : <sup className="ml-0.5 font-mono text-[9px] text-route">[{seg.cite + 1}]</sup>}
        </span>,
      );
    } else {
      out.push(<span key={i}>{shown}</span>);
    }
  });
  return out;
}

function Caret({ color }: { color: "route" | "live" }) {
  return <span className={`ml-0.5 inline-block h-3.5 w-[2px] translate-y-0.5 ${color === "route" ? "bg-route" : "bg-live"} animate-caret`} />;
}

function StatusDot({ ran, running }: { ran: boolean; running: boolean }) {
  if (ran) {
    return (
      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-live">
        <Check className="h-2.5 w-2.5 text-surface" strokeWidth={3} />
      </span>
    );
  }
  if (running) {
    return <Loader2 className="h-4 w-4 animate-spin text-route" />;
  }
  return <span className="h-4 w-4 rounded-full border-2 border-line" />;
}
