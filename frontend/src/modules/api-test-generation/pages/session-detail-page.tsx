/** Session detail page — view a past API test generation result. */

import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, FileQuestion, History, Trash2 } from "lucide-react";

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
import { GenerationResults } from "@/modules/api-test-generation/components/generation-results";
import { useApiTestSession, useDeleteApiTestSession } from "@/modules/api-test-generation/hooks/use-api-test-generation";
import { LoadingState } from "@/components/loading-state";
import { EmptyState } from "@/components/empty-state";
import { SessionExportMenu } from "@/components/session-export-menu";

export function ApiTestSessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = useApiTestSession(sessionId);
  const deleteMutation = useDeleteApiTestSession();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(ROUTES.API_TEST_GENERATION)}
          className="shrink-0"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-xl font-bold tracking-tight sm:text-2xl">
          Generation Session
        </h1>
        {sessionId && (
          <code className="rounded bg-muted px-2 py-0.5 text-xs font-mono text-muted-foreground">
            {sessionId.slice(0, 8)}...
          </code>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(ROUTES.API_TEST_SESSIONS)}
          className="ml-auto gap-1.5 text-xs text-muted-foreground shrink-0"
        >
          <History className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">History</span>
        </Button>
        {sessionId && (
          <SessionExportMenu
            exportPath={`/openapi/sessions/${sessionId}/export`}
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
                This action cannot be undone. The generation session will be
                permanently removed.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => {
                  if (sessionId) {
                    deleteMutation.mutate(sessionId, {
                      onSuccess: () => navigate(ROUTES.API_TEST_SESSIONS),
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
            "Could not load this generation session. It may have been deleted."
          }
          action={
            <Button variant="outline" onClick={() => navigate(ROUTES.API_TEST_SESSIONS)}>
              Back to Sessions
            </Button>
          }
        />
      )}

      {/* Results */}
      {data && <GenerationResults result={data} />}
    </div>
  );
}
