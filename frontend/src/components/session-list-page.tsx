/** Shared parameterized session list page.
 *
 * Eliminates ~550 lines of duplicated code across the 3 module
 * session-list pages. Each page becomes a thin ~25-line wrapper.
 */

import { useState, useMemo, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Clock,
  Cpu,
  Hash,
  Search,
  Trash2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { LoadingState } from "@/components/loading-state";
import { EmptyState } from "@/components/empty-state";
import { SessionSearch } from "@/components/session-search";
import { cn } from "@/lib/utils";
import type { UseMutationResult } from "@tanstack/react-query";

// ── Minimal interface every session list item must satisfy ─────

export interface SessionListItemBase {
  session_id: string;
  title?: string | null;
  status: string;
  provider?: string | null;
  total_tokens?: number;
  created_at: string;
}

// ── Props ──────────────────────────────────────────────────────

export interface SessionListPageProps<T extends SessionListItemBase> {
  /** TanStack Query result for fetching sessions. */
  useSessions: (
    page: number,
  ) => {
    data?: { items: T[]; total: number };
    isLoading: boolean;
    isError: boolean;
    error: unknown;
  };

  /** TanStack Query mutation for deleting a session. */
  useDeleteSession: () => UseMutationResult<unknown, Error, string>;

  /** Back-navigation route (e.g. ROUTES.FAILURE_ANALYSIS). */
  backRoute: string;

  /** Session detail route template with ":sessionId" placeholder. */
  sessionRoute: string;

  /** Page title. */
  title: string;

  /** Page description. */
  description: string;

  /** Text shown for the empty state. */
  emptyTitle: string;
  emptyDescription: string;

  /** Label for the empty-state CTA button. */
  emptyActionLabel: string;

  /** Icon shown in the empty state. */
  emptyIcon: ReactNode;

  /** Page size for pagination (default 20). */
  pageSize?: number;

  /** Render a single session row. */
  renderRow: (session: T, options: { onClick: () => void; onDelete: (session: T) => void }) => ReactNode;
}

// ── Component ──────────────────────────────────────────────────

export function SessionListPage<T extends SessionListItemBase>({
  useSessions,
  useDeleteSession,
  backRoute,
  sessionRoute,
  title,
  description,
  emptyTitle,
  emptyDescription,
  emptyActionLabel,
  emptyIcon,
  pageSize = 20,
  renderRow,
}: SessionListPageProps<T>) {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error } = useSessions(page);
  const deleteMutation = useDeleteSession();
  const [deleteTarget, setDeleteTarget] = useState<T | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;
  const hasPrev = page > 1;
  const hasNext = data ? page * pageSize < data.total : false;

  // Client-side search & filter
  const filteredItems = useMemo(() => {
    if (!data) return [];
    let items = data.items;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      items = items.filter((s) => {
        const titleMatch = (s.title || "").toLowerCase().includes(q);
        const extraMatch = "spec_title" in s && s.spec_title
          ? (s.spec_title as string).toLowerCase().includes(q)
          : "input_summary" in s && s.input_summary
            ? (s.input_summary as string).toLowerCase().includes(q)
            : false;
        return titleMatch || extraMatch;
      });
    }
    if (statusFilter !== "all") {
      items = items.filter((s) => s.status === statusFilter);
    }
    return items;
  }, [data, searchQuery, statusFilter]);

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Page header */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(backRoute)}
          className="shrink-0"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>

      {/* Search & filter bar */}
      {data && data.items.length > 0 && (
        <SessionSearch
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          total={data.total}
          filtered={filteredItems.length}
        />
      )}

      {/* Loading */}
      {isLoading && <LoadingState message="Loading sessions..." />}

      {/* Error */}
      {isError && (
        <EmptyState
          icon={<Search className="h-12 w-12 text-destructive" />}
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
          icon={emptyIcon}
          title={emptyTitle}
          description={emptyDescription}
          action={
            <Button onClick={() => navigate(backRoute)}>
              {emptyActionLabel}
            </Button>
          }
        />
      )}

      {/* No results from search/filter */}
      {data && data.items.length > 0 && filteredItems.length === 0 && (
        <EmptyState
          icon={<Search className="h-12 w-12 text-muted-foreground" />}
          title="No matching sessions"
          description="Try a different search term or status filter."
        />
      )}

      {/* Session list */}
      {data && data.items.length > 0 && filteredItems.length > 0 && (
        <>
          <div className="space-y-2">
            {filteredItems.map((session) => (
              <div key={session.session_id}>
                {renderRow(session, {
                  onClick: () =>
                    navigate(
                      sessionRoute.replace(
                        ":sessionId",
                        session.session_id,
                      ),
                    ),
                  onDelete: setDeleteTarget,
                })}
              </div>
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

      {/* Delete confirmation dialog */}
      <AlertDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this session?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. The session will be permanently
              removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deleteTarget) {
                  deleteMutation.mutate(deleteTarget.session_id, {
                    onSuccess: () => setDeleteTarget(null),
                  });
                }
              }}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// ── Shared session row helpers ──────────────────────────────────

interface SessionRowConfig {
  /** Icon element for the row (e.g. <FileText />, <Bug />). */
  icon: ReactNode;
  /** Title to display (already resolved from session data). */
  title: string;
  /** Status string. */
  status: string;
  /** Optional source type label. */
  sourceTypeLabel?: string;
  /** Optional extra info lines (e.g. endpoint count). */
  extraInfo?: { icon: ReactNode; label: string }[];
  /** Provider string. */
  provider?: string | null;
  /** Total tokens. */
  totalTokens?: number;
  /** Created-at timestamp. */
  createdAt: string;
}

/** Renders a uniform session row with the given config. */
export function SessionRow({ config, onClick, onDelete }: {
  config: SessionRowConfig;
  onClick: () => void;
  onDelete: () => void;
}) {
  const date = new Date(config.createdAt);
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
          {config.icon}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p className="truncate text-sm font-medium">{config.title}</p>
            <StatusBadge status={config.status} />
          </div>

          <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
            {config.sourceTypeLabel && (
              <span className="inline-flex items-center gap-1">
                <Search className="h-3 w-3" />
                {config.sourceTypeLabel}
              </span>
            )}
            {config.extraInfo?.map((info, i) => (
              <span key={i} className="inline-flex items-center gap-1">
                {info.icon}
                {info.label}
              </span>
            ))}
            <span className="inline-flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {dateStr}
            </span>
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {timeStr}
            </span>
            {config.provider && (
              <span className="inline-flex items-center gap-1">
                <Cpu className="h-3 w-3" />
                {config.provider}
              </span>
            )}
            {config.totalTokens != null && (
              <span className="inline-flex items-center gap-1">
                <Hash className="h-3 w-3" />
                {config.totalTokens.toLocaleString()} tokens
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground/40 opacity-0 transition-all hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
            title="Delete session"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
          <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground/40 transition-transform group-hover:translate-x-0.5" />
        </div>
      </div>
    </button>
  );
}

// ── Status badge ─────────────────────────────────────────────

export function StatusBadge({ status }: { status: string }) {
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
