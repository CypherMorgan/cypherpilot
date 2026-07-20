/** Settings API calls — AI provider configuration. */

import { apiClient } from "@/services/api-client";
import type { ApiSuccessResponse } from "@/types/api";

// ── Types ──────────────────────────────────────────────────────

export interface AiSettings {
  provider: string;
  openrouter_api_key: string;
  openrouter_model: string;
  ollama_base_url: string;
  ollama_model: string;
  gemini_api_key: string;
  gemini_model: string;
  max_tokens: number;
  temperature: number;
}

export interface AiSettingsUpdate {
  provider?: string;
  openrouter_api_key?: string;
  openrouter_model?: string;
  ollama_base_url?: string;
  ollama_model?: string;
  gemini_api_key?: string;
  gemini_model?: string;
  max_tokens?: number;
  temperature?: number;
}

// ── Functions ──────────────────────────────────────────────────

/**
 * Fetch the current AI provider settings (API keys are masked).
 */
export async function getAiSettings(): Promise<AiSettings> {
  const response = await apiClient.get<ApiSuccessResponse<AiSettings>>(
    "/settings/ai",
  );
  return response.data.data;
}

/**
 * Update AI provider settings at runtime.
 * Persists to .env.local and re-registers providers immediately.
 */
export async function updateAiSettings(
  update: AiSettingsUpdate,
): Promise<AiSettings> {
  const response = await apiClient.put<ApiSuccessResponse<AiSettings>>(
    "/settings/ai",
    update,
  );
  return response.data.data;
}
