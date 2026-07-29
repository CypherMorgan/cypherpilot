/** Batch Analysis page.

Accepts 2-20 failure inputs in a single request, processes them
sequentially, and displays individual results grouped by batch_id.
*/

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  History,
  Plus,
  Trash2,
  XCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ROUTES } from "@/lib/constants";
import { AnalysisSummary } from "@/modules/failure-analysis/components/analysis-summary";
import { useBatchAnalyzeFailures } from "@/modules/failure-analysis/hooks/use-failure-analysis";
import type {
  BatchAnalysisResponse,
  BatchInputItem,
  InputSourceType,
} from "@/modules/failure-analysis/types";

interface InputEntry {
  id: string;
  content: string;
  sourceType: InputSourceType;
  title: string;
  context: string;
}

function createEntry(overrides?: Partial<InputEntry>): InputEntry {
  return {
    id: crypto.randomUUID(),
    content: "",
    sourceType: "plain_text",
    title: "",
    context: "",
    ...overrides,
  };
}

export function BatchAnalysisPage() {
  const navigate = useNavigate();
  const {
    mutateAsync: runBatch,
    isPending,
    reset,
  } = useBatchAnalyzeFailures();

  const [inputs, setInputs] = useState<InputEntry[]>([
    createEntry(),
    createEntry(),
  ]);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BatchAnalysisResponse | null>(null);
  const [elapsed, setElapsed] = useState(0);

  // Elapsed-time ticker while submitting
  useEffect(() => {
    if (isPending) {
      setElapsed(0);
      const interval = setInterval(() => setElapsed((s) => s + 1), 1000);
      return () => clearInterval(interval);
    }
  }, [isPending]);

  const updateInput = (id: string, patch: Partial<InputEntry>) => {
    setInputs((prev) =>
      prev.map((e) => (e.id === id ? { ...e, ...patch } : e)),
    );
  };

  const removeInput = (id: string) => {
    setInputs((prev) => prev.filter((e) => e.id !== id));
  };

  const addInput = () => {
    setInputs((prev) => [...prev, createEntry()]);
  };

  const canAddMore = inputs.length < 20;
  const canSubmit =
    inputs.length >= 2 &&
    inputs.every((e) => e.content.trim().length > 0) &&
    !isPending;

  const handleSubmit = async () => {
    setError(null);
    const batchInputs: BatchInputItem[] = inputs.map((e) => ({
      content: e.content.trim(),
      source_type: e.sourceType,
      title: e.title.trim() || null,
      context: e.context.trim() || null,
    }));

    try {
      const data = await runBatch({ inputs: batchInputs });
      setResult(data);
    } catch (err) {
      const message =
        err && typeof err === "object" && "message" in err
          ? (err as { message: string }).message
          : "An unexpected error occurred during batch analysis.";
      setError(message);
    }
  };

  const handleReset = () => {
    setResult(null);
    setInputs([createEntry(), createEntry()]);
    setError(null);
    reset();
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate(ROUTES.HOME)}
              className="shrink-0"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-xl font-bold tracking-tight sm:text-2xl">
              Batch Analysis
            </h1>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(ROUTES.FAILURE_SESSIONS)}
              className="ml-auto gap-1.5 text-xs text-muted-foreground shrink-0"
            >
              <History className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">History</span>
            </Button>
          </div>
          <p className="mt-1 ml-0 text-sm text-muted-foreground sm:ml-10">
            Submit 2–20 failure logs at once for AI-powered root cause
            analysis and suggested fixes.
          </p>
        </div>
      </div>

      {/* ── Batch result view ─────────────────────────────────── */}
      {result ? (
        <div className="space-y-6">
          {/* Summary bar */}
          <div className="flex items-center gap-4 rounded-xl border bg-card p-4">
            <div className="flex items-center gap-2 text-sm">
              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
              <span className="font-medium">
                {result.completed} / {result.total}
              </span>
              <span className="text-muted-foreground">completed</span>
            </div>
            {result.failed > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <XCircle className="h-5 w-5 text-destructive" />
                <span className="font-medium text-destructive">
                  {result.failed}
                </span>
                <span className="text-muted-foreground">failed</span>
              </div>
            )}
            <span className="ml-auto text-xs text-muted-foreground">
              Batch ID: {result.batch_id.slice(0, 8)}&hellip;
            </span>
          </div>

          {/* Individual results */}
          {result.results.map((item) => (
            <div
              key={item.index}
              className="rounded-xl border bg-card"
            >
              {/* Result header */}
              <div className="flex items-center justify-between border-b px-4 py-3">
                <div className="flex items-center gap-2">
                  {item.status === "completed" ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  ) : (
                    <XCircle className="h-4 w-4 text-destructive" />
                  )}
                  <span className="text-sm font-medium">
                    Input #{item.index + 1}
                  </span>
                  {item.session_id && (
                    <Button
                      variant="link"
                      size="sm"
                      className="h-auto p-0 text-xs"
                      onClick={() =>
                        navigate(
                          `/failures/sessions/${item.session_id}`,
                        )
                      }
                    >
                      View Session
                    </Button>
                  )}
                </div>
                {item.status === "completed" && (
                  <span className="text-xs text-muted-foreground">
                    {item.latency_ms ? `${(item.latency_ms / 1000).toFixed(1)}s` : ""}
                    {item.total_tokens ? ` · ${item.total_tokens} tokens` : ""}
                  </span>
                )}
              </div>

              {/* Result body */}
              <div className="p-4">
                {item.status === "completed" && item.result ? (
                  <AnalysisSummary
                    result={item.result}
                    provider={item.provider}
                    model={item.model}
                    totalTokens={item.total_tokens}
                    latencyMs={item.latency_ms}
                  />
                ) : (
                  <div className="flex items-start gap-2 text-sm text-destructive">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>{item.error || "Analysis failed."}</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          <div className="flex gap-2">
            <Button variant="outline" onClick={handleReset}>
              New Batch
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate(ROUTES.FAILURE_SESSIONS)}
            >
              View All Sessions
            </Button>
          </div>
        </div>
      ) : (
        /* ── Batch input form ─────────────────────────────────── */
        <div className="space-y-6">
          {error && (
            <div className="rounded-md border border-destructive/50 bg-destructive/5 p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-destructive">
                    Batch Analysis Failed
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

          {/* Input entries */}
          <div className="space-y-4">
            {inputs.map((entry, index) => (
              <div
                key={entry.id}
                className="rounded-xl border bg-card p-4"
              >
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="text-sm font-semibold">
                    Input #{index + 1}
                  </h3>
                  {inputs.length > 2 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeInput(entry.id)}
                      disabled={isPending}
                    >
                      <Trash2 className="mr-1 h-3.5 w-3.5" />
                      Remove
                    </Button>
                  )}
                </div>

                <div className="space-y-3">
                  {/* Title */}
                  <div>
                    <Label
                      htmlFor={`title-${entry.id}`}
                      className="text-xs"
                    >
                      Title (optional)
                    </Label>
                    <Input
                      id={`title-${entry.id}`}
                      placeholder="e.g. Login test failure"
                      value={entry.title}
                      onChange={(e) =>
                        updateInput(entry.id, {
                          title: e.target.value,
                        })
                      }
                      disabled={isPending}
                    />
                  </div>

                  {/* Content */}
                  <div>
                    <Label
                      htmlFor={`content-${entry.id}`}
                      className="text-xs"
                    >
                      Failure Output *
                    </Label>
                    <Textarea
                      id={`content-${entry.id}`}
                      placeholder="Paste CI/CD log, stack trace, or error output..."
                      rows={5}
                      value={entry.content}
                      onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                        updateInput(entry.id, {
                          content: e.target.value,
                        })
                      }
                      disabled={isPending}
                    />
                  </div>

                  {/* Source type + Context row */}
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div>
                      <Label
                        htmlFor={`source-${entry.id}`}
                        className="text-xs"
                      >
                        Source Type
                      </Label>
                      <Select
                        value={entry.sourceType}
                        onValueChange={(
                          v: InputSourceType,
                        ) =>
                          updateInput(entry.id, {
                            sourceType: v,
                          })
                        }
                        disabled={isPending}
                      >
                        <SelectTrigger
                          id={`source-${entry.id}`}
                        >
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="plain_text">
                            Plain Text
                          </SelectItem>
                          <SelectItem value="markdown">
                            Markdown
                          </SelectItem>
                          <SelectItem value="ci_log">
                            CI Log
                          </SelectItem>
                          <SelectItem value="stack_trace">
                            Stack Trace
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label
                        htmlFor={`context-${entry.id}`}
                        className="text-xs"
                      >
                        Context (optional)
                      </Label>
                      <Input
                        id={`context-${entry.id}`}
                        placeholder="e.g. Python 3.11, pytest, Linux"
                        value={entry.context}
                        onChange={(e) =>
                          updateInput(entry.id, {
                            context: e.target.value,
                          })
                        }
                        disabled={isPending}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Add more button */}
          <div className="flex justify-center">
            {canAddMore ? (
              <Button
                variant="outline"
                size="sm"
                onClick={addInput}
                disabled={isPending}
              >
                <Plus className="mr-1.5 h-4 w-4" />
                Add Input ({inputs.length}/20)
              </Button>
            ) : (
              <p className="text-xs text-muted-foreground">
                Maximum of 20 inputs reached.
              </p>
            )}
          </div>

          {/* Submit */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-xs text-muted-foreground">
              {inputs.length} input(s). All inputs must have
              failure output filled in.
            </p>
            <Button
              onClick={handleSubmit}
              disabled={!canSubmit}
              size="lg"
              className="w-full sm:w-auto"
            >
              {isPending
                ? `Analyzing... (${elapsed}s)`
                : `Analyze ${inputs.length} Inputs`}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
