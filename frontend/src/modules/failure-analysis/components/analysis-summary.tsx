/** Failure analysis results display.

Renders the complete analysis result with root causes, suggested
fixes, affected components, and other sections in a structured layout.
*/

import {
  Bug,
  Cpu,
  FileCode,
  FlaskConical,
  Lightbulb,
  ShieldAlert,
  Target,
  Wrench,
} from "lucide-react";

import { ExportActions } from "@/components/export-actions";
import { SectionCard } from "@/components/section-card";
import {
  formatAsJson,
  formatAsMarkdown,
} from "@/modules/failure-analysis/utils/export";
import type {
  AffectedComponent,
  FailureAnalysisResult,
  RootCause,
  SuggestedFix,
  TestFailure,
} from "@/modules/failure-analysis/types";

interface AnalysisSummaryProps {
  result: FailureAnalysisResult;
  provider?: string | null;
  model?: string | null;
  totalTokens?: number;
  latencyMs?: number;
}

// ── Severity badges ───────────────────────────────────────────────

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  high: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
  medium: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
  low: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
};

function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
        SEVERITY_COLORS[severity] ?? SEVERITY_COLORS.medium
      }`}
    >
      {severity}
    </span>
  );
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  high: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  medium: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  low: "bg-slate-100 text-slate-600 dark:bg-slate-800/30 dark:text-slate-400",
};

function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
        PRIORITY_COLORS[priority] ?? PRIORITY_COLORS.medium
      }`}
    >
      {priority}
    </span>
  );
}

// ── Content renderers ─────────────────────────────────────────────

