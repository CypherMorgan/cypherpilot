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
