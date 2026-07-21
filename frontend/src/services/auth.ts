/** Auth API calls — register, login, profile. */

import { apiClient } from "@/services/api-client";

// ── Types ──────────────────────────────────────────────────────

export interface User {
  id: string;
  username: string;
  email: string;
  display_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  display_name?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

// ── Functions ──────────────────────────────────────────────────

export async function register(data: RegisterRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/register", data);
  return response.data;
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login", data);
  return response.data;
}

export async function getMe(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me");
  return response.data;
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<void> {
  await apiClient.post("/auth/change-password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
}
