/** Main Failure Analysis page.

Provides the complete workflow: paste failure output, attach artifact files,
analyze, view results.
*/

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertCircle, ArrowLeft, History, Paperclip, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ROUTES } from "@/lib/constants";
import { FailureInput } from "@/modules/failure-analysis/components/failure-input";
import { AnalysisSummary } from "@/modules/failure-analysis/components/analysis-summary";
import { FileUpload, type FileEntry } from "@/modules/failure-analysis/components/file-upload";
import {
  useAnalyzeFailure,
  useAnalyzeFailureWithArtifacts,
} from "@/modules/failure-analysis/hooks/use-failure-analysis";
import type { AnalysisResponse, InputSourceType } from "@/modules/failure-analysis/types";

export function FailureAnalysisPage() {
  const navigate = useNavigate();
  const {
    mutateAsync: analyze,
    isPending,
    reset: resetAnalyze,
  } = useAnalyzeFailure();
  const { mutateAsync: analyzeWithArtifacts, isPending: isArtifactPending, reset: resetArtifact } =
    useAnalyzeFailureWithArtifacts();

  const [content, setContent] = useState("");
  const [sourceType, setSourceType] = useState<InputSourceType>("plain_text");
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [artifacts, setArtifacts] = useState<FileEntry[]>([]);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [elapsed, setElapsed] = useState(0);

  const isSubmitting = isPending || isArtifactPending;
  const canSubmit = (content.trim().length > 0 || artifacts.length > 0) && !isSubmitting;

  // Elapsed-time ticker while submitting
  useEffect(() => {
    if (isSubmitting) {
      setElapsed(0);
      const interval = setInterval(() => setElapsed((s) => s + 1), 1000);
      return () => clearInterval(interval);
    }
  }, [isSubmitting]);

  const handleSubmit = async () => {
    setError(null);
    try {
      let data: AnalysisResponse;
      if (artifacts.length > 0) {
        const files = artifacts
          .filter((e) => !e.error)
          .map((e) => e.file);
        data = await analyzeWithArtifacts({
          content: content.trim(),
          sourceType,
          files,
        });
      } else {
        data = await analyze({
          content: content.trim(),
          source_type: sourceType,
        });
      }
      setResult(data);
      setArtifacts([]);
    } catch (err) {
      const message =
        err && typeof err === "object" && "message" in err
          ? (err as { message: string }).message
          : "An unexpected error occurred during analysis.";
      setError(message);
    }
  };

  const handleReset = () => {
    setResult(null);
    setContent("");
    setSourceType("plain_text");
    setTitle("");
    setError(null);
    setArtifacts([]);
    resetAnalyze();
    resetArtifact();
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
      {!result ? (
        <div className="space-y-6">
          <FailureInput
            content={content}
            onContentChange={setContent}
            sourceType={sourceType}
            onSourceTypeChange={setSourceType}
            title={title}
            onTitleChange={setTitle}
            onSubmit={handleSubmit}
            disabled={isSubmitting}
          />

          {/* Artifact file upload */}
          <div className="rounded-xl border bg-card p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Paperclip className="h-4 w-4" />
              Attach Artifacts
              <span className="text-xs font-normal text-muted-foreground/60">
                (optional — screenshots, JSON logs, HTML page source, .log files, etc.)
              </span>
            </div>
            <FileUpload
              files={artifacts}
              onFilesChange={setArtifacts}
              disabled={isSubmitting}
            />
          </div>

          {/* Error message with retry */}
          {error && (
            <div className="rounded-md border border-destructive/50 bg-destructive/5 p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-destructive">
                    Analysis Failed
                  </p>
                  <p className="mt-0.5 text-sm text-destructive/80">
                    {error}
                  </p>
                </div>
              </div>
              <div className="mt-3 flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSubmit}
                  disabled={!canSubmit}
                >
                  <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                  Retry
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setError(null)}
                >
                  Dismiss
                </Button>
              </div>
            </div>
          )}

          {/* Submit — at the bottom, below both text input and file upload */}
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              {artifacts.length > 0
                ? `${artifacts.length} file(s) attached. Click "Analyze Failure" to run analysis.`
                : "The failure output is analyzed by AI to identify root causes, suggest fixes, and assess impact."}
            </p>
            <Button onClick={handleSubmit} disabled={!canSubmit} size="lg">
              {isSubmitting ? `Analyzing... (${elapsed}s)` : "Analyze Failure"}
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleReset}>
              New Analysis
            </Button>
          </div>
          {result.artifacts && result.artifacts.length > 0 && (
            <ArtifactSummary artifacts={result.artifacts} />
          )}
          <AnalysisSummary
            result={result.result}
            provider={result.provider}
            model={result.model}
            totalTokens={result.total_tokens}
            latencyMs={result.latency_ms}
          />
        </div>
      )}
    </div>
  );
}

/** Displays a summary of attached artifacts in the analysis result. */
function ArtifactSummary({
  artifacts,
}: {
  artifacts: Array<{ filename: string; file_type: string; file_size: number; content_preview?: string }>;
}) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold">
        <Paperclip className="h-4 w-4" />
        Attached Artifacts ({artifacts.length})
      </h3>
      <ul className="space-y-1.5">
        {artifacts.map((a, i) => (
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
  );
}
