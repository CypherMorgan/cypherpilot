# Changelog

All notable changes to CypherPilot are documented here.

---

## v0.5.1 — Provider Resilience & Error Recovery (2026-07-23)

### Backend
- **ResilientProvider** — automatic retry with exponential backoff + jitter on transient errors (429, 500, 503), up to 2 retries per provider
- **Fallback chain** — if primary provider fails, automatically tries the next configured provider (e.g. OpenRouter → Gemini → Ollama)
- **HealthTracker** — per-provider success/failure counts, average latency, success rate, consecutive failure tracking
- **Unhealthy provider skipping** — providers with 5+ consecutive failures are temporarily bypassed
- **Better error messages** — "Invalid API key for OpenRouter" instead of generic "500 error"
- **Google Gemini provider** — new `GeminiProvider` using the generateContent REST API, free-tier friendly
- **GET /api/v1/providers/health** — real-time health statistics endpoint
- **Updated /health endpoint** — now includes provider health summary

### Frontend
- **Provider Health dashboard** — Settings page shows per-provider status badges, success/failure counts, avg latency, success rate
- **Gemini in Settings UI** — Google Gemini appears as a provider option with API key input and link to AI Studio
- **GitHub Pages demo mode** — detect unreachable backend, enter demo mode with "Browse in Demo Mode" CTA on login/register
- **Refresh button** — manually refresh provider health stats

---

## v0.5.0 — Multi-User & Teams (2026-07-21)

### Backend
- **User authentication** — registration, login, JWT tokens, bcrypt password hashing
- **User model** — `users` table with username, email, display_name, role (admin/user/viewer), is_active
- **Auth middleware** — `get_current_user` (required) and `get_optional_current_user` (optional) FastAPI dependencies
- **Auth endpoints** — `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/change-password`
- **Team management** — `teams` and `team_members` tables with owner/admin/member/viewer roles
- **Team endpoints** — CRUD operations, invite/remove members, update member roles
- **Session ownership** — nullable `user_id` and `team_id` FK on `analysis_sessions` for scoped access
- **RBAC-ready** — all module list endpoints accept optional user_id for session scoping
- **Alembic migrations** — `c2d3e4f5a6b7` (users), `d3e4f5a6b7c8` (session user_id), `e4f5a6b7c8d9` (teams + team_members)

### Frontend
- **Login & Register pages** — clean auth forms with error handling and validation
- **AuthContext & useAuth** — JWT token stored in localStorage, auto-validation on mount
- **Protected routes** — redirects to /login when unauthenticated
- **API interceptor** — automatically injects Bearer token in all requests
- **User menu** — avatar with initials, display name, role badge, sign-out dropdown
- **Teams pages** — team list with create dialog, team detail with member management
- **Invite members** — username-based invitation with role selection
- **Member management** — role editing (admin/member/viewer) and member removal
- **UI components added** — Input, Label, Card, Avatar, Dialog, Select

### Quality
- **293 backend tests**, 34 frontend tests all pass
- ruff, tsc, vite build clean

## v0.4.9 — Usability & Consistency (2026-07-19)

- **AI Provider settings UI** — configure provider (OpenRouter / Ollama), model, API key, and base URL from the Settings page without editing `.env` or restarting
- **Shared export dropdown** — extracted `ExportActions` component using shadcn `DropdownMenu` replaces the hand-rolled `useState`+`onBlur` hack in Failure Analysis; both modules now use consistent export UX
- **Shared SessionListPage** — parameterized `SessionListPage<T>` component eliminates ~550 lines of duplicate pagination/search/filter/delete code; all 3 session pages now share one implementation
- **Better AI error messages** — structured error panels with "Analysis Failed" title, error details, Retry button (replays last input), and Dismiss button
- **Version bumped**: 0.4.8 → 0.4.9

## v0.4.8 — Quality-of-Life Polish (2026-07-17)

- **Fix dead Export/Copy buttons** in Requirement Analysis results — wired up the existing `ExportActions` component
- **Dashboard AI Provider info** — health endpoint now populates `active_provider` and `active_model` so dashboard cards show real values
- **`Ctrl+Enter` / `Cmd+Enter` to submit** — keyboard shortcut on all 3 analysis editors (failure, requirement, API test)
- **Elapsed time on submit button** — shows "Analyzing... (14s)" instead of a static spinner during long AI operations
- **Session history search & filter** — text search by title/summary + status filter (All / Completed / Failed / Processing) on all 3 session pages
- **245 backend + 34 frontend tests**, tsc, mypy, ruff, vite build all pass

## v0.4.7 — Multi-Artifact Failure Analysis (2026-07-16)

