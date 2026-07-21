import axios from "axios";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";

import { API_BASE_URL, API_PREFIX } from "@/lib/constants";
import type { ApiError } from "@/types/api";

/**
 * Typed Axios instance with base URL, request/response interceptors,
 * and normalized error handling.
 *
 * Business modules should NOT import axios directly — always go through
 * a typed service function in src/services/.
 */
export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  timeout: 180_000, // 180s — AI analysis can be slow (Ollama cold start >60s)
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Request interceptor — inject auth token from localStorage.
 */
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem("cypherpilot-token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Normalize API errors into a standard ApiError shape.
 * The backend returns:
 *   { "error": { "code": "...", "message": "...", "detail": ... }, "meta": { ... } }
 *
 * We flatten this into a consistent ApiError interface.
 */
function normalizeError(error: AxiosError<{ error?: ApiError }>): ApiError {
  if (error.response?.data?.error) {
    return {
      ...error.response.data.error,
      status: error.response.status,
      requestId: "",
    };
  }

  // Network or timeout errors
  if (error.code === "ECONNABORTED") {
    return {
      code: "TIMEOUT",
      message: "Request timed out",
      detail: null,
      requestId: "",
      status: 0,
    };
  }

  if (!error.response) {
    return {
      code: "NETWORK_ERROR",
      message: "Unable to reach the server",
      detail: null,
      requestId: "",
      status: 0,
    };
  }

  return {
    code: "UNKNOWN_ERROR",
    message: error.message || "An unexpected error occurred",
    detail: null,
    requestId: "",
    status: error.response?.status ?? 0,
  };
}

/**
 * Response error interceptor — transforms raw Axios errors into typed ApiError.
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ error?: ApiError }>) => {
    const normalized = normalizeError(error);
    return Promise.reject(normalized);
  },
);

export { normalizeError };
export type { ApiError };
