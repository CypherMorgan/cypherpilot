/** Comparison API service — compare two analysis sessions. */

import { apiClient } from "@/services/api-client";
import type { ApiSuccessResponse } from "@/types/api";

// ── Types ──────────────────────────────────────────────────────

export interface SessionInfo {
  id: string;
  title: string | null;
  analysis_type: string;
  status: string;
  provider: string | null;
  model: string | null;
  total_tokens: number | null;
  latency_ms: number | null;
  created_at: string | null;
}

export interface ScalarDiff {
  field: string;
  value_a: unknown;
  value_b: unknown;
  changed: boolean;
}

export interface SectionDiff {
  section: string;
  count_a: number;
  count_b: number;
  added: Record<string, unknown>[];
  removed: Record<string, unknown>[];
  changed: { a: Record<string, unknown>; b: Record<string, unknown> }[];
  unchanged: Record<string, unknown>[];
}

export interface ComparisonResult {
  session_a: SessionInfo;
  session_b: SessionInfo;
  metadata_diffs: ScalarDiff[];
  summary_a: string | null;
  summary_b: string | null;
  section_diffs: SectionDiff[];
  raw_a: Record<string, unknown> | null;
  raw_b: Record<string, unknown> | null;
}

export interface CompareSessionItem {
  id: string;
  title: string | null;
  analysis_type: string;
  status: string;
  provider: string | null;
  model: string | null;
  total_tokens: number | null;
  created_at: string | null;
}

// ── API functions ──────────────────────────────────────────────

export async function compareSessions(
  sessionIdA: string,
  sessionIdB: string,
): Promise<ComparisonResult> {
  const response = await apiClient.post<ApiSuccessResponse<ComparisonResult>>(
    "/compare",
    { session_id_a: sessionIdA, session_id_b: sessionIdB },
  );
  return response.data.data;
}

export async function listCompareSessions(params: {
  analysis_type?: string;
  page?: number;
  page_size?: number;
}): Promise<{ items: CompareSessionItem[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params.analysis_type) searchParams.set("analysis_type", params.analysis_type);
  if (params.page) searchParams.set("page", String(params.page));
  if (params.page_size) searchParams.set("page_size", String(params.page_size));

  const qs = searchParams.toString();
  const response = await apiClient.get<ApiSuccessResponse<CompareSessionItem[]>>(
    `/compare/sessions${qs ? `?${qs}` : ""}`,
  );
  return { items: response.data.data, total: (response.data as unknown as { meta: { total: number } }).meta?.total ?? 0 };
}

// ── Display helpers ────────────────────────────────────────────

const SECTION_LABELS: Record<string, string> = {
  root_causes: "Root Causes",
  suggested_fixes: "Suggested Fixes",
  affected_components: "Affected Components",
  test_failures: "Test Failures",
  recommendations: "Recommendations",
  environment_details: "Environment Details",
  related_tests: "Related Tests",
  functional_tests: "Functional Tests",
  negative_tests: "Negative Tests",
  boundary_tests: "Boundary Tests",
  edge_cases: "Edge Cases",
  assumptions: "Assumptions",
  risks: "Risks",
  missing_requirements: "Missing Requirements",
  suggested_questions: "Suggested Questions",
  automation_candidates: "Automation Candidates",
};

export function getSectionLabel(section: string): string {
  return SECTION_LABELS[section] ?? section.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

const ANALYSIS_TYPE_LABELS: Record<string, string> = {
  "failure-analysis": "Failure Analysis",
  "requirement-analysis": "Requirement Analysis",
  "api-test-generation": "API Test Generation",
};

export function getAnalysisTypeLabel(type: string): string {
  return ANALYSIS_TYPE_LABELS[type] ?? type;
}

const ANALYSIS_TYPE_COLORS: Record<string, string> = {
  "failure-analysis": "bg-red-500/15 text-red-600 dark:text-red-400",
  "requirement-analysis": "bg-blue-500/15 text-blue-600 dark:text-blue-400",
  "api-test-generation": "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
};

export function getAnalysisTypeColor(type: string): string {
  return ANALYSIS_TYPE_COLORS[type] ?? "bg-muted text-muted-foreground";
}
