export interface NotificationPreference {
  id: string;
  user_id: string;
  email_enabled: boolean;
  email_analysis_completed: boolean;
  email_analysis_failed: boolean;
  email_team_invite: boolean;
  email_team_removed: boolean;
  email_team_role_changed: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationPreferenceUpdate {
  email_enabled?: boolean;
  email_analysis_completed?: boolean;
  email_analysis_failed?: boolean;
  email_team_invite?: boolean;
  email_team_removed?: boolean;
  email_team_role_changed?: boolean;
}
