"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { MessageSquare, Plus, Search, Trash2 } from "lucide-react";
import { Topbar } from "@/components/layout/Topbar";
import { Skeleton } from "@/components/ui/Skeleton";
import { StaggerItem } from "@/components/ui/StaggerItem";
import { ErrorState } from "@/components/ui/ErrorState";
import { deleteConversation, listConversations } from "@/lib/api";
import { formatRelativeTime, truncate } from "@/lib/utils";
import { useChatStore } from "@/store/chatStore";
import { useToastStore } from "@/store/toastStore";
import { LANDING_SHELL } from "@/lib/constants/landing";
import type { ConversationSummary } from "@/lib/types";

interface Group {
  label: string;
  items: ConversationSummary[];
}

function groupByRecency(conversations: ConversationSummary[]): Group[] {
  const now = Date.now();
  const dayMs = 86_400_000;
  const buckets: Record<string, ConversationSummary[]> = { Today: [], Yesterday: [], "Previous 7 days": [], Older: [] };
  for (const c of conversations) {
    const age = now - new Date(c.created_at).getTime();
    if (age < dayMs) buckets["Today"]!.push(c);
    else if (age < 2 * dayMs) buckets["Yesterday"]!.push(c);
    else if (age < 7 * dayMs) buckets["Previous 7 days"]!.push(c);
    else buckets["Older"]!.push(c);
  }
  return Object.entries(buckets)
    .filter(([, items]) => items.length > 0)
    .map(([label, items]) => ({ label, items }));
}

export default function HistoryPage() {
  const router = useRouter();
  const pushToast = useToastStore((state) => state.push);
  const conversationId = useChatStore((state) => state.conversationId);
  const setConversationId = useChatStore((state) => state.setConversationId);
  const resetConversation = useChatStore((state) => state.resetConversation);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const load = useCallback(() => {
    setIsLoading(true);
    setError(null);
    listConversations()
      .then((data) => setConversations(data))
      .catch((err) => setError(err instanceof Error ? err.message : "failed to load conversations"))
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const groups = useMemo(() => {
    const filtered = query.trim()
      ? conversations.filter((c) => c.title.toLowerCase().includes(query.trim().toLowerCase()))
      : conversations;
    return groupByRecency(filtered);
  }, [conversations, query]);

  const openConversation = (id: string) => {
    setConversationId(id);
    router.push("/app");
  };

  const startNew = () => {
    resetConversation();
    router.push("/app");
  };

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (conversationId === id) resetConversation();
      setConfirmDeleteId(null);
      pushToast("Conversation deleted", "live");
    } catch (err) {
      pushToast(err instanceof Error ? err.message : "Failed to delete conversation", "attn");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="flex h-full flex-1 flex-col overflow-y-auto">
      <Topbar
        title="History"
        description="Every conversation you've had, grouped by when it happened"
        actions={
          <button
            type="button"
            onClick={startNew}
            className="group flex items-center gap-1.5 rounded-md bg-ink px-3 py-1.5 text-sm font-medium text-canvas transition-all hover:opacity-90"
          >
            <Plus className="h-3.5 w-3.5 transition-transform duration-200 group-hover:rotate-90" strokeWidth={2} />
            New conversation
          </button>
        }
      />
      <div className={`flex flex-col gap-6 py-4 md:py-8 ${LANDING_SHELL}`}>
        <div className="relative max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-faint" strokeWidth={1.75} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search conversations"
            className="w-full rounded-md border border-line bg-surface py-2 pl-9 pr-3 text-sm text-ink transition-colors placeholder:text-ink-faint focus:border-route focus:outline-none"
          />
        </div>

        {isLoading ? (
          <div className="grid gap-3 lg:grid-cols-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : conversations.length === 0 ? (
          <div className="animate-fade-in flex flex-col items-center justify-center gap-3 py-20 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-sunken">
              <MessageSquare className="h-5 w-5 text-ink-faint" strokeWidth={1.5} />
            </span>
            <p className="text-sm text-ink-muted">No conversations yet.</p>
            <button type="button" onClick={startNew} className="text-sm font-medium text-route hover:underline">
              Start your first one
            </button>
          </div>
        ) : groups.length === 0 ? (
          <p className="py-10 text-sm text-ink-faint">No conversations match &ldquo;{query}&rdquo;.</p>
        ) : (
          <div className="flex flex-col gap-8">
            {groups.map((group) => (
              <div key={group.label} className="flex flex-col gap-2">
                <p className="font-mono text-[11px] uppercase tracking-wide text-ink-faint">{group.label}</p>
                <div className="grid gap-2 lg:grid-cols-2">
                  {group.items.map((conversation, i) => (
                    <StaggerItem key={conversation.id} index={i} step={40}>
                      <div className="flex items-center gap-2 rounded-md border border-line bg-surface p-2 transition-colors hover:border-line-strong">
                        <button
                          type="button"
                          onClick={() => openConversation(conversation.id)}
                          className="flex min-w-0 flex-1 items-center gap-3 rounded-sm px-2 py-1.5 text-left transition-colors hover:bg-surface-sunken"
                        >
                          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-surface-sunken">
                            <MessageSquare className="h-4 w-4 text-ink-muted" strokeWidth={1.6} />
                          </span>
                          <div className="min-w-0">
                            <p className="truncate text-sm text-ink">{truncate(conversation.title, 60)}</p>
                            <p className="font-mono text-[11px] text-ink-faint">{formatRelativeTime(conversation.created_at)}</p>
                          </div>
                        </button>
                        {confirmDeleteId === conversation.id ? (
                          <div className="flex shrink-0 items-center gap-1">
                            <button
                              type="button"
                              disabled={deletingId === conversation.id}
                              onClick={(e) => {
                                e.stopPropagation();
                                void handleDelete(conversation.id);
                              }}
                              className="rounded-sm bg-attn px-2 py-1 text-xs font-medium text-surface transition-opacity hover:opacity-90 disabled:opacity-50"
                            >
                              {deletingId === conversation.id ? "Deleting…" : "Delete"}
                            </button>
                            <button
                              type="button"
                              disabled={deletingId === conversation.id}
                              onClick={(e) => {
                                e.stopPropagation();
                                setConfirmDeleteId(null);
                              }}
                              className="rounded-sm px-2 py-1 text-xs text-ink-muted transition-colors hover:text-ink disabled:opacity-50"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setConfirmDeleteId(conversation.id);
                            }}
                            aria-label="Delete conversation"
                            className="shrink-0 rounded-sm p-2 text-ink-faint transition-colors hover:bg-attn-soft hover:text-attn"
                          >
                            <Trash2 className="h-4 w-4" strokeWidth={1.75} />
                          </button>
                        )}
                      </div>
                    </StaggerItem>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
