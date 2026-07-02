"use client";

import { useEffect, useRef, useState } from "react";
import { AlertTriangle, Plus } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { MessageInput } from "@/components/chat/MessageInput";
import { useChat } from "@/hooks/useChat";

export default function ChatPage() {
  const { conversationId, messages, isStreaming, streamError, isLoadingHistory, openConversation, startNewConversation, sendMessage, stopStreaming } = useChat();
  const [, setRefreshKey] = useState(0);
  const hydratedRef = useRef(false);

  useEffect(() => {
    if (hydratedRef.current) return;
    hydratedRef.current = true;
    if (conversationId && messages.length === 0) {
      void openConversation(conversationId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSend = async (text: string) => {
    await sendMessage(text);
    setRefreshKey((key) => key + 1);
  };

  return (
    <div className="flex h-full flex-1 flex-col">
      <Topbar
        title="Chat"
        description="Ask questions across your documents, data, and connected tools"
        actions={
          <button
            type="button"
            onClick={startNewConversation}
            className="group flex items-center gap-1.5 rounded-md border border-line bg-surface px-3 py-1.5 text-sm font-medium text-ink-muted transition-all hover:border-route hover:text-route"
          >
            <Plus className="h-3.5 w-3.5 transition-transform duration-200 group-hover:rotate-90" strokeWidth={1.75} />
            New conversation
          </button>
        }
      />
      <div className="flex flex-1 flex-col overflow-hidden">
        {streamError && (
          <div className="flex items-center gap-2 border-b border-attn/30 bg-attn-soft px-4 py-2 text-xs text-attn md:px-8">
            <AlertTriangle className="h-3.5 w-3.5 shrink-0" strokeWidth={1.75} />
            {streamError}
          </div>
        )}
        <ChatWindow messages={messages} isLoadingHistory={isLoadingHistory} onExampleSelect={handleSend} />
        <MessageInput onSend={handleSend} onStop={stopStreaming} isStreaming={isStreaming} />
      </div>
    </div>
  );
}
