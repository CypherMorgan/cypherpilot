/** Standard API error shape returned by the backend */
export interface ApiError {
  code: string;
  message: string;
  detail: Record<string, unknown> | null;
  requestId: string;
  status: number;
}

/** Standard API success envelope */
export interface ApiSuccessResponse<T> {
  data: T;
  meta: ApiMeta;
}

/** Standard API list envelope */
export interface ApiListResponse<T> {
  data: T[];
  meta: ApiListMeta;
}

/** Pagination and metadata */
export interface ApiMeta {
  request_id: string;
  timestamp: string;
}

/** List-specific metadata with pagination */
export interface ApiListMeta extends ApiMeta {
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

/** Health check response */
export interface HealthResponse {
  status: string;
  app_name: string;
  app_version: string;
  active_provider?: string;
  active_model?: string;
  checks: {
    database: {
      status: string;
      latency_ms: number;
    };
  };
}

/** A recently failed analysis session (dashboard widget). */
export interface RecentFailure {
  session_id: string;
  title: string | null;
  analysis_type: string;
  error_message: string | null;
  created_at: string;
}

/** One day in the 14-day usage series. */
export interface UsagePoint {
  date: string;
  sessions: number;
}

/** Aggregate usage analytics for the authenticated user. */
export interface DashboardStats {
  total_sessions: number;
  sessions_by_type: Record<string, number>;
  sessions_by_status: Record<string, number>;
  success_rate: number;
  total_tokens: number;
  total_latency_ms: number;
  avg_latency_ms: number;
  recent_failures: RecentFailure[];
  usage_over_time: UsagePoint[];
}
