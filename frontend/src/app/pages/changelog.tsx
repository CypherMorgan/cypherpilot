import { APP_NAME } from "@/lib/constants";
import { Separator } from "@/components/ui/separator";

interface ChangelogEntry {
  version: string;
  date: string;
  title: string;
  items: string[];
}

const entries: ChangelogEntry[] = [
  {
    version: "0.4.9",
    date: "2026-07-19",
    title: "Usability & Consistency",
    items: [
      "AI Provider settings UI — configure provider, model, API key, and base URL from Settings without editing .env or restarting",
      "Shared export dropdown — consistent ExportActions component with DropdownMenu across all modules",
      "Shared SessionListPage — parameterized component eliminates ~550 lines of duplicate pagination/search/filter/delete code",
      "Better AI error messages — structured error panels with Retry button (replays last input) and Dismiss",
    ],
  },
  {
    version: "0.4.8",
    date: "2026-07-17",
    title: "Quality-of-Life Polish",
    items: [
      "Fix dead Export/Copy buttons in Requirement Analysis — wired up the existing ExportActions component",
      "Dashboard AI Provider info — health endpoint now populates active_provider and active_model so status cards show real values",
      "Ctrl+Enter / Cmd+Enter to submit — keyboard shortcut on all 3 analysis editors",
      "Elapsed time on submit button — shows 'Analyzing... (14s)' instead of a static spinner",
      "Session history search & filter — text search by title/summary + status filter on all 3 session pages",
    ],
  },
  {
    version: "0.4.7",
    date: "2026-07-16",
    title: "Multi-Artifact Failure Analysis",
    items: [
      "Upload artifacts — drag-and-drop screenshots, JSON logs, HTML page source, and text files alongside failure output",
      "Context-aware analysis — artifact content is read server-side and inlined into the AI prompt; images are stored for future vision-provider support",
      "New POST /failures/analyze-with-artifacts endpoint — multipart form-data, keeps existing JSON endpoint backward-compatible",
      "Artifact display — thumbnails and file-type icons in the analysis page and session detail view",
    ],
  },
  {
    version: "0.4.6",
    date: "2026-07-16",
    title: "Session Cleanup & Retention",
    items: [
      "Delete analysis sessions — trash button on detail pages and list pages with confirmation dialog",
      "Configurable retention policy — RETENTION__RETENTION_DAYS env var (default: 90 days, set to 0 to disable)",
      "Bulk cleanup endpoint — DELETE /api/v1/cleanup/expired removes all expired sessions at once",
      "Cleanup UI in Settings — Clean Up Old Sessions button with result feedback",
    ],
  },
  {
    version: "0.4.5",
    date: "2026-07-14",
    title: "API Test Gen Presets",
    items: [
      "5 real-world OpenAPI specs — Payment Intents (Stripe-style), Issues & Repos (GitHub-style), Transactional Email (SendGrid-style), User Management (auth + admin), File Storage (S3-compatible)",
      "Load with a click — fills the editor, auto-selects JSON format, sets the title",
      "Production-scale detail — full request/response schemas, auth flows, error handling, pagination, webhooks",
    ],
  },
  {
    version: "0.4.4",
    date: "2026-07-14",
    title: "Requirement Analysis Presets",
    items: [
      "6 real-world product requirements — Enterprise SSO (SAML/OIDC + SCIM), Marketplace Payouts (Stripe Connect-style), Collaborative Editing (CRDT-based), Video Streaming Platform, Immutable Audit Log System, Feature Flag Platform",
      "Rich specifications — detailed functional and non-functional requirements in plain text, Markdown, and Gherkin (Given/When/Then) formats",
      "Great for demo mode — all presets are client-side, no backend needed",
    ],
  },
  {
    version: "0.4.3",
    date: "2026-07-14",
    title: "CI Log Presets",
    items: [
      "One-click demo scenarios — 8 realistic CI failure examples (assertion error, timeout, missing dependency, flaky test, type error, env mismatch, DB connection, compilation error)",
      "Load with a click — fills the editor, auto-selects source type, ready to analyze",
      "Great for demo mode — works fully in GitHub Pages preview mode, no backend needed",
    ],
  },
  {
    version: "0.4.2",
    date: "2026-07-13",
    title: "Session History",
    items: [
      "Session History pages for all three modules — browse past analyses with pagination, status badges, metadata",
      'Quick navigation — "History" button on every analysis page and session detail page',
      'Previous "Back to Dashboard" buttons now navigate back to the module\'s analysis page',
    ],
  },
  {
    version: "0.4.1",
    date: "2026-07-13",
    title: "Export & Share",
    items: [
      "Export Failure Analysis reports — Download as Markdown (.md) or JSON (.json) with one click",
      "Copy to clipboard — Copy the full Markdown report for pasting into PRs, tickets, or Slack",
      "Client-side export — No backend needed; works fully in GitHub Pages preview mode",
    ],
  },
  {
    version: "0.4.0",
    date: "2026-07-13",
    title: "Automation Failure Analysis",
    items: [
      "Failure Analysis module — analyze CI/CD logs, stack traces, and error output for AI-powered root cause detection",
      "Multiple input formats — plain text, CI log output, stack traces",
      "Export reports — downloadable Markdown and JSON reports",
      "Backend — 245+ tests, FastAPI async endpoints, SQLAlchemy 2.0",
    ],
  },
  {
    version: "0.3.0",
    date: "2026-07-12",
    title: "API Test Generation",
    items: [
      "API Test Generation module — paste an OpenAPI spec and get ready-to-run pytest test suites generated by AI",
      "OpenAPI 3.0 / 3.1 support — JSON and YAML input formats",
      "Session persistence — save and browse past API test generations",
    ],
  },
  {
    version: "0.2.0",
    date: "2026-07-11",
    title: "Requirement Analysis",
    items: [
      "Requirement Analysis module — upload product requirements, get structured test cases, boundary values, and edge cases via AI",
      "Rich output — functional test cases, assumptions, risks, priority assessment",
      "Session persistence — save and browse past analyses",
    ],
  },
  {
    version: "0.1.0",
    date: "2026-07-10",
    title: "Foundation",
    items: [
      "Backend foundation — FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2",
      "AI infrastructure — provider-agnostic AI layer (Ollama local, OpenRouter cloud)",
      "Prompt management — versioned Markdown prompt templates with Jinja2",
      "Docker setup — Docker Compose for full-stack development",
      "Frontend scaffold — React + Vite + TypeScript, TanStack Query, Tailwind CSS",
    ],
  },
];

export function ChangelogPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-8 p-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">What's New</h1>
        <p className="mt-1 text-muted-foreground">
          Release history for {APP_NAME}.
        </p>
      </div>

      <Separator />

      {/* Timeline */}
      <div className="relative space-y-10">
        {/* Vertical line */}
        <div className="absolute left-[7px] top-2 h-[calc(100%-1.5rem)] w-px bg-border" aria-hidden />

        {entries.map((entry) => (
          <div key={entry.version} className="relative pl-8">
            {/* Timeline dot */}
            <div className="absolute left-0 top-1.5 h-3.5 w-3.5 rounded-full border-2 border-primary bg-background" aria-hidden />

            {/* Version badge + date */}
            <div className="mb-2 flex items-baseline gap-3">
              <span className="inline-flex items-center rounded-md bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">
                v{entry.version}
              </span>
              <time className="text-xs text-muted-foreground">{entry.date}</time>
            </div>

            {/* Title */}
            <h2 className="mb-2 text-base font-semibold">{entry.title}</h2>

            {/* Items */}
            <ul className="space-y-1.5">
              {entry.items.map((item, i) => (
                <li key={i} className="text-sm text-muted-foreground leading-relaxed">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
