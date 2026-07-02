export type Role = "user" | "assistant";

export interface Citation {
  index: number;
  document_id: string | null;
  title: string | null;
  source_uri: string | null;
  page_number: number | null;
  score: number | null;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
}

export interface MessageRecord {
  id: string;
  role: Role;
  content: string;
  citations: Citation[];
  provider_used: string | null;
  model_used: string | null;
  confidence: number | null;
  created_at: string;
}

export interface ChatStreamRequestBody {
  message: string;
  conversation_id: string | null;
  connector_ids: string[] | null;
  provider: string | null;
  model: string | null;
}

export interface LLMCallRecord {
  task: string;
  provider: string | null;
  model: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens?: number;
}

export interface PlanStep {
  capability: string;
  parameter: string | null;
}

export interface ContentTable {
  type: "table";
  title?: string;
  headers: string[];
  rows: string[][];
}

export interface ContentChart {
  type: "chart";
  title: string;
  chart_type: "bar" | "line" | "pie";
  labels: string[];
  series: Record<string, number[]>;
}

export type ContentBlock = ContentTable | ContentChart;

export interface StreamDoneEvent {
  message_id: string;
  conversation_id: string;
  citations: Citation[];
  provider: string | null;
  model: string | null;
  verified: boolean;
  confidence: number | null;
  error: boolean;
  plan: PlanStep[];
  llm_calls: LLMCallRecord[];
  blocks: ContentBlock[];
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  latency_ms: number;
  query_log_id: string;
  phoenix_trace_url?: string | null;
}

export type ConnectorType =
  | "s3"
  | "azure_blob"
  | "gcs"
  | "slack"
  | "github"
  | "jira"
  | "confluence"
  | "notion"
  | "google_drive"
  | "dropbox"
  | "zendesk"
  | "linear"
  | "sql"
  | "mongodb"
  | "web";

export type AuthMode = "oauth" | "credentials" | "config_only";

export interface ConnectorTypeInfo {
  type: ConnectorType;
  auth_mode: AuthMode;
  required_credential_fields: string[];
  required_config_fields: string[];
}

export type ConnectorStatus = "connected" | "pending_auth" | "syncing" | "error" | "disconnected";

export interface Connector {
  id: string;
  type: ConnectorType;
  name: string;
  status: ConnectorStatus;
  config: Record<string, unknown>;
  last_synced_at: string | null;
  created_at: string;
}

export type DocumentStatus = "pending" | "processing" | "indexed" | "failed";

export interface DocumentRecord {
  id: string;
  title: string;
  source_type: string;
  source_uri: string;
  status: DocumentStatus;
  error_message: string | null;
  chunk_count: number;
  size_bytes: number;
  created_at: string;
  indexed_at: string | null;
}

export interface ProviderInfo {
  provider: string;
  default_model: string;
  circuit_state: "closed" | "open" | "half_open";
}

export interface ModelOption {
  id: string;
  label: string;
  tier: "flagship" | "balanced" | "fast" | "reasoning" | "default";
  is_default: boolean;
}

export interface ProviderModels {
  provider: string;
  default_model: string;
  circuit_state: ProviderInfo["circuit_state"] | null;
  configured: boolean;
  models: ModelOption[];
}

export interface ModelUsageBreakdown {
  provider: string;
  model: string;
  queries: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
}

export interface ProviderUsageBreakdown {
  provider: string;
  queries: number;
  llm_calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
}

export interface ModelCatalog {
  providers: ProviderModels[];
}

export interface TaskRoutingInfo {
  task: string;
  fallback_chain: string[];
  default_temperature: number;
}

export interface DashboardMetrics {
  total_queries: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  avg_tokens_per_query: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  avg_confidence: number;
  cache_hit_rate: number;
  by_provider: ProviderUsageBreakdown[];
  by_model: ModelUsageBreakdown[];
  by_day: {
    date: string;
    queries: number;
    prompt_tokens: number;
    completion_tokens: number;
    tokens: number;
    cost_usd: number;
    avg_confidence: number;
  }[];
  by_retrieval_strategy: { strategy: string; queries: number }[];
  by_capability: { capability: string; count: number }[];
  by_task: {
    task: string;
    calls: number;
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  }[];
}

export interface TraceOut {
  id: string;
  query_text: string;
  plan: PlanStep[];
  retrieval_strategy: string;
  confidence: number;
  provider: string;
  model: string;
  llm_calls: LLMCallRecord[];
  llm_call_count: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  latency_ms: number;
  created_at: string;
  phoenix_trace_url?: string | null;
}

export interface IntelligenceCapabilities {
  web_search: string[];
  direct_answer: string[];
  news: string[];
  places: string[];
  trends: string[];
  finance: string[];
  demographics: string[];
}

export interface ApiKeyField {
  key: string;
  label: string;
  group: "llm" | "intelligence";
  secret: boolean;
  placeholder: string;
  configured: boolean;
  masked_value: string | null;
}

export interface ApiKeysResponse {
  fields: ApiKeyField[];
}

export type ReportFormat = "pdf" | "docx" | "html";

export interface ApiErrorBody {
  code?: string;
  message?: string;
  detail?: string | { msg: string }[];
}
