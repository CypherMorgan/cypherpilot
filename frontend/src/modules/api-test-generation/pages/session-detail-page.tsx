/** Session detail page — view a past API test generation result. */

import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, FileQuestion, History } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ROUTES } from "@/lib/constants";
import { GenerationResults } from "@/modules/api-test-generation/components/generation-results";
import { useApiTestSession } from "@/modules/api-test-generation/hooks/use-api-test-generation";
import { LoadingState } from "@/components/loading-state";
import { EmptyState } from "@/components/empty-state";

export function ApiTestSessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = useApiTestSession(sessionId);

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(ROUTES.API_TEST_GENERATION)}
          className="shrink-0"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">
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
          className="ml-auto gap-1.5 text-xs text-muted-foreground"
        >
          <History className="h-3.5 w-3.5" />
          History
        </Button>
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
