import { create } from "zustand";
import type { Citation, ContentBlock, LLMCallRecord, MessageRecord, PlanStep } from "@/lib/types";

export interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  blocks: ContentBlock[];
  providerUsed: string | null;
  modelUsed: string | null;
  confidence: number | null;
  verified: boolean | null;
  isStreaming: boolean;
  plan: PlanStep[];
  llmCalls: LLMCallRecord[];
  costUsd: number | null;
  queryLogId: string | null;
  phoenixTraceUrl: string | null;
}

interface ChatState {
  conversationId: string | null;
  messages: DisplayMessage[];
  isStreaming: boolean;
  streamError: string | null;
  selectedConnectorIds: string[] | null;
  provider: string | null;
  model: string | null;
  setConversationId: (id: string | null) => void;
  loadMessages: (records: MessageRecord[]) => void;
  resetConversation: () => void;
  addUserMessage: (id: string, content: string) => void;
  beginAssistantMessage: () => void;
  appendAssistantDelta: (delta: string) => void;
  replaceAssistantContent: (content: string) => void;
  finalizeAssistantMessage: (data: {
    id: string;
    citations: Citation[];
    blocks: ContentBlock[];
    providerUsed: string | null;
    modelUsed: string | null;
    confidence: number | null;
    verified: boolean;
    plan: PlanStep[];
    llmCalls: LLMCallRecord[];
    costUsd: number;
    queryLogId: string;
    phoenixTraceUrl: string | null;
  }) => void;
  setStreaming: (value: boolean) => void;
  setStreamError: (message: string | null) => void;
  setSelectedConnectorIds: (ids: string[] | null) => void;
  setProvider: (provider: string | null) => void;
  setModel: (model: string | null) => void;
}

function newClientId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `local-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export const useChatStore = create<ChatState>()((set) => ({
  conversationId: null,
  messages: [],
  isStreaming: false,
  streamError: null,
  selectedConnectorIds: null,
  provider: null,
  model: null,

  setConversationId: (id) => set({ conversationId: id }),

  loadMessages: (records) =>
    set({
      messages: records.map((record) => ({
        id: record.id,
        role: record.role,
        content: record.content,
        citations: record.citations,
        blocks: [],
        providerUsed: record.provider_used,
        modelUsed: record.model_used,
        confidence: record.confidence,
        verified: null,
        isStreaming: false,
        plan: [],
        llmCalls: [],
        costUsd: null,
        queryLogId: null,
        phoenixTraceUrl: null,
      })),
    }),

  resetConversation: () => set({ conversationId: null, messages: [], streamError: null }),

  addUserMessage: (id, content) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id,
          role: "user",
          content,
          citations: [],
          blocks: [],
          providerUsed: null,
          modelUsed: null,
          confidence: null,
          verified: null,
          isStreaming: false,
          plan: [],
          llmCalls: [],
          costUsd: null,
          queryLogId: null,
          phoenixTraceUrl: null,
        },
      ],
    })),

  beginAssistantMessage: () =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id: newClientId(),
          role: "assistant",
          content: "",
          citations: [],
          blocks: [],
          providerUsed: null,
          modelUsed: null,
          confidence: null,
          verified: null,
          isStreaming: true,
          plan: [],
          llmCalls: [],
          costUsd: null,
          queryLogId: null,
          phoenixTraceUrl: null,
        },
      ],
    })),

  appendAssistantDelta: (delta) =>
    set((state) => {
      if (state.messages.length === 0) return state;
      const messages = [...state.messages];
      const last = messages[messages.length - 1];
      if (last && last.role === "assistant" && last.isStreaming) {
        messages[messages.length - 1] = { ...last, content: last.content + delta };
      }
      return { messages };
    }),

  replaceAssistantContent: (content) =>
    set((state) => {
      if (state.messages.length === 0) return state;
      const messages = [...state.messages];
      const last = messages[messages.length - 1];
      if (last && last.role === "assistant" && last.isStreaming) {
        messages[messages.length - 1] = { ...last, content };
      }
      return { messages };
    }),

  finalizeAssistantMessage: (data) =>
    set((state) => {
      if (state.messages.length === 0) return state;
      const messages = [...state.messages];
      const last = messages[messages.length - 1];
      if (last && last.role === "assistant") {
        messages[messages.length - 1] = {
          ...last,
          id: data.id,
          citations: data.citations,
          blocks: data.blocks,
          providerUsed: data.providerUsed,
          modelUsed: data.modelUsed,
          confidence: data.confidence,
          verified: data.verified,
          isStreaming: false,
          plan: data.plan,
          llmCalls: data.llmCalls,
          costUsd: data.costUsd,
          queryLogId: data.queryLogId,
          phoenixTraceUrl: data.phoenixTraceUrl,
        };
      }
      return { messages };
    }),

  setStreaming: (value) => set({ isStreaming: value }),
  setStreamError: (message) => set({ streamError: message }),
  setSelectedConnectorIds: (ids) => set({ selectedConnectorIds: ids }),
  setProvider: (provider) => set({ provider }),
  setModel: (model) => set({ model }),
}));
