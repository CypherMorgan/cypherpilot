/** Application-wide constants */
export const APP_NAME = "CypherPilot";
export const APP_VERSION = "0.5.2";

/** Set to "true" at build time for GitHub Pages deployment (no backend) */
export const IS_PREVIEW = import.meta.env.VITE_PREVIEW_ONLY === "true";

/** API base URL — configured via Vite env, defaults to local backend */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

/** API prefix */
export const API_PREFIX = "/api/v1";

/** Route paths */
export const ROUTES = {
  HOME: "/",
  SETTINGS: "/settings",
  CHANGELOG: "/changelog",
  ACTIVITY: "/activity",
  TEAMS: "/teams",
  TEAM_DETAIL: "/teams/:teamId",
  LOGIN: "/login",
  REGISTER: "/register",
  REQUIREMENT_ANALYSIS: "/requirements/analyze",
  REQUIREMENT_SESSIONS: "/requirements/sessions",
  REQUIREMENT_SESSION: "/requirements/sessions/:sessionId",
  API_TEST_GENERATION: "/api-tests/analyze",
  API_TEST_SESSIONS: "/api-tests/sessions",
  API_TEST_SESSION: "/api-tests/sessions/:sessionId",
  FAILURE_ANALYSIS: "/failures/analyze",
  FAILURE_SESSIONS: "/failures/sessions",
  FAILURE_SESSION: "/failures/sessions/:sessionId",
} as const;

/** Navigation items displayed in the sidebar */
export const NAV_ITEMS = [
  { label: "Dashboard", path: ROUTES.HOME, icon: "LayoutDashboard" as const },
  { label: "Requirement Analysis", path: ROUTES.REQUIREMENT_ANALYSIS, icon: "FileText" as const },
  { label: "API Test Generation", path: ROUTES.API_TEST_GENERATION, icon: "FlaskConical" as const },
  { label: "Failure Analysis", path: ROUTES.FAILURE_ANALYSIS, icon: "Bug" as const },
  { label: "Settings", path: ROUTES.SETTINGS, icon: "Settings" as const },
] as const;

/** Local storage keys */
export const STORAGE_KEYS = {
  THEME: "cypherpilot-theme",
} as const;
