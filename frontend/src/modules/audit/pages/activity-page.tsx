/**
 * Activity page — global audit log / activity feed.
 *
 * Shows a paginated timeline of all platform events: logins,
 * session creates/deletes, team invites, etc.
 */

import { useEffect, useState, useCallback } from "react";
import { Clock, ChevronLeft, ChevronRight, Loader2, Activity as ActivityIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  getAuditLogs,
  getActionLabel,
  getActionColor,
  type AuditLogEntry,
} from "@/modules/audit/services";

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const secs = Math.floor(diffMs / 1000);
  if (secs < 60) return `${secs}s ago`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function formatTimestamp(dateStr: string): string {
  return new Date(dateStr).toLocaleString();
}

function describeEntry(entry: AuditLogEntry): string {
  const meta = entry.extra_data ?? {};
  switch (entry.action) {
    case "auth.register":
      return `New account: ${meta.username ?? "unknown"}`;
    case "auth.login":
      return `Signed in as ${meta.username ?? "user"}`;
    case "auth.change_password":
      return "Changed their password";
    case "team.create":
      return `Created team "${meta.name ?? "unknown"}"`;
    case "team.invite_member":
      return `Invited ${meta.username ?? "user"} as ${meta.role ?? "member"}`;
    case "team.remove_member":
      return `Removed a member from the team`;
    case "session.create":
      return `Started ${meta.module ?? "analysis"}${meta.title ? `: ${meta.title}` : ""}`;
    case "session.delete":
      return `Deleted a ${meta.module ?? "analysis"} session`;
    default:
      return entry.action;
  }
}

export function ActivityPage() {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pageSize = 20;

  const fetchLogs = useCallback(async (p: number) => {
    setLoading(true);
    setError(null);
    try {
      const result = await getAuditLogs({ page: p, page_size: pageSize });
      setEntries(result.items);
      setTotal(result.total);
    } catch (err: unknown) {
      setError((err as { message?: string })?.message ?? "Failed to load activity");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs(page);
  }, [page, fetchLogs]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Activity</h1>
        <p className="mt-1 text-muted-foreground">
          Platform-wide activity feed — logins, analysis runs, team changes, and more.
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading activity...
        </div>
      ) : error ? (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      ) : entries.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-muted-foreground">
          <ActivityIcon className="mb-3 h-10 w-10 opacity-30" />
          <p className="text-sm">No activity recorded yet.</p>
          <p className="mt-1 text-xs">Actions like logins, analysis runs, and team changes will appear here.</p>
        </div>
      ) : (
        <>
          <div className="space-y-1">
            {entries.map((entry) => (
              <div
                key={entry.id}
                className="flex items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/50"
              >
                <div className="mt-0.5">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${getActionColor(entry.action)}`}
                    >
                      {getActionLabel(entry.action)}
                    </span>
                    <span className="text-xs text-muted-foreground" title={formatTimestamp(entry.created_at)}>
                      {timeAgo(entry.created_at)}
                    </span>
                  </div>
                  <p className="mt-1 text-sm">{describeEntry(entry)}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4">
              <p className="text-sm text-muted-foreground">
                Page {page} of {totalPages} ({total} events)
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
