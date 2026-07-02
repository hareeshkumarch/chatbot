"use client";

import { useCallback, useRef, useState } from "react";
import { useChatStore } from "@/store/chatStore";
import { getMessages, streamChat } from "@/lib/api";

export function useChat() {
  const conversationId = useChatStore((state) => state.conversationId);
  const messages = useChatStore((state) => state.messages);
  const isStreaming = useChatStore((state) => state.isStreaming);
  const streamError = useChatStore((state) => state.streamError);
  const selectedConnectorIds = useChatStore((state) => state.selectedConnectorIds);
  const provider = useChatStore((state) => state.provider);
  const model = useChatStore((state) => state.model);

  const setConversationId = useChatStore((state) => state.setConversationId);
  const loadMessages = useChatStore((state) => state.loadMessages);
  const resetConversation = useChatStore((state) => state.resetConversation);
  const addUserMessage = useChatStore((state) => state.addUserMessage);
  const beginAssistantMessage = useChatStore((state) => state.beginAssistantMessage);
  const appendAssistantDelta = useChatStore((state) => state.appendAssistantDelta);
  const replaceAssistantContent = useChatStore((state) => state.replaceAssistantContent);
  const finalizeAssistantMessage = useChatStore((state) => state.finalizeAssistantMessage);
  const setStreaming = useChatStore((state) => state.setStreaming);
  const setStreamError = useChatStore((state) => state.setStreamError);

  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const openConversation = useCallback(
    async (id: string) => {
      setIsLoadingHistory(true);
      try {
        const records = await getMessages(id);
        setConversationId(id);
        loadMessages(records);
      } finally {
        setIsLoadingHistory(false);
      }
    },
    [setConversationId, loadMessages],
  );

  const startNewConversation = useCallback(() => {
    resetConversation();
  }, [resetConversation]);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) return;

      setStreamError(null);
      addUserMessage(`local-user-${Date.now()}`, trimmed);
      beginAssistantMessage();
      setStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        await streamChat(
          {
            message: trimmed,
            conversation_id: conversationId,
            connector_ids: selectedConnectorIds,
            provider,
            model,
          },
          {
            onStart: (data) => {
              if (!conversationId) setConversationId(data.conversation_id);
            },
            onToken: (delta) => appendAssistantDelta(delta),
            onReplace: (content) => replaceAssistantContent(content),
            onStreamError: (message) => setStreamError(message),
            onDone: (data) => {
              setConversationId(data.conversation_id);
              finalizeAssistantMessage({
                id: data.message_id,
                citations: data.citations,
                blocks: data.blocks ?? [],
                providerUsed: data.provider,
                modelUsed: data.model,
                confidence: data.confidence,
                verified: data.verified,
                plan: data.plan,
                llmCalls: data.llm_calls,
                costUsd: data.cost_usd,
                queryLogId: data.query_log_id,
                phoenixTraceUrl: data.phoenix_trace_url ?? null,
              });
            },
          },
          controller.signal,
        );
      } catch (error) {
        setStreamError(error instanceof Error ? error.message : "the connection to the assistant was interrupted");
      } finally {
        setStreaming(false);
      }
    },
    [
      conversationId,
      isStreaming,
      selectedConnectorIds,
      provider,
      model,
      addUserMessage,
      beginAssistantMessage,
      appendAssistantDelta,
      replaceAssistantContent,
      finalizeAssistantMessage,
      setConversationId,
      setStreamError,
      setStreaming,
    ],
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return {
    conversationId,
    messages,
    isStreaming,
    streamError,
    isLoadingHistory,
    openConversation,
    startNewConversation,
    sendMessage,
    stopStreaming,
  };
}
