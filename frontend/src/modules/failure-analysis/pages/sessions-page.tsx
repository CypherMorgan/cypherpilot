/** Sessions page — browse past failure analysis sessions. */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Bug,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Clock,
  Cpu,
  FileQuestion,
  Hash,
  Terminal,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { LoadingState } from "@/components/loading-state";
import { EmptyState } from "@/components/empty-state";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { useFailureSessions } from "@/modules/failure-analysis/hooks/use-failure-analysis";
import type { AnalysisSessionListItem } from "@/modules/failure-analysis/types";

const PAGE_SIZE = 20;

const SOURCE_ICONS: Record<string, typeof Terminal> = {
  plain_text: Terminal,
  ci_log: Terminal,
  stack_trace: Terminal,
  markdown: Terminal,
};

export function FailureSessionsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error } = useFailureSessions(page);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;
  const hasPrev = page > 1;
  const hasNext = data ? page * PAGE_SIZE < data.total : false;

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Page header */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(ROUTES.FAILURE_ANALYSIS)}
          className="shrink-0"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Session History</h1>
          <p className="text-sm text-muted-foreground">
            Browse past failure analysis results.
          </p>
        </div>
      </div>

      {/* Loading */}
      {isLoading && <LoadingState message="Loading sessions..." />}

      {/* Error */}
      {isError && (
        <EmptyState
          icon={<FileQuestion className="h-12 w-12 text-destructive" />}
          title="Failed to load sessions"
          description={
            (error as { message?: string })?.message ??
            "Could not retrieve session list."
          }
        />
      )}

      {/* Empty */}
      {data && data.items.length === 0 && (
        <EmptyState
          icon={<Bug className="h-12 w-12 text-muted-foreground" />}
          title="No sessions yet"
          description="Run your first failure analysis to see past results here."
          action={
            <Button onClick={() => navigate(ROUTES.FAILURE_ANALYSIS)}>
              New Analysis
            </Button>
          }
        />
      )}

      {/* Session list */}
      {data && data.items.length > 0 && (
        <>
          <div className="space-y-2">
            {data.items.map((session) => (
              <SessionRow
                key={session.session_id}
                session={session}
                onClick={() =>
                  navigate(
                    ROUTES.FAILURE_SESSION.replace(
                      ":sessionId",
                      session.session_id,
                    ),
                  )
                }
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 pt-2">
              <Button
                variant="outline"
                size="sm"
                disabled={!hasPrev}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                <ChevronLeft className="mr-1 h-4 w-4" />
                Previous
              </Button>
              <span className="text-xs text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={!hasNext}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            </div>
          )}

          <p className="text-center text-xs text-muted-foreground">
            {data.total} session{data.total !== 1 ? "s" : ""} total
          </p>
        </>
      )}
    </div>
  );
}

// ── Session row ──────────────────────────────────────────────

function SessionRow({
  session,
  onClick,
}: {
  session: AnalysisSessionListItem;
  onClick: () => void;
}) {
  const SourceIcon = SOURCE_ICONS[session.source_type ?? ""] ?? Terminal;

  const date = new Date(session.created_at);
  const dateStr = date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  const timeStr = date.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "group w-full rounded-xl border bg-card p-4 text-left transition-all",
        "hover:border-primary/30 hover:shadow-sm",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
      )}
    >
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border bg-muted/50">
          <SourceIcon className="h-4 w-4 text-muted-foreground" />
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p className="truncate text-sm font-medium">
              {session.input_summary || session.title || "Untitled"}
            </p>
            <StatusBadge status={session.status} />
          </div>

          <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
            {session.source_type && (
              <span className="inline-flex items-center gap-1">
                <Terminal className="h-3 w-3" />
                {session.source_type.replace("_", " ")}
              </span>
            )}
            <span className="inline-flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {dateStr}
            </span>
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {timeStr}
            </span>
            {session.provider && (
              <span className="inline-flex items-center gap-1">
                <Cpu className="h-3 w-3" />
                {session.provider}
              </span>
            )}
            {session.total_tokens != null && (
              <span className="inline-flex items-center gap-1">
                <Hash className="h-3 w-3" />
                {session.total_tokens.toLocaleString()} tokens
              </span>
            )}
          </div>
        </div>

        {/* Chevron */}
        <ChevronRight className="mt-2 h-4 w-4 shrink-0 text-muted-foreground/40 transition-transform group-hover:translate-x-0.5" />
      </div>
    </button>
  );
}

// ── Status badge ─────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    completed: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    failed: "bg-red-500/10 text-red-600 dark:text-red-400",
    processing: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  };

  return (
    <span
      className={cn(
        "shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium capitalize",
        colorMap[status] ?? "bg-muted text-muted-foreground",
      )}
    >
      {status}
    </span>
  );
}
