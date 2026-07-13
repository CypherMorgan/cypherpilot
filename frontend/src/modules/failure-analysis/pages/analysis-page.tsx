/** Main Failure Analysis page.

Provides the complete workflow: paste failure output, analyze, view results.
*/

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, History } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ROUTES } from "@/lib/constants";
import { FailureInput } from "@/modules/failure-analysis/components/failure-input";
import { AnalysisSummary } from "@/modules/failure-analysis/components/analysis-summary";
import { useAnalyzeFailure } from "@/modules/failure-analysis/hooks/use-failure-analysis";
import type { InputSourceType } from "@/modules/failure-analysis/types";

export function FailureAnalysisPage() {
  const navigate = useNavigate();
  const {
    mutateAsync: analyze,
    isPending,
    data: response,
    reset,
  } = useAnalyzeFailure();

  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (content: string, sourceType: InputSourceType) => {
    setError(null);
    try {
      await analyze({
        content,
        source_type: sourceType,
      });
    } catch (err) {
      const message =
        err && typeof err === "object" && "message" in err
          ? (err as { message: string }).message
          : "An unexpected error occurred during analysis.";
      setError(message);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate(ROUTES.HOME)}
              className="shrink-0"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-2xl font-bold tracking-tight">
              Failure Analysis
            </h1>
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
          <p className="mt-1 ml-10 text-sm text-muted-foreground">
            Paste CI/CD logs, stack traces, or error output to get
            AI-powered root cause analysis and suggested fixes.
          </p>
        </div>
      </div>

      {/* Main content */}
      {!response ? (
        <div className="space-y-6">
          <FailureInput
            onSubmit={handleSubmit}
            isSubmitting={isPending}
            error={error}
          />
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={reset}>
              New Analysis
            </Button>
          </div>
          <AnalysisSummary
            result={response.result}
            provider={response.provider}
            model={response.model}
            totalTokens={response.total_tokens}
            latencyMs={response.latency_ms}
          />
        </div>
      )}
    </div>
  );
}
