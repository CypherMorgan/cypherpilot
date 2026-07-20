/** Main analysis results display.

Renders the complete analysis result with all sections in a
structured, scrollable layout.
*/

import {
  CheckCircle2,
  XCircle,
  ArrowLeftRight,
  AlertTriangle,
  Lightbulb,
  ShieldAlert,
  FileQuestion,
  HelpCircle,
  Cpu,
  GanttChartSquare,
} from "lucide-react";

import { SectionCard } from "@/components/section-card";
import {
  FunctionalTestCases,
  NegativeTestCases,
  BoundaryTestCases,
  EdgeCasesList,
  AssumptionsList,
  RisksList,
  MissingRequirementsList,
  QuestionsList,
  AutomationCandidatesTable,
  PriorityAssessmentBlock,
} from "@/modules/requirement-analysis/components/section-content";
import { ExportActions } from "@/components/export-actions";
import type { RequirementAnalysisResult } from "@/modules/requirement-analysis/types";

/**
 * Format the requirement analysis result as Markdown (client-side).
 */
function formatAsMarkdown(result: RequirementAnalysisResult): string {
  const lines: string[] = [];
  lines.push("# Requirement Analysis Report");
  lines.push("");
  lines.push(`**Input summary:** ${result.input_summary}`);
  lines.push("");
  lines.push("---");
  lines.push("");

  lines.push("## Functional Test Cases");
  for (const tc of result.functional_tests) {
    lines.push(`### ${tc.id}: ${tc.title}`);
    lines.push(`- **Priority:** ${tc.priority}`);
    lines.push(`- ${tc.description}`);
    lines.push("");
  }

  lines.push("## Negative Test Cases");
  for (const tc of result.negative_tests) {
    lines.push(`### ${tc.id}: ${tc.title}`);
    lines.push(`- **Priority:** ${tc.priority}`);
    lines.push(`- ${tc.description}`);
    lines.push("");
  }

  lines.push("## Risks");
  for (const r of result.risks) {
    lines.push(`- **${r.id}:** ${r.description} (Severity: ${r.severity}, Likelihood: ${r.likelihood})`);
  }

  return lines.join("\n");
}

interface AnalysisResultsProps {
  result: RequirementAnalysisResult;
  provider?: string | null;
  model?: string | null;
  totalTokens?: number;
  latencyMs?: number;
}

export function AnalysisResults({
  result,
  provider,
  model,
  totalTokens,
  latencyMs,
}: AnalysisResultsProps) {
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
              formatAsJson={() => JSON.stringify(result, null, 2)}
              filenamePrefix="requirement-analysis"
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
                Tokens: <span className="font-medium">{totalTokens.toLocaleString()}</span>
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
        {/* Functional Tests */}
        <SectionCard
          title="Functional Test Cases"
          icon={<CheckCircle2 className="h-4 w-4" />}
          count={result.functional_tests.length}
          variant="success"
          emptyMessage="No functional test cases identified."
        >
          <FunctionalTestCases tests={result.functional_tests} />
        </SectionCard>

        {/* Negative Tests */}
        <SectionCard
          title="Negative Test Cases"
          icon={<XCircle className="h-4 w-4" />}
          count={result.negative_tests.length}
          variant="danger"
          emptyMessage="No negative test cases identified."
        >
          <NegativeTestCases tests={result.negative_tests} />
        </SectionCard>

        {/* Boundary Tests */}
        <SectionCard
          title="Boundary Tests"
          icon={<ArrowLeftRight className="h-4 w-4" />}
          count={result.boundary_tests.length}
          variant="info"
          emptyMessage="No boundary tests identified."
        >
          <BoundaryTestCases tests={result.boundary_tests} />
        </SectionCard>

        {/* Edge Cases */}
        <SectionCard
          title="Edge Cases"
          icon={<AlertTriangle className="h-4 w-4" />}
          count={result.edge_cases.length}
          variant="warning"
          emptyMessage="No edge cases identified."
        >
          <EdgeCasesList cases={result.edge_cases} />
        </SectionCard>

        {/* Assumptions */}
        <SectionCard
          title="Assumptions"
          icon={<Lightbulb className="h-4 w-4" />}
          count={result.assumptions.length}
          emptyMessage="No assumptions recorded."
        >
          <AssumptionsList items={result.assumptions} />
        </SectionCard>

        {/* Risks */}
        <SectionCard
          title="Risks"
          icon={<ShieldAlert className="h-4 w-4" />}
          count={result.risks.length}
          variant="danger"
          emptyMessage="No risks identified."
        >
          <RisksList risks={result.risks} />
        </SectionCard>

        {/* Missing Requirements */}
        <SectionCard
          title="Missing Requirements"
          icon={<FileQuestion className="h-4 w-4" />}
          count={result.missing_requirements.length}
          variant="warning"
          emptyMessage="No missing requirements detected."
        >
          <MissingRequirementsList items={result.missing_requirements} />
        </SectionCard>

        {/* Suggested Questions */}
        <SectionCard
          title="Suggested Questions"
          icon={<HelpCircle className="h-4 w-4" />}
          count={result.suggested_questions.length}
          variant="info"
          emptyMessage="No suggested questions."
        >
          <QuestionsList items={result.suggested_questions} />
        </SectionCard>

        {/* Automation Candidates */}
        <SectionCard
          title="Automation Candidates"
          icon={<Cpu className="h-4 w-4" />}
          count={result.automation_candidates.length}
          emptyMessage="No automation candidates identified."
        >
          <AutomationCandidatesTable candidates={result.automation_candidates} />
        </SectionCard>

        {/* Priority Assessment */}
        <SectionCard
          title="Priority Assessment"
          icon={<GanttChartSquare className="h-4 w-4" />}
          variant="info"
        >
          <PriorityAssessmentBlock assessment={result.priority_assessment} />
        </SectionCard>
      </div>
    </div>
  );
}
