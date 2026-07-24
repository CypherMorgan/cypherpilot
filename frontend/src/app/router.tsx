import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { RootLayout } from "@/layouts/root-layout";
import { ProtectedRoute } from "@/components/protected-route";
import { ErrorBoundary } from "@/components/error-boundary";
import { HomePage } from "@/app/pages/home";
import { SettingsPage } from "@/app/pages/settings";
import { ChangelogPage } from "@/app/pages/changelog";
import { NotFoundPage } from "@/app/pages/not-found";
import { LoginPage } from "@/app/pages/auth/login";
import { RegisterPage } from "@/app/pages/auth/register";
import { TeamsPage } from "@/modules/teams/pages/teams-page";
import { TeamDetailPage } from "@/modules/teams/pages/team-detail-page";
import { ActivityPage } from "@/modules/audit/pages/activity-page";
import { RequirementAnalysisPage } from "@/modules/requirement-analysis/pages/analysis-page";
import { SessionDetailPage } from "@/modules/requirement-analysis/pages/session-detail-page";
import { RequirementSessionsPage } from "@/modules/requirement-analysis/pages/sessions-page";
import { ApiTestGenerationPage } from "@/modules/api-test-generation/pages/generation-page";
import { ApiTestSessionDetailPage } from "@/modules/api-test-generation/pages/session-detail-page";
import { ApiTestSessionsPage } from "@/modules/api-test-generation/pages/sessions-page";
import { FailureAnalysisPage } from "@/modules/failure-analysis/pages/analysis-page";
import { FailureSessionsPage } from "@/modules/failure-analysis/pages/sessions-page";
import { FailureSessionDetailPage } from "@/modules/failure-analysis/pages/session-detail-page";

// On GitHub Pages the site is at /cypherpilot/ — match the Vite base path here.
const basename = import.meta.env.VITE_BASE_PATH || "/";

const router = createBrowserRouter(
  [
    // Public routes (no auth required)
    {
      path: "/login",
      element: <LoginPage />,
    },
    {
      path: "/register",
      element: <RegisterPage />,
    },
    // Protected routes (auth required)
    {
      path: "/",
      element: <ProtectedRoute />,
      children: [
        {
          element: <RootLayout />,
          errorElement: (
            <ErrorBoundary>
              <RootLayout />
            </ErrorBoundary>
          ),
          children: [
            { index: true, element: <HomePage /> },
            { path: "settings", element: <SettingsPage /> },
            { path: "changelog", element: <ChangelogPage /> },
            { path: "activity", element: <ActivityPage /> },
            // Teams
            { path: "teams", element: <TeamsPage /> },
            { path: "teams/:teamId", element: <TeamDetailPage /> },
            // Requirement Analysis module
            { path: "requirements/analyze", element: <RequirementAnalysisPage /> },
            { path: "requirements/sessions", element: <RequirementSessionsPage /> },
            { path: "requirements/sessions/:sessionId", element: <SessionDetailPage /> },
            // API Test Generation module
            { path: "api-tests/analyze", element: <ApiTestGenerationPage /> },
            { path: "api-tests/sessions", element: <ApiTestSessionsPage /> },
            { path: "api-tests/sessions/:sessionId", element: <ApiTestSessionDetailPage /> },
            // Failure Analysis module
            { path: "failures/analyze", element: <FailureAnalysisPage /> },
            { path: "failures/sessions", element: <FailureSessionsPage /> },
            { path: "failures/sessions/:sessionId", element: <FailureSessionDetailPage /> },
            { path: "*", element: <NotFoundPage /> },
          ],
        },
      ],
    },
  ],
  { basename },
);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
