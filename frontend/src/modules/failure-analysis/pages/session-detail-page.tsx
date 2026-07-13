/** Session detail page — view a past failure analysis result. */

import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, FileQuestion, History } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ROUTES } from "@/lib/constants";
import { AnalysisSummary } from "@/modules/failure-analysis/components/analysis-summary";
import { useFailureSession } from "@/modules/failure-analysis/hooks/use-failure-analysis";
import { LoadingState } from "@/components/loading-state";
import { EmptyState } from "@/components/empty-state";

export function FailureSessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = useFailureSession(sessionId);

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(ROUTES.FAILURE_ANALYSIS)}
          className="shrink-0"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">
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
        <AnalysisSummary
          result={data.result}
          provider={data.provider}
          model={data.model}
          totalTokens={data.total_tokens}
          latencyMs={data.latency_ms}
        />
      )}
    </div>
  );
}
