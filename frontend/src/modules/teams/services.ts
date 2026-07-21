/** Teams API calls. */

import { apiClient } from "@/services/api-client";

// ── Types ──────────────────────────────────────────────────────

export interface Team {
  id: string;
  name: string;
  description: string | null;
  created_by: string | null;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  user_id: string;
  username: string;
  display_name: string | null;
  role: string;
  joined_at: string;
}

export interface TeamDetail extends Team {
  members: TeamMember[];
}

// ── Functions ──────────────────────────────────────────────────

export async function listMyTeams(): Promise<Team[]> {
  const response = await apiClient.get<{ data: Team[] }>("/teams");
  return response.data.data;
}

export async function createTeam(
  name: string,
  description?: string,
): Promise<Team> {
  const response = await apiClient.post<{ data: Team }>("/teams", {
    name,
    description,
  });
  return response.data.data;
}

export async function getTeamDetail(teamId: string): Promise<TeamDetail> {
  const response = await apiClient.get<{ data: TeamDetail }>(
    `/teams/${teamId}`,
  );
  return response.data.data;
}

export async function updateTeam(
  teamId: string,
  data: { name?: string; description?: string },
): Promise<Team> {
  const response = await apiClient.patch<{ data: Team }>(
    `/teams/${teamId}`,
    data,
  );
  return response.data.data;
}

export async function deleteTeam(teamId: string): Promise<void> {
  await apiClient.delete(`/teams/${teamId}`);
}

export async function inviteMember(
  teamId: string,
  username: string,
  role: string = "member",
): Promise<TeamMember> {
  const response = await apiClient.post<{ data: TeamMember }>(
    `/teams/${teamId}/members`,
    { username, role },
  );
  return response.data.data;
}

export async function removeMember(
  teamId: string,
  userId: string,
): Promise<void> {
  await apiClient.delete(`/teams/${teamId}/members/${userId}`);
}

export async function updateMemberRole(
  teamId: string,
  userId: string,
  role: string,
): Promise<TeamMember> {
  const response = await apiClient.patch<{ data: TeamMember }>(
    `/teams/${teamId}/members/${userId}`,
    { role },
  );
  return response.data.data;
}
