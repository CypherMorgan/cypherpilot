/**
 * Usage Analytics — home-page dashboard widget.
 *
 * Shows the authenticated user's aggregate stats: total sessions,
 * success rate, token/latency totals, breakdowns by module and status,
 * a 14-day activity chart, and recent failures.
 *
 * Signed-out users get a sign-in hint (the endpoint requires auth);
 * backend-unavailable states degrade gracefully like the rest of the app.
 */

import { Link } from "react-router-dom";
import {
  AlertTriangle,
  BarChart3,
  Clock,
  Coins,
  CheckCircle2,
  Loader2,
  XCircle,
} from "lucide-react";

import { useAuth } from "@/hooks/use-auth";
import { useDashboardStats } from "@/hooks/use-dashboard";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { ApiError, DashboardStats } from "@/types/api";

const MODULE_LABELS: Record<string, string> = {
  "requirement-analysis": "Requirement Analysis",
  "api-test-generation": "API Test Generation",
  "failure-analysis": "Failure Analysis",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  processing: "Processing",
  completed: "Completed",
  failed: "Failed",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-muted-foreground/50",
  processing: "bg-amber-500",
  completed: "bg-emerald-500",
  failed: "bg-destructive",
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function isUnauthorized(err: unknown): boolean {
  return !!err && typeof err === "object" && (err as ApiError).status === 401;
}

export function UsageAnalytics() {
  const { isAuthenticated } = useAuth();
  const { data, isLoading, isError, error } = useDashboardStats();

  return (
    <section>
      <div className="mb-4 flex items-center gap-2">
        <BarChart3 className="h-4 w-4 text-muted-foreground" />
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          Usage Analytics
        </h2>
      </div>

      {!isAuthenticated && (
        <div className="rounded-xl border bg-card p-6 text-center">
          <BarChart3 className="mx-auto h-8 w-8 text-muted-foreground/60" />
          <p className="mt-2 text-sm font-medium">Sign in to view usage analytics</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Your sessions, success rate, and activity over the last 14 days.
          </p>
          <Link
            to={ROUTES.LOGIN}
            className="mt-4 inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Sign in
          </Link>
        </div>
      )}

      {isAuthenticated && isLoading && (
        <div className="flex items-center justify-center gap-2 rounded-xl border bg-card p-8 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading analytics...
        </div>
      )}

      {isAuthenticated && isError && !isUnauthorized(error) && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-6 text-center">
          <AlertTriangle className="mx-auto h-6 w-6 text-destructive/60" />
          <p className="mt-2 text-sm font-medium text-destructive">
            Unable to load analytics
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            The backend could not be reached or returned an error.
          </p>
        </div>
      )}

      {isAuthenticated && isError && isUnauthorized(error) && (
        <div className="rounded-xl border bg-card p-6 text-center">
          <BarChart3 className="mx-auto h-8 w-8 text-muted-foreground/60" />
          <p className="mt-2 text-sm font-medium">Sign in to view usage analytics</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Your session has expired or you are signed out.
          </p>
          <Link
            to={ROUTES.LOGIN}
            className="mt-4 inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Sign in
          </Link>
        </div>
      )}

      {isAuthenticated && data && !isError && <StatsBoard stats={data} />}
    </section>
  );
}

function StatsBoard({ stats }: { stats: DashboardStats }) {
  const maxDay = Math.max(1, ...stats.usage_over_time.map((p) => p.sessions));

  return (
    <div className="space-y-4">
      {/* ── Stat cards ─────────────────────────────────────── */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={<BarChart3 className="h-4 w-4" />}
          label="Total Sessions"
          value={stats.total_sessions.toLocaleString()}
        />
        <StatCard
          icon={<CheckCircle2 className="h-4 w-4" />}
          label="Success Rate"
          value={stats.total_sessions === 0 ? "—" : `${Math.round(stats.success_rate * 100)}%`}
          meta={
            stats.sessions_by_status.failed > 0
              ? `${stats.sessions_by_status.failed} failed`
              : undefined
          }
        />
        <StatCard
          icon={<Coins className="h-4 w-4" />}
          label="Tokens Used"
          value={stats.total_tokens.toLocaleString()}
        />
        <StatCard
          icon={<Clock className="h-4 w-4" />}
          label="Avg Latency"
          value={stats.total_sessions === 0 ? "—" : `${stats.avg_latency_ms}ms`}
          meta={`${stats.total_latency_ms.toLocaleString()}ms total`}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* ── Breakdowns ───────────────────────────────────── */}
        <div className="rounded-xl border bg-card p-4">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Sessions by module
          </h3>
          <div className="space-y-2.5">
            {Object.entries(stats.sessions_by_type).map(([key, count]) => (
              <BreakdownRow
                key={key}
                label={MODULE_LABELS[key] ?? key}
                count={count}
                total={stats.total_sessions}
                color="bg-primary"
              />
            ))}
          </div>
        </div>

        <div className="rounded-xl border bg-card p-4">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Sessions by status
          </h3>
          <div className="space-y-2.5">
            {Object.entries(stats.sessions_by_status).map(([key, count]) => (
              <BreakdownRow
                key={key}
                label={STATUS_LABELS[key] ?? key}
                count={count}
                total={stats.total_sessions}
                color={STATUS_COLORS[key] ?? "bg-muted-foreground/50"}
              />
            ))}
          </div>
        </div>
      </div>

      {/* ── 14-day activity chart ──────────────────────────── */}
      <div className="rounded-xl border bg-card p-4">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Activity — last 14 days
        </h3>
        <div className="flex h-28 items-end gap-1.5">
          {stats.usage_over_time.map((point) => (
            <div
              key={point.date}
              className="group relative flex h-full flex-1 flex-col justify-end"
              title={`${point.sessions} session${point.sessions === 1 ? "" : "s"} on ${point.date}`}
            >
              <div
                className={cn(
                  "w-full rounded-t-sm bg-primary/70 transition-colors group-hover:bg-primary",
                  point.sessions === 0 && "bg-muted/40",
                )}
                style={{ height: point.sessions === 0 ? "2px" : `${Math.max(8, (point.sessions / maxDay) * 100)}%` }}
              />
              <span className="mt-1 hidden text-center text-[9px] text-muted-foreground sm:block">
                {formatDate(point.date)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Recent failures ────────────────────────────────── */}
      <div className="rounded-xl border bg-card p-4">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Recent failures
        </h3>
        {stats.recent_failures.length === 0 ? (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            No failed sessions in the last 14 days.
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {stats.recent_failures.map((failure) => (
              <li key={failure.session_id} className="flex items-start gap-3 py-2.5">
                <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">
                    {failure.title || "Untitled session"}
                  </p>
                  <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">
                    {failure.error_message || "No error details"}
                  </p>
                </div>
                <div className="shrink-0 text-right">
                  <span className="text-[11px] text-muted-foreground">
                    {MODULE_LABELS[failure.analysis_type] ?? failure.analysis_type}
                  </span>
                  <span className="block text-[11px] text-muted-foreground/70">
                    {formatDate(failure.created_at)}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  meta,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  meta?: string;
}) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {icon}
        <span>{label}</span>
      </div>
      <p className="mt-1.5 text-lg font-semibold tracking-tight">{value}</p>
      {meta && <p className="mt-0.5 text-[11px] text-muted-foreground">{meta}</p>}
    </div>
  );
}

function BreakdownRow({
  label,
  count,
  total,
  color,
}: {
  label: string;
  count: number;
  total: number;
  color: string;
}) {
  const pct = total === 0 ? 0 : (count / total) * 100;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{count.toLocaleString()}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full rounded-full", color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
