/** Templates API service. */

import { apiClient } from "@/services/api-client";
import type {
  AnalysisTemplate,
  CreateTemplatePayload,
  TemplateListResponse,
  UpdateTemplatePayload,
} from "@/modules/templates/types";

/**
 * Fetch the current user's templates with pagination.
 */
export async function listTemplates(params?: {
  page?: number;
  page_size?: number;
}): Promise<TemplateListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.page_size) searchParams.set("page_size", String(params.page_size));

  const qs = searchParams.toString();
  const response = await apiClient.get<TemplateListResponse>(
    `/templates${qs ? `?${qs}` : ""}`,
  );
  return response.data;
}

/**
 * Create a new template.
 */
export async function createTemplate(
  data: CreateTemplatePayload,
): Promise<AnalysisTemplate> {
  const response = await apiClient.post<AnalysisTemplate>("/templates", data);
  return response.data;
}

/**
 * Update an existing template.
 */
export async function updateTemplate(
  templateId: string,
  data: UpdateTemplatePayload,
): Promise<AnalysisTemplate> {
  const response = await apiClient.patch<AnalysisTemplate>(
    `/templates/${templateId}`,
    data,
  );
  return response.data;
}

/**
 * Delete a template.
 */
export async function deleteTemplate(templateId: string): Promise<void> {
  await apiClient.delete(`/templates/${templateId}`);
}
