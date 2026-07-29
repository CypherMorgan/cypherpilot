# CypherPilot — Feature Roadmap

> A living document tracking the planned evolution of the platform. Updated as priorities shift and lessons are learned.

---

## Phase 0 — Product Discovery *(current)*

**Status:** ✅ Complete

**Deliverables:**
- Product Vision
- MVP Scope
- Non-Goals
- Success Criteria
- Feature Roadmap (this document)
- Engineering Journal

---

## Phase 1 — System Design *(next)*

**Status:** 🔜 Planned

**Goal:** Complete architectural design before writing any implementation code.

**Deliverables:**
- Architecture overview (C4 diagrams — Context, Container, Component)
- Feature module boundaries and interfaces
- Folder structure specification
- Database schema design (ERD)
- API contract design (RESTful endpoints)
- AI Orchestration Layer design
- Provider abstraction design
- Prompt architecture and template structure
- Architecture Decision Records (ADRs)
- Design review and sign-off

---

## Phase 2 — Engineering Foundation

**Status:** 📋 Planned

**Goal:** Establish the platform skeleton — everything needed before business features.

| Layer | Technology | Key Deliverables |
|---|---|---|
| **Backend** | Python 3.12+, FastAPI | App factory, DI container, config, middleware, error handlers, health check |
| **Database** | PostgreSQL, SQLAlchemy 2.0, Alembic | Base model, session factory, migrations, seed data |
| **AI** | Provider abstraction, Prompt Manager | Base provider, Gemini adapter, template loader, response models |
| **Frontend** | React 18+, TypeScript, Vite | Project scaffold, routing, API client, shared components, theme |
| **Infrastructure** | Docker, Docker Compose | Dockerfile (backend + frontend), compose.yaml, .env template |
| **CI/CD** | GitHub Actions | Lint, type-check, test, build workflows |
| **Tooling** | Ruff, MyPy, PyTest, pre-commit | Config files, hooks, test fixtures |

**Non-functional:**
- Logging infrastructure (structured JSON logs)
- Exception handling hierarchy
- Configuration management (pydantic-settings)
- Middleware (CORS, request ID, timing)
- Pydantic response models for every endpoint

---

## Phase 3 — MVP Feature Modules

### v0.2.0 — Requirement Analysis

**Status:** 📋 Planned

### v0.3.0 — API Test Generation

**Status:** 📋 Planned

### v0.4.0 — Automation Failure Analysis

**Status:** 📋 Planned

---

## Future Phases (Post-MVP)

### v0.6.0 — Allure Report Analysis
- Upload Allure report XML/JSON
- AI-powered analysis of test trends, flaky tests, and failure clusters
- Aggregate insights across multiple test runs

### v0.6.1 — Jira Bug Generator
- Convert failure analysis into structured bug reports
- Jira-format output with summary, description, environment, steps to reproduce
- Optionally integrate with Jira API for direct ticket creation

### v0.7.0 — Test Data Generator
- Generate realistic test data for specific schemas
- Support: JSON, CSV, SQL INSERT statements, factory-boy fixtures
- AI-powered data variation and edge case generation

### v0.8.0 — PR Review Assistant
- Analyze PR diffs and identify missing test coverage
- Suggest test cases for new/changed code paths
- Integrate with GitHub PR webhooks

### v0.9.0 — Prompt Playground
- Interactive prompt editor and tester
- Compare outputs across providers and models
- Template version management UI

### v1.0.0 — Platform Maturity
- Authentication and API key management
- Multi-user workspaces
- Team collaboration (shared analyses, comments, annotations)
- Export Center (PDF, CSV, JIRA, TestRail)
- AI Usage Analytics (cost tracking, latency trends, model comparisons)
- Conversation/History browser
- Comprehensive audit logging

---

## Decision Framework: What Goes Into Each Release

Every feature candidate is evaluated against these criteria:

1. **Does it solve a real problem for the target user?**
2. **Can it be built with the current architecture?**
3. **Is it well-scoped enough to ship in one cycle (2–4 weeks)?**
4. **Does it demonstrate engineering quality suitable for a portfolio?**

If the answer to any of these is "no," the feature is deferred or descoped.

---

## How This Roadmap Evolves

- This document is updated after each Phase is completed
- Feedback from each phase may reprioritize future phases
- Non-goals may be revisited if user research contradicts our assumptions
- The roadmap is a **guide**, not a contract — we adapt as we learn
