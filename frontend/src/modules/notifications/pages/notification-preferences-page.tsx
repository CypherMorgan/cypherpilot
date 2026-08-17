import { Mail, ArrowLeft, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useNotificationPreferences, useUpdateNotificationPreferences } from "@/modules/notifications/hooks/use-notification-preferences";
import { useState, useEffect } from "react";
import type { NotificationPreference } from "@/modules/notifications/types/preferences";
import { cn } from "@/lib/utils";

interface ToggleRowProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

function ToggleRow({ label, description, checked, onChange, disabled }: ToggleRowProps) {
  return (
    <div className={cn("flex items-center justify-between gap-4 py-3", disabled && "opacity-50")}>
      <div className="flex-1">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed",
          checked ? "bg-primary" : "bg-input",
        )}
      >
        <span
          className={cn(
            "pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg ring-0 transition-transform",
            checked ? "translate-x-5" : "translate-x-0",
          )}
        />
      </button>
    </div>
  );
}

export function NotificationPreferencesPage() {
  const navigate = useNavigate();
  const { data: preferences, isLoading, error } = useNotificationPreferences();
  const updateMutation = useUpdateNotificationPreferences();

  // Local state for optimistic UI
  const [localPrefs, setLocalPrefs] = useState<NotificationPreference | null>(null);

  useEffect(() => {
    if (preferences) {
      setLocalPrefs(preferences);
    }
  }, [preferences]);

  const handleToggle = (field: keyof NotificationPreference, value: boolean) => {
    if (!localPrefs) return;

    // Optimistic update
    setLocalPrefs({ ...localPrefs, [field]: value });

    // Send to server
    updateMutation.mutate({ [field]: value });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-8">
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-sm text-muted-foreground">
              Failed to load notification preferences. Please try again.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const prefs = localPrefs ?? preferences;

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      {/* Header */}
      <div className="mb-6 flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate("/notifications")}
          aria-label="Back to notifications"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Notification Preferences</h1>
          <p className="text-sm text-muted-foreground">
            Manage how you receive notifications from CypherPilot.
          </p>
        </div>
      </div>

      {/* Email Notifications Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Email Notifications
          </CardTitle>
          <CardDescription>
            Choose which events trigger email notifications. Emails are only
            sent when SMTP is configured by your administrator.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Master switch */}
          <ToggleRow
            label="Email Notifications"
            description="Master switch — disable to stop all email notifications"
            checked={prefs?.email_enabled ?? true}
            onChange={(v) => handleToggle("email_enabled", v)}
          />

          <Separator className="my-1" />

          {/* Analysis events */}
          <div className="pt-2 pb-1">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Analysis Events
            </p>
          </div>

          <ToggleRow
            label="Analysis Completed"
            description="When an analysis (Failure, Requirement, API Test) finishes successfully"
            checked={prefs?.email_analysis_completed ?? true}
            onChange={(v) => handleToggle("email_analysis_completed", v)}
            disabled={!prefs?.email_enabled}
          />

          <ToggleRow
            label="Analysis Failed"
            description="When an analysis fails with an error"
            checked={prefs?.email_analysis_failed ?? true}
            onChange={(v) => handleToggle("email_analysis_failed", v)}
            disabled={!prefs?.email_enabled}
          />

          <Separator className="my-1" />

          {/* Team events */}
          <div className="pt-2 pb-1">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Team Events
            </p>
          </div>

          <ToggleRow
            label="Team Invitations"
            description="When you are invited to join a team"
            checked={prefs?.email_team_invite ?? true}
            onChange={(v) => handleToggle("email_team_invite", v)}
            disabled={!prefs?.email_enabled}
          />

          <ToggleRow
            label="Removed from Team"
            description="When you are removed from a team"
            checked={prefs?.email_team_removed ?? true}
            onChange={(v) => handleToggle("email_team_removed", v)}
            disabled={!prefs?.email_enabled}
          />

          <ToggleRow
            label="Role Changes"
            description="When your role in a team is updated"
            checked={prefs?.email_team_role_changed ?? true}
            onChange={(v) => handleToggle("email_team_role_changed", v)}
            disabled={!prefs?.email_enabled}
          />
        </CardContent>
      </Card>

      {/* Info note */}
      <p className="mt-4 text-xs text-muted-foreground text-center">
        Changes are saved automatically. In-app notifications are always delivered
        regardless of these settings.
      </p>
    </div>
  );
}
