/** TanStack Query hooks for the Failure Analysis module. */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AnalysisRequest, BatchAnalysisRequest } from "@/modules/failure-analysis/types";
import {
  analyzeFailure,
  analyzeFailureWithArtifacts,
  batchAnalyzeFailures,
  getFailureSession,
  listFailureSessions,
  deleteFailureSession,
} from "@/modules/failure-analysis/services/failure-analysis";

const FAILURE_KEYS = {
  all: ["failure-analysis"] as const,
  sessions: (page?: number) => [...FAILURE_KEYS.all, "sessions", page] as const,
  session: (id: string | undefined) =>
    [...FAILURE_KEYS.all, "session", id] as const,
};

/**
 * Submit failure output for analysis.
 */
export function useAnalyzeFailure() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: AnalysisRequest) => analyzeFailure(request),
    onSuccess: () => {
      // Invalidate session list so it refreshes with the new session
      queryClient.invalidateQueries({ queryKey: FAILURE_KEYS.sessions() });
    },
  });
}

/**
 * Submit failure output with uploaded artifact files for analysis.
 */
export function useAnalyzeFailureWithArtifacts() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      content,
      sourceType,
      files,
    }: {
      content: string;
      sourceType: string;
      files: File[];
    }) => analyzeFailureWithArtifacts(content, sourceType, files),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FAILURE_KEYS.sessions() });
    },
  });
}

/**
 * Fetch a single failure analysis session by ID.
 */
export function useFailureSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: FAILURE_KEYS.session(sessionId),
    queryFn: () => getFailureSession(sessionId!),
    enabled: !!sessionId,
  });
}

/**
 * Fetch a paginated list of failure analysis sessions.
 */
export function useFailureSessions(page: number = 1) {
  return useQuery({
    queryKey: FAILURE_KEYS.sessions(page),
    queryFn: () => listFailureSessions(page),
    staleTime: 30_000,
  });
}

/**
 * Delete a failure analysis session.
 * Invalidates both the session list and the specific session cache.
 */
export function useDeleteFailureSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) => deleteFailureSession(sessionId),
    onSuccess: (_data, sessionId) => {
      queryClient.invalidateQueries({ queryKey: FAILURE_KEYS.sessions() });
      queryClient.removeQueries({ queryKey: FAILURE_KEYS.session(sessionId) });
    },
  });
}

/**
 * Submit multiple failure inputs for batch analysis.
 */
export function useBatchAnalyzeFailures() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: BatchAnalysisRequest) => batchAnalyzeFailures(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FAILURE_KEYS.sessions() });
    },
  });
}
