import { describe, it, expect, vi, beforeEach } from "vitest";
import { normalizeError } from "@/services/api-client";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";

describe("normalizeError", () => {
  it("extracts backend error response", () => {
    const error = {
      response: {
        status: 502,
        data: {
          error: {
            code: "PROVIDER_ERROR",
            message: "AI provider returned an error",
            detail: { provider: "openrouter" },
          },
        },
      },
    } as AxiosError;

    const result = normalizeError(error);
    expect(result.code).toBe("PROVIDER_ERROR");
    expect(result.message).toBe("AI provider returned an error");
    expect(result.status).toBe(502);
    expect(result.detail).toEqual({ provider: "openrouter" });
  });

  it("handles timeout errors", () => {
    const error = {
      code: "ECONNABORTED",
      message: "timeout of 60000ms exceeded",
    } as AxiosError;

    const result = normalizeError(error);
    expect(result.code).toBe("TIMEOUT");
    expect(result.message).toBe("Request timed out");
  });

  it("handles network errors", () => {
    const error = {
      message: "Network Error",
    } as AxiosError;

    const result = normalizeError(error);
    expect(result.code).toBe("NETWORK_ERROR");
    expect(result.message).toBe("Unable to reach the server");
  });

  it("handles unknown errors", () => {
    const error = {
      message: "Something went wrong",
      response: {
        status: 500,
        data: {},
      },
    } as AxiosError;

    const result = normalizeError(error);
    expect(result.code).toBe("UNKNOWN_ERROR");
    expect(result.status).toBe(500);
  });
});

describe("apiClient", () => {
  it("is configured with correct base URL and timeout", async () => {
    // Dynamic import to get the configured instance
    const { apiClient } = await import("@/services/api-client");
    expect(apiClient.defaults.timeout).toBe(180000);
    expect(apiClient.defaults.baseURL).toContain("/api/v1");
  });
});
