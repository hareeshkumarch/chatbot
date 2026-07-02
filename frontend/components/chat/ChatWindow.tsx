"use client";

import { useEffect, useRef } from "react";
import type { DisplayMessage } from "@/store/chatStore";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ExamplePrompts } from "@/components/chat/ExamplePrompts";
import { LogoMark } from "@/components/icons/Logo";

interface ChatWindowProps {
  messages: DisplayMessage[];
  isLoadingHistory: boolean;
  onExampleSelect: (prompt: string) => void;
}

export function ChatWindow({ messages, isLoadingHistory, onExampleSelect }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  if (isLoadingHistory) {
    return <div className="flex-1" />;
  }

  if (messages.length === 0) {
    return (
      <div className="animate-fade-in flex flex-1 flex-col items-center justify-center gap-6 px-4 text-center">
        <div className="flex flex-col items-center gap-3">
          <span className="relative flex h-14 w-14 items-center justify-center">
            <span className="absolute inline-flex h-full w-full animate-pulse-soft rounded-full bg-route-soft" />
            <LogoMark className="relative h-10 w-10" spin />
          </span>
          <p className="max-w-sm text-sm text-ink-muted">
            Ask about your documents, your connected data sources, or the live web. Everything routes through the source that fits the question.
          </p>
        </div>
        <ExamplePrompts onSelect={onExampleSelect} />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
      <div className="mx-auto flex max-w-3xl flex-col gap-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
