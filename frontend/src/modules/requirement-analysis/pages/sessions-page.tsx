/** Sessions page — browse past requirement analysis sessions. */

import { FileText } from "lucide-react";

import { ROUTES } from "@/lib/constants";
import {
  SessionListPage,
  SessionRow,
} from "@/components/session-list-page";
import {
  useAnalysisSessions,
  useDeleteRequirementSession,
} from "@/modules/requirement-analysis/hooks/use-requirement-analysis";
import type { AnalysisSessionListItem } from "@/modules/requirement-analysis/types";

export function RequirementSessionsPage() {
  return (
    <SessionListPage
      useSessions={(page) => {
        const { data, isLoading, isError, error } = useAnalysisSessions(page);
        return { data, isLoading, isError, error };
      }}
      useDeleteSession={useDeleteRequirementSession}
      backRoute={ROUTES.REQUIREMENT_ANALYSIS}
      sessionRoute={ROUTES.REQUIREMENT_SESSION}
      title="Session History"
      description="Browse past requirement analysis results."
      emptyTitle="No sessions yet"
      emptyDescription="Run your first requirement analysis to see past results here."
      emptyActionLabel="New Analysis"
      emptyIcon={<FileText className="h-12 w-12 text-muted-foreground" />}
      renderRow={(session, { onClick, onDelete }) => (
        <SessionRow
          config={{
            icon: <FileText className="h-4 w-4 text-muted-foreground" />,
            title:
              (session as AnalysisSessionListItem).input_summary ||
              session.title ||
              "Untitled",
            status: session.status,
            sourceTypeLabel:
              (session as AnalysisSessionListItem).source_type?.replace(
                "_",
                " ",
              ) ?? undefined,
            provider: session.provider,
            totalTokens: session.total_tokens,
            createdAt: session.created_at,
          }}
          onClick={onClick}
          onDelete={() => onDelete(session)}
        />
      )}
    />
  );
}
