import { AlertTriangle, CheckCircle2, User } from "lucide-react";
import type { DisplayMessage } from "@/store/chatStore";
import { CitationList } from "@/components/chat/CitationList";
import { MessageBlocks } from "@/components/chat/MessageBlocks";
import { MessageMarkdown } from "@/components/chat/MessageMarkdown";
import { TraceDetails } from "@/components/chat/TraceDetails";
import { LogoMark } from "@/components/icons/Logo";
import { providerLabel, providerIcon } from "@/lib/constants/models";
import { cn } from "@/lib/utils";

export function MessageBubble({ message }: { message: DisplayMessage }) {
  const isUser = message.role === "user";
  const ProviderIcon = message.providerUsed ? providerIcon(message.providerUsed) : null;
  const hasContent = message.content.trim().length > 0;
  const showEmptyAssistant = !isUser && !message.isStreaming && !hasContent && message.blocks.length === 0;

  return (
    <div className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      <div className="flex shrink-0 pt-0.5">
        {isUser ? (
          <span className="flex h-8 w-8 items-center justify-center rounded-full border border-line bg-surface-sunken">
            <User className="h-4 w-4 text-ink-muted" strokeWidth={1.75} />
          </span>
        ) : (
          <span className="flex h-8 w-8 items-center justify-center">
            <LogoMark className="h-8 w-8" spin={message.isStreaming} animated={!message.isStreaming} />
          </span>
        )}
      </div>

      <div className={cn("flex min-w-0 max-w-[85%] flex-col gap-1.5", isUser ? "items-end" : "items-start")}>
        {!isUser && !message.isStreaming && message.providerUsed && (
          <span className="flex items-center gap-1.5 px-0.5 font-mono text-[11px] text-ink-faint">
            {ProviderIcon && <ProviderIcon className="h-3 w-3" />}
            {providerLabel(message.providerUsed)}
            {message.modelUsed ? ` · ${message.modelUsed}` : ""}
            {message.confidence != null && ` · ${Math.round(message.confidence * 100)}% match`}
          </span>
        )}

        {!isUser && message.isStreaming && (
          <span className="flex items-center gap-1.5 px-0.5 font-mono text-[11px] text-route">
            <span className="h-1.5 w-1.5 animate-signal-pulse rounded-full bg-route" />
            Generating
          </span>
        )}

        <div
          className={cn(
            "w-full rounded-lg px-3.5 py-2.5 text-sm leading-relaxed",
            isUser
              ? "bg-ink text-canvas"
              : "border border-line bg-surface text-ink shadow-[0_1px_2px_rgba(20,24,26,0.04)]",
          )}
        >
          {hasContent ? (
            isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <MessageMarkdown content={message.content} />
            )
          ) : message.isStreaming ? (
            <p className="text-ink-faint">Thinking…</p>
          ) : showEmptyAssistant ? (
            <p className="text-ink-muted">No response was generated. Add API keys in Settings to enable model calls.</p>
          ) : null}
          {message.isStreaming && hasContent && (
            <span className="ml-0.5 inline-block h-3.5 w-[2px] translate-y-0.5 animate-caret bg-route" />
          )}
        </div>

        {!isUser && !message.isStreaming && message.blocks.length > 0 && <MessageBlocks blocks={message.blocks} />}

        {!isUser && message.verified === true && (
          <span className="flex items-center gap-1 px-0.5 text-xs text-live">
            <CheckCircle2 className="h-3 w-3" strokeWidth={1.75} />
            Verified against sources
          </span>
        )}

        {!isUser && message.verified === false && (
          <span className="flex items-center gap-1 px-0.5 text-xs text-attn">
            <AlertTriangle className="h-3 w-3" strokeWidth={1.75} />
            Unverified answer
          </span>
        )}

        {!isUser && hasContent && <CitationList citations={message.citations} />}
        {!isUser && !message.isStreaming && hasContent && <TraceDetails message={message} />}
      </div>
    </div>
  );
}
