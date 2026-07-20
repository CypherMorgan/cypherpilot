/** Sessions page — browse past failure analysis sessions. */

import { Bug, Terminal } from "lucide-react";

import { ROUTES } from "@/lib/constants";
import {
  SessionListPage,
  SessionRow,
} from "@/components/session-list-page";
import {
  useFailureSessions,
  useDeleteFailureSession,
} from "@/modules/failure-analysis/hooks/use-failure-analysis";
import type { AnalysisSessionListItem } from "@/modules/failure-analysis/types";

const SOURCE_ICONS: Record<string, typeof Terminal> = {
  plain_text: Terminal,
  ci_log: Terminal,
  stack_trace: Terminal,
  markdown: Terminal,
};

export function FailureSessionsPage() {
  return (
    <SessionListPage
      useSessions={(page) => {
        const { data, isLoading, isError, error } = useFailureSessions(page);
        return { data, isLoading, isError, error };
      }}
      useDeleteSession={useDeleteFailureSession}
      backRoute={ROUTES.FAILURE_ANALYSIS}
      sessionRoute={ROUTES.FAILURE_SESSION}
      title="Session History"
      description="Browse past failure analysis results."
      emptyTitle="No sessions yet"
      emptyDescription="Run your first failure analysis to see past results here."
      emptyActionLabel="New Analysis"
      emptyIcon={<Bug className="h-12 w-12 text-muted-foreground" />}
      renderRow={(session, { onClick, onDelete }) => (
        <SessionRow
          config={{
            icon: (() => {
              const Icon = (session as AnalysisSessionListItem).source_type
                ? SOURCE_ICONS[
                    (session as AnalysisSessionListItem)
                      .source_type as keyof typeof SOURCE_ICONS
                  ] ?? Terminal
                : Terminal;
              return <Icon className="h-4 w-4 text-muted-foreground" />;
            })(),
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
