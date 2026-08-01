/** TypeScript types for the Templates module. */

import type { InputSourceType } from "@/modules/failure-analysis/types";

/** A reusable analysis template owned by the current user. */
export interface AnalysisTemplate {
  id: string;
  name: string;
  description: string | null;
  content: string;
  source_type: InputSourceType;
  created_at: string;
  updated_at: string;
}

/** Paginated list response from GET /templates. */
export interface TemplateListResponse {
  items: AnalysisTemplate[];
  total: number;
  page: number;
  page_size: number;
}

/** Payload for POST /templates. */
export interface CreateTemplatePayload {
  name: string;
  description?: string | null;
  content: string;
  source_type: InputSourceType;
}

/** Payload for PATCH /templates/{id} — all fields optional. */
export interface UpdateTemplatePayload {
  name?: string;
  description?: string | null;
  content?: string;
  source_type?: InputSourceType;
}
