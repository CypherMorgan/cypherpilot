/** Webhooks API calls. */

import { apiClient } from "@/services/api-client";

// ── Types ──────────────────────────────────────────────────────

export const WEBHOOK_EVENTS = [
  "analysis.completed",
  "analysis.failed",
] as const;

export type WebhookEvent = (typeof WEBHOOK_EVENTS)[number];

export interface DeliverySummary {
  delivery_id: string;
  event: string;
  status: "pending" | "delivered" | "failed";
  attempts: number;
  last_status_code: number | null;
  last_error: string | null;
  created_at: string;
}

export interface Webhook {
  id: string;
  name: string;
  url: string;
  events: WebhookEvent[];
  secret_masked: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_delivery: DeliverySummary | null;
}

export interface CreateWebhookPayload {
  name: string;
  url: string;
  events: WebhookEvent[];
  secret?: string;
}

export interface UpdateWebhookPayload {
  name?: string;
  url?: string;
  events?: WebhookEvent[];
  is_active?: boolean;
  regenerate_secret?: boolean;
}

export interface TestWebhookResult {
  delivery_id: string;
  event: string;
  status: "pending" | "delivered" | "failed";
  attempts: number;
  last_status_code: number | null;
  last_error: string | null;
}

// ── Functions ──────────────────────────────────────────────────

/** Fetch the current user's webhooks with their latest delivery outcome. */
export async function listWebhooks(): Promise<Webhook[]> {
  const response = await apiClient.get<{ data: Webhook[] }>("/webhooks");
  return response.data.data;
}

/** Create a webhook (secret is generated server-side when omitted). */
export async function createWebhook(
  data: CreateWebhookPayload,
): Promise<Webhook> {
  const response = await apiClient.post<{ data: Webhook }>("/webhooks", data);
  return response.data.data;
}

/** Get a single webhook by id. */
export async function getWebhook(webhookId: string): Promise<Webhook> {
  const response = await apiClient.get<{ data: Webhook }>(
    `/webhooks/${webhookId}`,
  );
  return response.data.data;
}

/** Update a webhook (partial; regenerate_secret rotates the signing key). */
export async function updateWebhook(
  webhookId: string,
  data: UpdateWebhookPayload,
): Promise<Webhook> {
  const response = await apiClient.patch<{ data: Webhook }>(
    `/webhooks/${webhookId}`,
    data,
  );
  return response.data.data;
}

/** Delete a webhook. */
export async function deleteWebhook(webhookId: string): Promise<void> {
  await apiClient.delete(`/webhooks/${webhookId}`);
}

/** Send a manual test ping and return the delivery outcome. */
export async function testWebhook(
  webhookId: string,
): Promise<TestWebhookResult> {
  const response = await apiClient.post<{ data: TestWebhookResult }>(
    `/webhooks/${webhookId}/test`,
  );
  return response.data.data;
}
