import { AnthropicIcon, OpenAIIcon, GeminiIcon, GroqIcon, XAIIcon, MoonshotIcon } from "@/components/icons/BrandIcons";

import type { ModelCatalog } from "@/lib/types";

interface ProviderMeta {
  label: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

export const PROVIDER_META: Record<string, ProviderMeta> = {
  anthropic: { label: "Anthropic", icon: AnthropicIcon },
  openai: { label: "OpenAI", icon: OpenAIIcon },
  gemini: { label: "Gemini", icon: GeminiIcon },
  groq: { label: "Groq", icon: GroqIcon },
  grok: { label: "Grok", icon: XAIIcon },
  moonshot: { label: "Moonshot", icon: MoonshotIcon },
};

export function providerLabel(provider: string): string {
  return PROVIDER_META[provider]?.label ?? provider;
}

export function providerIcon(provider: string): React.ComponentType<React.SVGProps<SVGSVGElement>> | null {
  return PROVIDER_META[provider]?.icon ?? null;
}

export const TIER_LABELS: Record<string, string> = {
  flagship: "Flagship",
  balanced: "Balanced",
  fast: "Fast",
  reasoning: "Reasoning",
  default: "Default",
};

export const TIER_DESCRIPTIONS: Record<string, string> = {
  flagship: "Highest quality for complex work",
  balanced: "Good balance of speed and quality",
  fast: "Low latency for quick tasks",
  reasoning: "Extended thinking for logic and math",
  default: "Used when Auto route picks this provider",
};

export function modelLabel(catalog: ModelCatalog | null, provider: string, modelId: string): string {
  const entry = catalog?.providers.find((item) => item.provider === provider);
  return entry?.models.find((model) => model.id === modelId)?.label ?? modelId;
}
