/** Failure Analysis API service functions. */

import { apiClient } from "@/services/api-client";
import type {
  AnalysisRequest,
  AnalysisResponse,
  AnalysisSessionListItem,
  BatchAnalysisRequest,
  BatchAnalysisResponse,
} from "@/modules/failure-analysis/types";

interface ApiSuccessResponse<T> {
  data: T;
  meta?: Record<string, unknown>;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

/**
 * Submit failure output for AI-powered analysis.
 */
export async function analyzeFailure(
  request: AnalysisRequest,
): Promise<AnalysisResponse> {
  const response = await apiClient.post<ApiSuccessResponse<AnalysisResponse>>(
    "/failures/analyze",
    request,
  );
  return response.data.data;
}

/**
 * Submit failure output with uploaded artifact files for AI-powered analysis.
 *
 * Sends as multipart/form-data so files are included in the request.
 */
export async function analyzeFailureWithArtifacts(
  content: string,
  sourceType: string,
  files: File[],
): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append("content", content);
  formData.append("source_type", sourceType);
  for (const file of files) {
    formData.append("artifacts", file);
  }

  const response = await apiClient.post<ApiSuccessResponse<AnalysisResponse>>(
    "/failures/analyze-with-artifacts",
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    },
  );
  return response.data.data;
}

/**
 * Retrieve a completed failure analysis session by ID.
 */
export async function getFailureSession(
  sessionId: string,
): Promise<AnalysisResponse> {
  const response = await apiClient.get<ApiSuccessResponse<AnalysisResponse>>(
    `/failures/sessions/${sessionId}`,
  );
  return response.data.data;
}

/**
 * List past failure analysis sessions with pagination.
 */
export async function listFailureSessions(
  page: number = 1,
  pageSize: number = 20,
): Promise<PaginatedResponse<AnalysisSessionListItem>> {
  const response = await apiClient.get<
    ApiSuccessResponse<AnalysisSessionListItem[]>
  >("/failures/sessions", {
    params: { page, page_size: pageSize },
  });
  const meta = response.data.meta as
    | { pagination: { total: number } }
    | undefined;
  return {
    items: response.data.data,
    total: meta?.pagination?.total ?? 0,
  };
}

/**
 * Delete a failure analysis session by ID.
 */
export async function deleteFailureSession(
  sessionId: string,
): Promise<void> {
  await apiClient.delete(`/failures/sessions/${sessionId}`);
}

/**
 * Submit multiple failure inputs for batch AI-powered analysis.
 */
export async function batchAnalyzeFailures(
  request: BatchAnalysisRequest,
): Promise<BatchAnalysisResponse> {
  const response = await apiClient.post<
    ApiSuccessResponse<BatchAnalysisResponse>
  >("/failures/batch-analyze", request);
  return response.data.data;
}
