/** Session detail page — view a past failure analysis result. */

import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, FileQuestion, History, Paperclip, Trash2 } from "lucide-react";

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
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { ROUTES } from "@/lib/constants";
import { AnalysisSummary } from "@/modules/failure-analysis/components/analysis-summary";
import { useFailureSession, useDeleteFailureSession } from "@/modules/failure-analysis/hooks/use-failure-analysis";
import { LoadingState } from "@/components/loading-state";
import { EmptyState } from "@/components/empty-state";
import { SessionExportMenu } from "@/components/session-export-menu";

export function FailureSessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = useFailureSession(sessionId);
  const deleteMutation = useDeleteFailureSession();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(ROUTES.FAILURE_ANALYSIS)}
          className="shrink-0"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-xl font-bold tracking-tight sm:text-2xl">
          Failure Analysis Session
        </h1>
        {sessionId && (
          <code className="rounded bg-muted px-2 py-0.5 text-xs font-mono text-muted-foreground">
            {sessionId.slice(0, 8)}...
          </code>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(ROUTES.FAILURE_SESSIONS)}
          className="ml-auto gap-1.5 text-xs text-muted-foreground shrink-0"
        >
          <History className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">History</span>
        </Button>
        {sessionId && (
          <SessionExportMenu
            exportPath={`/failures/sessions/${sessionId}/export`}
            disabled={!data}
          />
        )}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="gap-1.5 text-xs text-destructive/80 hover:text-destructive shrink-0"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Delete</span>
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete this session?</AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. The analysis session will be
                permanently removed.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => {
                  if (sessionId) {
                    deleteMutation.mutate(sessionId, {
                      onSuccess: () => navigate(ROUTES.FAILURE_SESSIONS),
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

      {/* Loading state */}
      {isLoading && <LoadingState message="Loading session..." fullPage />}

      {/* Error state */}
      {isError && (
        <EmptyState
          icon={<FileQuestion className="h-12 w-12 text-destructive" />}
          title="Session Not Found"
          description={
            (error as { message?: string })?.message ??
            "Could not load this analysis session. It may have been deleted."
          }
          action={
            <Button variant="outline" onClick={() => navigate(ROUTES.HOME)}>
              Back to Dashboard
            </Button>
          }
        />
      )}

      {/* Results */}
      {data && (
        <div className="space-y-6">
          {data.artifacts && data.artifacts.length > 0 && (
            <div className="rounded-xl border bg-card p-4">
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold">
                <Paperclip className="h-4 w-4" />
                Attached Artifacts ({data.artifacts.length})
              </h3>
              <ul className="space-y-1.5">
                {data.artifacts.map((a, i) => (
                  <li key={i} className="flex items-center gap-3 text-sm">
                    <span className="inline-flex h-6 w-6 items-center justify-center rounded bg-muted text-[10px] font-medium text-muted-foreground uppercase">
                      {a.file_type === "image" ? "IMG" : a.file_type === "text" ? "TXT" : "BIN"}
                    </span>
                    <span className="font-medium">{a.filename}</span>
                    <span className="text-xs text-muted-foreground">
                      {(a.file_size / 1024).toFixed(1)} KB
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <AnalysisSummary
            result={data.result}
            provider={data.provider}
            model={data.model}
            totalTokens={data.total_tokens}
            latencyMs={data.latency_ms}
          />
        </div>
      )}
    </div>
  );
}