- **Upload artifacts** — drag-and-drop screenshots, JSON logs, HTML page source, and text files alongside failure output
- **Context-aware analysis** — artifact content (text files) is read server-side and inlined into the AI prompt; images are stored for future vision-provider support
- **`POST /failures/analyze-with-artifacts`** — new multipart/form-data endpoint keeps the existing JSON endpoint backward-compatible
- **Artifact display** — thumbnails and file-type icons in the analysis page and session detail view
- **245 backend + 34 frontend tests**, tsc, mypy, ruff, vite build all pass

## v0.4.6 — Session Cleanup & Retention (2026-07-16)

- **Delete analysis sessions** — trash button on detail pages and list pages with confirmation dialog
- **Configurable retention policy** — `RETENTION__RETENTION_DAYS` env var (default: 90 days, set to 0 to disable)
- **Bulk cleanup endpoint** — `DELETE /api/v1/cleanup/expired` removes all expired sessions at once
- **Cleanup UI in Settings** — "Clean Up Old Sessions" button with result feedback
- **Bump to v0.4.6** — 162 backend tests, 34 frontend tests, tsc, mypy, ruff all pass

## v0.4.5 — API Test Gen Presets (2026-07-14)

- **5 real-world OpenAPI specs** — Payment Intents (Stripe-style), Issues & Repos (GitHub-style), Transactional Email (SendGrid-style), User Management (auth + admin), File Storage (S3-compatible)
- **Load with a click** — fills the editor, auto-selects JSON format, sets the title
- **Production-scale detail** — full request/response schemas, auth flows, error handling, pagination, webhooks

## v0.4.4 — Requirement Analysis Presets (2026-07-14)

- **6 real-world product requirements** — Enterprise SSO (SAML/OIDC + SCIM), Marketplace Payouts (Stripe Connect-style), Collaborative Editing (CRDT-based), Video Streaming Platform, Immutable Audit Log System, Feature Flag Platform
- **Rich specifications** — detailed functional and non-functional requirements in plain text, Markdown, and Gherkin (Given/When/Then) formats
- **Great for demo mode** — all presets are client-side, no backend needed

## v0.4.3 — CI Log Presets (2026-07-14)

- **One-click demo scenarios** — 8 realistic CI failure examples (assertion error, timeout, missing dependency, flaky test, type error, env mismatch, DB connection, compilation error)
- **Load with a click** — fills the editor, auto-selects source type, ready to analyze
- **Great for demo mode** — works fully in GitHub Pages preview mode, no backend needed

## v0.4.2 — Session History (2026-07-13)

- **Session History pages** for all three modules — browse past analyses with pagination, status badges, metadata
- **Quick navigation** — "History" button on every analysis page and session detail page
- Previous "Back to Dashboard" buttons now navigate back to the module's analysis page

## v0.4.1 — Export & Share (2026-07-13)

- **Export Failure Analysis reports** — Download as Markdown (.md) or JSON (.json) with one click
- **Copy to clipboard** — Copy the full Markdown report for pasting into PRs, tickets, or Slack
- **Client-side export** — No backend needed; works fully in GitHub Pages preview mode

## v0.4.0 — Automation Failure Analysis (2026-07-13)

- **Failure Analysis module** — analyze CI/CD logs, stack traces, and error output for AI-powered root cause detection
- **Multiple input formats** — plain text, CI log output, stack traces
- **Export reports** — downloadable Markdown and JSON reports
- **Backend** — 245+ tests, FastAPI async endpoints, SQLAlchemy 2.0

## v0.3.0 — API Test Generation (2026-07-12)

- **API Test Generation module** — paste an OpenAPI spec and get ready-to-run pytest test suites generated by AI
- **OpenAPI 3.0 / 3.1 support** — JSON and YAML input formats
- **Session persistence** — save and browse past API test generations

## v0.2.0 — Requirement Analysis (2026-07-11)

- **Requirement Analysis module** — upload product requirements, get structured test cases, boundary values, and edge cases via AI
- **Rich output** — functional test cases, assumptions, risks, priority assessment
- **Session persistence** — save and browse past analyses

## v0.1.0 — Foundation (2026-07-10)

- **Backend foundation** — FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **AI infrastructure** — provider-agnostic AI layer (Ollama local, OpenRouter cloud)
- **Prompt management** — versioned Markdown prompt templates with Jinja2
- **Docker setup** — Docker Compose for full-stack development
- **Frontend scaffold** — React + Vite + TypeScript, TanStack Query, Tailwind CSS

---

For the full roadmap, see [README.md](./README.md#roadmap).
