"use client";

import { useState, type KeyboardEvent } from "react";
import { ArrowUp, Square } from "lucide-react";
import { Textarea } from "@/components/ui/Input";
import { ModelSelector } from "@/components/chat/ModelSelector";
import { ConnectorScope } from "@/components/chat/ConnectorScope";
import { ReportGenerateButton } from "@/components/chat/ReportGenerateButton";
import { useChatStore } from "@/store/chatStore";

interface MessageInputProps {
  onSend: (text: string) => void;
  onStop: () => void;
  isStreaming: boolean;
}

export function MessageInput({ onSend, onStop, isStreaming }: MessageInputProps) {
  const [value, setValue] = useState("");
  const provider = useChatStore((state) => state.provider);
  const model = useChatStore((state) => state.model);
  const selectedConnectorIds = useChatStore((state) => state.selectedConnectorIds);
  const setSelectedConnectorIds = useChatStore((state) => state.setSelectedConnectorIds);

  const submit = () => {
    if (!value.trim() || isStreaming) return;
    onSend(value);
    setValue("");
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <div className="border-t border-line bg-canvas px-4 py-4 md:px-8">
      <div className="mx-auto max-w-3xl">
        <div className="rounded-md border border-line bg-surface focus-within:border-route">
          <Textarea
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your documents, data, or connected tools"
            rows={2}
            className="border-0 focus:ring-0"
          />
          <div className="flex items-center justify-between border-t border-line px-3 py-2">
            <div className="flex items-center gap-2">
              <ConnectorScope selectedIds={selectedConnectorIds} onChange={setSelectedConnectorIds} />
              <ModelSelector />
              <ReportGenerateButton query={value} connectorIds={selectedConnectorIds} provider={provider} model={model} />
            </div>
            {isStreaming ? (
              <button
                type="button"
                onClick={onStop}
                className="flex h-8 w-8 items-center justify-center rounded-full bg-ink text-canvas hover:bg-ink/80"
                aria-label="Stop generating"
              >
                <Square className="h-3 w-3" fill="currentColor" />
              </button>
            ) : (
              <button
                type="button"
                onClick={submit}
                disabled={!value.trim()}
                className="flex h-8 w-8 items-center justify-center rounded-full bg-route text-white transition-all duration-150 hover:bg-route/90 hover:scale-105 active:scale-95 disabled:scale-100 disabled:bg-line-strong"
                aria-label="Send message"
              >
                <ArrowUp className="h-4 w-4" strokeWidth={2} />
              </button>
            )}
          </div>
        </div>
        <p className="mt-2 text-center font-mono text-[10px] text-ink-faint">Enter to send · Shift + Enter for a new line</p>
      </div>
    </div>
  );
}
