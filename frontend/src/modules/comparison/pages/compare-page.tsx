/**
 * Compare page — side-by-side comparison of two analysis sessions.
 *
 * Two modes:
 * 1. Session picker — select two sessions to compare
 * 2. Comparison view — shows diffs between the two sessions
 */

import { useEffect, useState, useCallback } from "react";
import {
  ArrowLeftRight,
  ChevronDown,
  ChevronRight,
  Loader2,
  GitCompareArrows,
  Plus,
  Minus,
  Pencil,
  Equal,
  BadgeCheck,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  compareSessions,
  listCompareSessions,
  getSectionLabel,
  getAnalysisTypeLabel,
  getAnalysisTypeColor,
  type CompareSessionItem,
  type ComparisonResult,
  type SectionDiff,
  type ScalarDiff,
} from "@/modules/comparison/services";

// ── Session Picker ─────────────────────────────────────────────

function SessionCard({
  session,
  label,
  selected,
  onSelect,
}: {
  session: CompareSessionItem;
  label: string;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      className={`w-full rounded-lg border p-3 text-left transition-all ${
        selected
          ? "border-primary bg-primary/5 ring-2 ring-primary/20"
          : "border-border hover:border-primary/50 hover:bg-muted/50"
      }`}
    >
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
        {selected && <BadgeCheck className="h-4 w-4 text-primary" />}
      </div>
      <p className="mt-1 text-sm font-medium truncate">
        {session.title || "Untitled Analysis"}
      </p>
      <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
        <span
          className={`inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-medium ${getAnalysisTypeColor(session.analysis_type)}`}
        >
          {getAnalysisTypeLabel(session.analysis_type)}
        </span>
        {session.provider && <span>{session.provider}</span>}
        {session.total_tokens && <span>{session.total_tokens.toLocaleString()} tokens</span>}
      </div>
    </button>
  );
}

// ── Diff Display Components ────────────────────────────────────

function MetadataDiffRow({ diff }: { diff: ScalarDiff }) {
  if (!diff.changed) return null;
  return (
    <div className="flex items-center gap-3 rounded-md border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-sm">
      <span className="font-medium capitalize text-muted-foreground min-w-[100px]">
        {diff.field.replace(/_/g, " ")}
      </span>
      <span className="text-red-500 line-through">{String(diff.value_a ?? "—")}</span>
      <span className="text-muted-foreground">→</span>
      <span className="text-emerald-500">{String(diff.value_b ?? "—")}</span>
    </div>
  );
}

