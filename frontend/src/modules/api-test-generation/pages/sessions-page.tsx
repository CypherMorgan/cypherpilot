/** Sessions page — browse past API test generation sessions. */

import { FlaskConical, ListEnd, Layers } from "lucide-react";

import { ROUTES } from "@/lib/constants";
import {
  SessionListPage,
  SessionRow,
} from "@/components/session-list-page";
import {
  useApiTestSessions,
  useDeleteApiTestSession,
} from "@/modules/api-test-generation/hooks/use-api-test-generation";
import type { ApiTestSessionListItem } from "@/modules/api-test-generation/types";

export function ApiTestSessionsPage() {
  return (
    <SessionListPage
      useSessions={(page) => {
        const { data, isLoading, isError, error } = useApiTestSessions(page);
        return { data, isLoading, isError, error };
      }}
      useDeleteSession={useDeleteApiTestSession}
      backRoute={ROUTES.API_TEST_GENERATION}
      sessionRoute={ROUTES.API_TEST_SESSION}
      title="Session History"
      description="Browse past API test generation results."
      emptyTitle="No sessions yet"
      emptyDescription="Run your first API test generation to see past results here."
      emptyActionLabel="New Generation"
      emptyIcon={<FlaskConical className="h-12 w-12 text-muted-foreground" />}
      renderRow={(session, { onClick, onDelete }) => {
        const s = session as ApiTestSessionListItem;
        return (
          <SessionRow
            config={{
              icon: (
                <FlaskConical className="h-4 w-4 text-muted-foreground" />
              ),
              title: s.spec_title || s.title || "Untitled",
              status: s.status,
              extraInfo: [
                ...(s.endpoint_count != null
                  ? [
                      {
                        icon: <ListEnd className="h-3 w-3" />,
                        label: `${s.endpoint_count} endpoint${s.endpoint_count !== 1 ? "s" : ""}`,
                      },
                    ]
                  : []),
                {
                  icon: <Layers className="h-3 w-3" />,
                  label: "OpenAPI",
                },
              ],
              provider: s.provider,
              totalTokens: s.total_tokens,
              createdAt: s.created_at,
            }}
            onClick={onClick}
            onDelete={() => onDelete(session)}
          />
        );
      }}
    />
  );
}
