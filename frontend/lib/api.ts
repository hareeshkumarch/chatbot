import type {
  ApiErrorBody,
  ChatStreamRequestBody,
  Connector,
  ConnectorTypeInfo,
  ConversationSummary,
  DashboardMetrics,
  DocumentRecord,
  ApiKeysResponse,
  IntelligenceCapabilities,
  MessageRecord,
  ModelCatalog,
  ProviderInfo,
  ReportFormat,
  StreamDoneEvent,
  TaskRoutingInfo,
  TraceOut,
} from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ApiErrorBody;
    if (body.message) return body.message;
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail) && body.detail[0]?.msg) return body.detail[0].msg;
  } catch {
  }
  return `Request failed with status ${response.status}`;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body && !(init.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new ApiError(response.status, await extractErrorMessage(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function listConversations(): Promise<ConversationSummary[]> {
  return apiFetch<ConversationSummary[]>("/api/v1/chat/conversations");
}

export async function createConversation(title?: string): Promise<ConversationSummary> {
  return apiFetch<ConversationSummary>("/api/v1/chat/conversations", {
    method: "POST",
    body: JSON.stringify({ title: title ?? null }),
  });
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await apiFetch<void>(`/api/v1/chat/conversations/${conversationId}`, { method: "DELETE" });
}

export async function getMessages(conversationId: string): Promise<MessageRecord[]> {
  return apiFetch<MessageRecord[]>(`/api/v1/chat/conversations/${conversationId}/messages`);
}

interface StreamHandlers {
  onStart?: (data: { conversation_id: string; user_message_id: string }) => void;
  onToken?: (delta: string) => void;
  onReplace?: (content: string) => void;
  onStreamError?: (message: string) => void;
  onDone?: (data: StreamDoneEvent) => void;
}

export async function streamChat(body: ChatStreamRequestBody, handlers: StreamHandlers, signal?: AbortSignal): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new ApiError(response.status, await extractErrorMessage(response));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const processEvent = (rawEvent: string) => {
    let eventName = "message";
    let dataLine = "";
    for (const line of rawEvent.split("\n")) {
      if (line.startsWith("event:")) eventName = line.slice(6).trim();
      if (line.startsWith("data:")) dataLine = line.slice(5).trim();
    }
    if (!dataLine) return;
    let payload: unknown;
    try {
      payload = JSON.parse(dataLine);
    } catch {
      return;
    }
    if (eventName === "start") handlers.onStart?.(payload as { conversation_id: string; user_message_id: string });
    else if (eventName === "token") handlers.onToken?.((payload as { delta: string }).delta);
    else if (eventName === "replace") handlers.onReplace?.((payload as { content: string }).content);
    else if (eventName === "error") handlers.onStreamError?.((payload as { message: string }).message);
    else if (eventName === "done") handlers.onDone?.(payload as StreamDoneEvent);
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      processEvent(buffer.slice(0, boundary));
      buffer = buffer.slice(boundary + 2);
      boundary = buffer.indexOf("\n\n");
    }
  }
}

export async function listDocuments(): Promise<DocumentRecord[]> {
  return apiFetch<DocumentRecord[]>("/api/v1/documents");
}

export async function uploadDocument(file: File): Promise<DocumentRecord> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<DocumentRecord>("/api/v1/documents/upload", { method: "POST", body: formData });
}

export async function deleteDocument(documentId: string): Promise<void> {
  await apiFetch<void>(`/api/v1/documents/${documentId}`, { method: "DELETE" });
}

export async function listConnectors(): Promise<Connector[]> {
  return apiFetch<Connector[]>("/api/v1/connectors");
}

export async function listConnectorTypes(): Promise<ConnectorTypeInfo[]> {
  return apiFetch<ConnectorTypeInfo[]>("/api/v1/connectors/types");
}

export async function createConnector(payload: {
  type: string;
  name: string;
  config?: Record<string, unknown>;
  credentials?: Record<string, unknown>;
}): Promise<Connector> {
  return apiFetch<Connector>("/api/v1/connectors", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateConnector(connectorId: string, payload: { name?: string; config?: Record<string, unknown> }): Promise<Connector> {
  return apiFetch<Connector>(`/api/v1/connectors/${connectorId}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export async function updateConnectorCredentials(connectorId: string, credentials: Record<string, unknown>): Promise<Connector> {
  return apiFetch<Connector>(`/api/v1/connectors/${connectorId}/credentials`, {
    method: "PUT",
    body: JSON.stringify({ credentials }),
  });
}

export async function getAuthorizeUrl(connectorId: string): Promise<{ authorize_url: string }> {
  return apiFetch<{ authorize_url: string }>(`/api/v1/connectors/${connectorId}/authorize`);
}

export async function testConnector(connectorId: string): Promise<{ connected: boolean; detail: string | null }> {
  return apiFetch(`/api/v1/connectors/${connectorId}/test`, { method: "POST" });
}

export async function syncConnector(connectorId: string): Promise<{ queued: boolean }> {
  return apiFetch(`/api/v1/connectors/${connectorId}/sync`, { method: "POST" });
}

export async function deleteConnector(connectorId: string): Promise<void> {
  await apiFetch<void>(`/api/v1/connectors/${connectorId}`, { method: "DELETE" });
}

export async function listProviders(): Promise<ProviderInfo[]> {
  return apiFetch<ProviderInfo[]>("/api/v1/models/providers");
}

export async function listTaskRouting(): Promise<TaskRoutingInfo[]> {
  return apiFetch<TaskRoutingInfo[]>("/api/v1/models/tasks");
}

export async function listModelCatalog(): Promise<ModelCatalog> {
  return apiFetch<ModelCatalog>("/api/v1/models/catalog");
}

export async function getDashboardMetrics(days = 7): Promise<DashboardMetrics> {
  return apiFetch<DashboardMetrics>(`/api/v1/analytics/dashboard?days=${days}`);
}

export async function getIntelligenceCapabilities(): Promise<IntelligenceCapabilities> {
  return apiFetch<IntelligenceCapabilities>("/api/v1/intelligence/capabilities");
}

export async function getApiKeys(): Promise<ApiKeysResponse> {
  return apiFetch("/api/v1/settings/api-keys");
}

export async function updateApiKeys(keys: Record<string, string | null>): Promise<ApiKeysResponse> {
  return apiFetch("/api/v1/settings/api-keys", {
    method: "PUT",
    body: JSON.stringify({ keys }),
  });
}

export async function getTrace(queryLogId: string): Promise<TraceOut> {
  return apiFetch<TraceOut>(`/api/v1/analytics/traces/${queryLogId}`);
}

export async function generateReport(
  query: string,
  format: ReportFormat,
  connectorIds: string[] | null,
  provider: string | null,
  model: string | null,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, format, connector_ids: connectorIds, provider, model }),
  });

  if (!response.ok) {
    throw new ApiError(response.status, await extractErrorMessage(response));
  }

  const disposition = response.headers.get("content-disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match?.[1] ?? `report.${format}`;

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