function SectionDiffView({ diff }: { diff: SectionDiff }) {
  const [expanded, setExpanded] = useState(false);
  const totalChanges = diff.added.length + diff.removed.length + diff.changed.length;

  return (
    <div className="rounded-lg border">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-muted/50"
      >
        <div className="flex items-center gap-3">
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="font-medium">{getSectionLabel(diff.section)}</span>
          <span className="text-sm text-muted-foreground">
            A: {diff.count_a} · B: {diff.count_b}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {diff.added.length > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
              <Plus className="h-3 w-3" /> {diff.added.length}
            </span>
          )}
          {diff.removed.length > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full bg-red-500/15 px-2 py-0.5 text-xs font-medium text-red-600 dark:text-red-400">
              <Minus className="h-3 w-3" /> {diff.removed.length}
            </span>
          )}
          {diff.changed.length > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/15 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
              <Pencil className="h-3 w-3" /> {diff.changed.length}
            </span>
          )}
          {totalChanges === 0 && (
            <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              <Equal className="h-3 w-3" /> identical
            </span>
          )}
        </div>
      </button>

      {expanded && (
        <div className="border-t px-4 py-3 space-y-3">
          {/* Added items */}
          {diff.added.map((item, i) => (
            <div
              key={`added-${i}`}
              className="rounded-md border border-emerald-500/20 bg-emerald-500/5 p-3"
            >
              <div className="flex items-center gap-2 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                <Plus className="h-3 w-3" /> Added in B
              </div>
              <pre className="mt-2 overflow-x-auto text-xs text-muted-foreground whitespace-pre-wrap">
                {JSON.stringify(item, null, 2)}
              </pre>
            </div>
          ))}

          {/* Removed items */}
          {diff.removed.map((item, i) => (
            <div
              key={`removed-${i}`}
              className="rounded-md border border-red-500/20 bg-red-500/5 p-3"
            >
              <div className="flex items-center gap-2 text-xs font-medium text-red-600 dark:text-red-400">
                <Minus className="h-3 w-3" /> Removed from A
              </div>
              <pre className="mt-2 overflow-x-auto text-xs text-muted-foreground whitespace-pre-wrap">
                {JSON.stringify(item, null, 2)}
              </pre>
            </div>
          ))}

          {/* Changed items */}
          {diff.changed.map((pair, i) => (
            <div
              key={`changed-${i}`}
              className="rounded-md border border-amber-500/20 bg-amber-500/5 p-3"
            >
              <div className="flex items-center gap-2 text-xs font-medium text-amber-600 dark:text-amber-400">
                <Pencil className="h-3 w-3" /> Changed
              </div>
              <div className="mt-2 grid grid-cols-2 gap-2">
                <div>
                  <p className="text-[10px] font-medium text-muted-foreground mb-1">A</p>
                  <pre className="overflow-x-auto text-xs text-muted-foreground whitespace-pre-wrap rounded bg-background p-2 border">
                    {JSON.stringify(pair.a, null, 2)}
                  </pre>
                </div>
                <div>
                  <p className="text-[10px] font-medium text-muted-foreground mb-1">B</p>
                  <pre className="overflow-x-auto text-xs text-muted-foreground whitespace-pre-wrap rounded bg-background p-2 border">
                    {JSON.stringify(pair.b, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          ))}

          {/* Unchanged count */}
          {diff.unchanged.length > 0 && (
            <p className="text-xs text-muted-foreground">
              {diff.unchanged.length} item{diff.unchanged.length !== 1 ? "s" : ""} unchanged
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Comparison View ───────────────────────────────────────

function ComparisonView({
  result,
  onBack,
}: {
  result: ComparisonResult;
  onBack: () => void;
}) {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeftRight className="mr-2 h-4 w-4" />
          Back to picker
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-bold tracking-tight">Session Comparison</h1>
        <p className="mt-1 text-muted-foreground">
          Comparing two {getAnalysisTypeLabel(result.session_a.analysis_type)} sessions.
        </p>
      </div>

      {/* Session headers */}
      <div className="grid grid-cols-2 gap-4">
        {[result.session_a, result.session_b].map((session, i) => (
          <div key={i} className="rounded-lg border p-4">
            <p className="text-xs font-medium text-muted-foreground">
              Session {i === 0 ? "A" : "B"}
            </p>
            <p className="mt-1 font-medium">{session.title || "Untitled Analysis"}</p>
            <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
              <span
                className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ${getAnalysisTypeColor(session.analysis_type)}`}
              >
                {getAnalysisTypeLabel(session.analysis_type)}
              </span>
              {session.provider && <span>Provider: {session.provider}</span>}
              {session.model && <span>Model: {session.model}</span>}
              {session.total_tokens && (
                <span>{session.total_tokens.toLocaleString()} tokens</span>
              )}
              {session.latency_ms && <span>{session.latency_ms}ms</span>}
            </div>
          </div>
        ))}
      </div>

      {/* Metadata diffs */}
      {result.metadata_diffs.some((d) => d.changed) && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-muted-foreground">Metadata Changes</h2>
          {result.metadata_diffs
            .filter((d) => d.changed)
            .map((diff) => (
              <MetadataDiffRow key={diff.field} diff={diff} />
            ))}
        </div>
      )}

      {/* Summary comparison */}
      {(result.summary_a || result.summary_b) && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-muted-foreground">Summary</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border p-4">
              <p className="text-xs font-medium text-muted-foreground mb-2">Session A</p>
              <p className="text-sm whitespace-pre-wrap">
                {result.summary_a || "No summary available"}
              </p>
            </div>
            <div className="rounded-lg border p-4">
              <p className="text-xs font-medium text-muted-foreground mb-2">Session B</p>
              <p className="text-sm whitespace-pre-wrap">
                {result.summary_b || "No summary available"}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Section diffs */}
      {result.section_diffs.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-muted-foreground">Content Differences</h2>
          {result.section_diffs.map((diff) => (
            <SectionDiffView key={diff.section} diff={diff} />
          ))}
        </div>
      )}

      {/* No differences */}
      {result.section_diffs.every(
        (d) => d.added.length === 0 && d.removed.length === 0 && d.changed.length === 0,
      ) && !result.metadata_diffs.some((d) => d.changed) && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12 text-muted-foreground">
          <Equal className="mb-3 h-10 w-10 opacity-30" />
          <p className="text-sm">These sessions appear identical</p>
        </div>
      )}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────

export function ComparePage() {
  const [sessions, setSessions] = useState<CompareSessionItem[]>([]);
  const [selectedA, setSelectedA] = useState<string | null>(null);
  const [selectedB, setSelectedB] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async (type?: string) => {
    setLoading(true);
    try {
      const res = await listCompareSessions({
        analysis_type: type === "all" ? undefined : type,
        page_size: 100,
      });
      setSessions(res.items);
    } catch (err: unknown) {
      setError((err as { message?: string })?.message ?? "Failed to load sessions");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions(filterType);
  }, [filterType, fetchSessions]);

  const handleCompare = async () => {
    if (!selectedA || !selectedB) return;
    setComparing(true);
    setError(null);
    try {
      const res = await compareSessions(selectedA, selectedB);
      setResult(res);
    } catch (err: unknown) {
      setError((err as { message?: string })?.message ?? "Failed to compare sessions");
    } finally {
      setComparing(false);
    }
  };

  // If comparison result is showing
  if (result) {
    return (
      <ComparisonView
        result={result}
        onBack={() => {
          setResult(null);
          setSelectedA(null);
          setSelectedB(null);
        }}
      />
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Compare Sessions</h1>
        <p className="mt-1 text-muted-foreground">
          Select two completed analysis sessions of the same type to see a side-by-side diff.
        </p>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">Filter by type:</span>
        <Select value={filterType} onValueChange={setFilterType}>
          <SelectTrigger className="w-[200px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="failure-analysis">Failure Analysis</SelectItem>
            <SelectItem value="requirement-analysis">Requirement Analysis</SelectItem>
            <SelectItem value="api-test-generation">API Test Generation</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          Loading sessions...
        </div>
      ) : sessions.length < 2 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-muted-foreground">
          <GitCompareArrows className="mb-3 h-10 w-10 opacity-30" />
          <p className="text-sm">Not enough sessions to compare</p>
          <p className="mt-1 text-xs">
            You need at least 2 completed sessions of the same type.
          </p>
        </div>
      ) : (
        <>
          {/* Session pickers */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="mb-2 text-sm font-medium">Session A</p>
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {sessions.map((s) => (
                  <SessionCard
                    key={s.id}
                    session={s}
                    label="A"
                    selected={selectedA === s.id}
                    onSelect={() => setSelectedA(s.id)}
                  />
                ))}
              </div>
            </div>
            <div>
              <p className="mb-2 text-sm font-medium">Session B</p>
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {sessions.map((s) => (
                  <SessionCard
                    key={s.id}
                    session={s}
                    label="B"
                    selected={selectedB === s.id}
                    onSelect={() => setSelectedB(s.id)}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Compare button */}
          <div className="flex justify-center">
            <Button
              onClick={handleCompare}
              disabled={!selectedA || !selectedB || selectedA === selectedB || comparing}
              size="lg"
            >
              {comparing ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <GitCompareArrows className="mr-2 h-4 w-4" />
              )}
              Compare Sessions
            </Button>
          </div>

          {selectedA && selectedB && selectedA === selectedB && (
            <p className="text-center text-sm text-amber-500">
              Cannot compare a session with itself — select two different sessions.
            </p>
          )}
        </>
      )}
    </div>
  );
}