function RootCauseCard({ cause }: { cause: RootCause }) {
  return (
    <div className="rounded-md border bg-card/50 p-3 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="font-mono text-xs text-muted-foreground">
            {cause.id}
          </span>
          <h4 className="mt-0.5 font-medium">{cause.title}</h4>
        </div>
        <SeverityBadge severity={cause.severity} />
      </div>

      <p className="mt-2 text-muted-foreground">{cause.description}</p>

      <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
        <span>
          <strong>Category:</strong>{" "}
          <code className="rounded bg-muted px-1 py-0.5">{cause.category}</code>
        </span>
        {cause.failing_file && (
          <span>
            <strong>File:</strong>{" "}
            <code className="rounded bg-muted px-1 py-0.5">
              {cause.failing_file}
              {cause.failing_line ? `:${cause.failing_line}` : ""}
            </code>
          </span>
        )}
      </div>

      {cause.error_message && (
        <div className="mt-2 rounded-md bg-red-500/5 p-2 font-mono text-xs text-red-600 dark:text-red-400">
          <pre className="whitespace-pre-wrap">{cause.error_message}</pre>
        </div>
      )}

      {cause.stack_trace && cause.stack_trace.length > 0 && (
        <div className="mt-2 rounded-md bg-muted/50 p-2">
          <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Stack trace
          </p>
          {cause.stack_trace.map((frame, i) => (
            <p key={i} className="font-mono text-[11px] text-muted-foreground">
              <span className="text-foreground/60">{frame.file}:{frame.line}</span>
              {frame.function && (
                <span className="text-foreground/40"> in {frame.function}</span>
              )}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

function FixCard({ fix }: { fix: SuggestedFix }) {
  return (
    <div className="rounded-md border bg-card/50 p-3 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="font-mono text-xs text-muted-foreground">
            {fix.id}
          </span>
          <h4 className="mt-0.5 font-medium">{fix.description}</h4>
        </div>
        <PriorityBadge priority={fix.priority} />
      </div>

      <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
        <span>
          <strong>Root cause:</strong>{" "}
          <code className="rounded bg-muted px-1 py-0.5">{fix.root_cause_id}</code>
        </span>
        {fix.effort_estimate && (
          <span>
            <strong>Effort:</strong> {fix.effort_estimate}
          </span>
        )}
      </div>

      {fix.related_files && fix.related_files.length > 0 && (
        <div className="mt-2">
          <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Files to modify
          </p>
          <ul className="mt-1 space-y-0.5">
            {fix.related_files.map((file) => (
              <li key={file}>
                <code className="rounded bg-muted px-1 py-0.5 font-mono text-[11px]">
                  {file}
                </code>
              </li>
            ))}
          </ul>
        </div>
      )}

      {fix.code_example && (
        <div className="mt-2 rounded-md bg-muted/50 p-2">
          <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Code fix
          </p>
          <pre className="whitespace-pre-wrap font-mono text-[11px]">
            {fix.code_example}
          </pre>
        </div>
      )}
    </div>
  );
}

function TestFailureCard({ failure }: { failure: TestFailure }) {
  return (
    <div className="rounded-md border border-red-500/20 bg-red-500/5 p-3 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="font-mono text-xs text-muted-foreground">
            {failure.id}
          </span>
          <h4 className="mt-0.5 font-medium">{failure.test_name}</h4>
        </div>
      </div>

      <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
        {failure.test_file && (
          <span>
            <strong>File:</strong>{" "}
            <code className="rounded bg-muted px-1 py-0.5">{failure.test_file}</code>
          </span>
        )}
        {failure.duration_seconds !== undefined && failure.duration_seconds !== null && (
          <span>
            <strong>Duration:</strong> {failure.duration_seconds}s
          </span>
        )}
        {failure.retry_count !== undefined && failure.retry_count > 0 && (
          <span>
            <strong>Retries:</strong> {failure.retry_count}
          </span>
        )}
      </div>

      {failure.error_message && (
        <div className="mt-2 rounded-md bg-muted/50 p-2 font-mono text-[11px] text-muted-foreground">
          <pre className="whitespace-pre-wrap">{failure.error_message}</pre>
        </div>
      )}
    </div>
  );
}

function AffectedComponentsTable({
  components,
}: {
  components: AffectedComponent[];
}) {
  if (components.length === 0) {
    return (
      <p className="py-4 text-center text-sm italic text-muted-foreground">
        No affected components identified.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-xs text-muted-foreground">
            <th className="pb-2 font-medium">ID</th>
            <th className="pb-2 font-medium">Component</th>
            <th className="pb-2 font-medium">Impact</th>
            <th className="pb-2 font-medium">Related Root Causes</th>
          </tr>
        </thead>
        <tbody>
          {components.map((cmp) => (
            <tr key={cmp.id} className="border-b last:border-0">
              <td className="py-2 font-mono text-xs">{cmp.id}</td>
              <td className="py-2 font-medium">{cmp.name}</td>
              <td className="py-2 text-muted-foreground">{cmp.impact}</td>
              <td className="py-2">
                {cmp.related_root_causes && cmp.related_root_causes.length > 0
                  ? cmp.related_root_causes.map((rc) => (
                      <code
                        key={rc}
                        className="mr-1 rounded bg-muted px-1 py-0.5 text-xs"
                      >
                        {rc}
                      </code>
                    ))
                  : "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────

export function AnalysisSummary({
  result,
  provider,
  model,
  totalTokens,
  latencyMs,
}: AnalysisSummaryProps) {
  const date = new Date().toISOString().slice(0, 10);

  return (
    <div className="space-y-6">
      {/* Summary bar */}
      <div className="rounded-lg border bg-card p-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <p className="text-lg font-semibold">Analysis Complete</p>
            <p className="text-sm text-muted-foreground">
              {result.input_summary}
            </p>
          </div>
          <div className="flex gap-2">
            <ExportActions
              formatAsMarkdown={() => formatAsMarkdown(result)}
              formatAsJson={() => formatAsJson(result)}
              filenamePrefix={`failure-analysis-${date}`}
            />
          </div>
        </div>
        {(provider || model) && (
          <div className="mt-3 flex flex-wrap gap-4 text-xs text-muted-foreground">
            {provider && (
              <span>
                Provider: <span className="font-medium">{provider}</span>
              </span>
            )}
            {model && (
              <span>
                Model: <span className="font-medium">{model}</span>
              </span>
            )}
            {totalTokens !== undefined && (
              <span>
                Tokens:{" "}
                <span className="font-medium">
                  {totalTokens.toLocaleString()}
                </span>
              </span>
            )}
            {latencyMs !== undefined && (
              <span>
                Latency: <span className="font-medium">{latencyMs}ms</span>
              </span>
            )}
          </div>
        )}
      </div>

      {/* Section cards grid */}
      <div className="grid gap-6">
        {/* Summary */}
        <SectionCard
          title="Failure Summary"
          icon={<Bug className="h-4 w-4" />}
          variant="danger"
        >
          <p className="text-sm text-muted-foreground">{result.summary}</p>
        </SectionCard>

        {/* Root Causes */}
        <SectionCard
          title="Root Causes"
          icon={<Target className="h-4 w-4" />}
          count={result.root_causes.length}
          variant="danger"
          emptyMessage="No root causes identified."
        >
          <div className="space-y-3">
            {result.root_causes.map((rc) => (
              <RootCauseCard key={rc.id} cause={rc} />
            ))}
          </div>
        </SectionCard>

        {/* Suggested Fixes */}
        <SectionCard
          title="Suggested Fixes"
          icon={<Wrench className="h-4 w-4" />}
          count={result.suggested_fixes.length}
          variant="warning"
          emptyMessage="No suggested fixes identified."
        >
          <div className="space-y-3">
            {result.suggested_fixes.map((fix) => (
              <FixCard key={fix.id} fix={fix} />
            ))}
          </div>
        </SectionCard>

        {/* Affected Components */}
        <SectionCard
          title="Affected Components"
          icon={<ShieldAlert className="h-4 w-4" />}
          count={result.affected_components.length}
          variant="info"
          emptyMessage="No affected components identified."
        >
          <AffectedComponentsTable components={result.affected_components} />
        </SectionCard>

        {/* Test Failures */}
        <SectionCard
          title="Test Failures"
          icon={<FlaskConical className="h-4 w-4" />}
          count={result.test_failures.length}
          variant="danger"
          emptyMessage="No individual test failures listed."
        >
          <div className="space-y-3">
            {result.test_failures.map((tf) => (
              <TestFailureCard key={tf.id} failure={tf} />
            ))}
          </div>
        </SectionCard>

        {/* Environment Details */}
        <SectionCard
          title="Environment Details"
          icon={<Cpu className="h-4 w-4" />}
          count={result.environment_details.length}
          emptyMessage="No environment details recorded."
        >
          <ul className="space-y-1 text-sm">
            {result.environment_details.map((detail, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground/50" />
                <span className="text-muted-foreground">{detail}</span>
              </li>
            ))}
          </ul>
        </SectionCard>

        {/* Recommendations */}
        <SectionCard
          title="Recommendations"
          icon={<Lightbulb className="h-4 w-4" />}
          count={result.recommendations.length}
          variant="info"
          emptyMessage="No recommendations provided."
        >
          <ul className="space-y-2 text-sm">
            {result.recommendations.map((rec, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-muted-foreground"
              >
                <span className="mt-0.5 shrink-0 font-medium text-foreground">
                  {i + 1}.
                </span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </SectionCard>

        {/* Related Tests */}
        <SectionCard
          title="Related Tests"
          icon={<FileCode className="h-4 w-4" />}
          count={result.related_tests.length}
          emptyMessage="No related tests identified."
        >
          <ul className="space-y-1 text-sm">
            {result.related_tests.map((test, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground/50" />
                <code className="text-muted-foreground">{test}</code>
              </li>
            ))}
          </ul>
        </SectionCard>
      </div>
    </div>
  );
}
