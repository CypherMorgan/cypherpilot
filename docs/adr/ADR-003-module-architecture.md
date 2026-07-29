# ADR-003: Module Architecture

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | 2026-07-01 |
| **Author(s)** | CypherPilot Engineering Team |
| **Supersedes** | None |
| **Superseded by** | N/A |

---

## Context

CypherPilot is organized around feature modules — independent bundles of business logic that each solve a specific QA engineering problem. The three MVP modules are:

1. **Requirement Analysis Module** — transforms requirements into structured test cases
2. **API Test Generation Module** — transforms OpenAPI specs into PyTest suites
3. **Automation Failure Analysis Module** — transforms failure artifacts into root-cause reports

These modules share common infrastructure (AI orchestration, persistence, configuration) but solve fundamentally different problems with different domain models and output formats.

The architecture must define:
- How a module is structured internally
- What goes in a module vs. what stays in shared infrastructure
- How modules communicate (if at all)
- How modules are registered and discovered
- How modules are tested in isolation

---

## Problem Statement

How should CypherPilot organize its feature modules to ensure:

1. **Each module is independently developable** — a developer can work on Requirement Analysis without understanding Failure Analysis internals
2. **Each module is independently testable** — tests for one module don't require setup from another
3. **Modules share infrastructure without sharing implementation** — common capabilities (AI, persistence) are used through interfaces, not by importing module internals
4. **Adding a new module is predictable** — a developer creating a new module follows a known pattern, not ad-hoc conventions
5. **Module boundaries prevent accidental coupling** — one module cannot accidentally depend on another module's internal implementation

---

## Decision

We will adopt a **feature-module architecture** where each module is a self-contained Python package within `app/modules/`, with strict rules about what it can access outside its boundaries.

### Module Structure

Every module follows the same internal structure:

```
app/modules/
└── <module_name>/
    ├── __init__.py                  # Public API — exports only what other modules may use
    ├── router.py                    # FastAPI APIRouter — HTTP endpoints for this module
    ├── service.py                   # Business logic — orchestrates AI + persistence
    ├── models.py                    # Domain models — Pydantic schemas, request/response types
    ├── prompts/                     # Module-specific prompt templates
    │   └── v1/
    │       ├── system.md
    │       └── examples.md
    ├── repository.py                # Module-specific repository (if module has unique entities)
    └── tests/
        ├── __init__.py
        ├── test_router.py
        ├── test_service.py
        └── fixtures/
            └── sample_requirements.md
```

**For MVP (three modules):**

```
app/modules/
├── requirement_analysis/
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   ├── models.py
│   ├── prompts/v1/
│   ├── repository.py
│   └── tests/
├── api_test_generation/
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   ├── models.py
│   ├── prompts/v1/
│   ├── repository.py
│   └── tests/
└── failure_analysis/
    ├── __init__.py
    ├── router.py
    ├── service.py
    ├── models.py
    ├── prompts/v1/
    ├── repository.py
    └── tests/
```

### Module Registration

Modules are registered in a central location. In the MVP, routers are registered in a dedicated aggregator module rather than directly in `main.py`:

```python
# app/api/v1/api.py

from fastapi import APIRouter
from app.modules.requirement_analysis.router import router as req_router
from app.modules.api_test_generation.router import router as api_router

router = APIRouter(prefix="/api/v1")
router.include_router(req_router)   # prefix="/requirements" in router
router.include_router(api_router)   # prefix="/openapi" in router
```

Then in `main.py`, the v1 router is mounted in one line:

```python
from app.api.v1.api import router as v1_router
app.include_router(v1_router)
```

**Why an aggregator instead of registering in main.py?**
- Keeps `main.py` clean when modules grow
- Allows multiple API versions (`v1`, `v2`) with separate aggregators
- Each module's router owns its prefix and tags
- The module list is still explicit (one import per module in `api.py`)

**Why explicit registration?**
- Avoids auto-discovery magic (reflection, directory scanning)
- Makes the module list obvious from reading `api.py`
- Prevents orphaned modules from running silently
- Allows ordering and prefix configuration at a glance

### Module Boundaries

#### What belongs inside a module:

| Item | Category | Example |
|---|---|---|
| **Router** | Presentation | HTTP endpoints, request validation, response serialization |
| **Service** | Application | Workflow orchestration — "call AI, persist result, return" |
| **Domain Models** | Domain | `TestCase`, `TestSuite`, `FailureReport`, `RootCause` |
| **Prompt Templates** | Infrastructure | Module-specific Markdown prompt files |
| **Module Repository** | Infrastructure | Data access for module-specific entities |
| **Tests** | Test | Everything needed to test the module in isolation |

#### What stays outside (shared infrastructure):

| Component | Location | Purpose |
|---|---|---|
| **AI Orchestrator** | `app/ai/orchestrator.py` | Central AI gateway — all modules use this |
| **Prompt Manager** | `app/ai/prompt_manager.py` | Template loading and rendering |
| **Provider Interface** | `app/ai/provider.py` | Provider contract and response model |
| **Provider Adapters** | `app/ai/providers/` | Gemini, Claude, etc. implementations |
| **Base Repository** | `app/infrastructure/database/repository.py` | Generic CRUD base class |
| **Database Models** | `app/infrastructure/database/models.py` | SQLAlchemy ORM entity definitions |
| **Configuration** | `app/infrastructure/config.py` | pydantic-settings configuration |
| **Logger** | `app/infrastructure/logging.py` | Structured logging setup |
| **Exception Handler** | `app/infrastructure/exceptions.py` | Exception hierarchy + handlers |
| **File Storage** | `app/infrastructure/storage.py` | File storage abstraction |
| **DI Wiring** | `app/main.py` or `app/di.py` | Dependency injection at startup |

### Cross-Module Communication Rules

```
┌─────────────────────────────────────────────────────────────┐
│                     HARD RULES                                │
│                                                               │
│  Rule 1: No module imports another module's internals.        │
│    ✗ from app.modules.requirement_analysis.service import ... │
│    ✓ Use shared domain models if needed (app.domain.*)        │
│                                                               │
│  Rule 2: No module calls another module's service directly.   │
│    ✗ req_service.generate_test_cases(...)                     │
│    ✓ If cross-module workflow is needed, add an Application   │
│      Service that orchestrates both modules.                  │
│                                                               │
│  Rule 3: Modules communicate only through shared interfaces.  │
│    ✓ Both modules depend on AI Orchestrator                   │
│    ✓ Both modules depend on BaseRepository                    │
│    ✓ Both modules depend on shared domain models (if needed)  │
│                                                               │
│  Rule 4: Shared domain models live in app/domain/, not in     │
│          a module.                                             │
│    ✓ from app.domain.models import AnalysisSession            │
│                                                               │
│  Rule 5: A module's __init__.py exports ONLY what other       │
│          modules are allowed to use. Everything else is       │
│          private (prefixed with _ or nested).                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Module Service Pattern

Every module's service follows the same pattern:

```python
# app/modules/requirement_analysis/service.py

from dataclasses import dataclass

from app.ai.orchestrator import AIOrchestrator
from app.modules.requirement_analysis.models import (
    TestSuite,
    RequirementInput,
)
from app.modules.requirement_analysis.repository import (
    AnalysisSessionRepository,
)


@dataclass
class RequirementAnalysisService:
    """Coordinates requirement analysis workflow."""

    orchestrator: AIOrchestrator
    repository: AnalysisSessionRepository

    async def analyze(self, input: RequirementInput) -> TestSuite:
        # 1. Call AI Orchestrator (no knowledge of which provider)
        result = await self.orchestrator.analyze(
            analysis_type="requirement-analysis",
            context={"artifact": input.text, "output_schema": ...},
            response_model=TestSuite,
        )

        # 2. Persist result
        session = await self.repository.create(
            input=input,
            output=result.content,
            metadata=result.metadata(),
        )

        # 3. Return domain model
        return result.content
```

**Key properties:**
- The service receives all dependencies through its constructor (DI-friendly)
- The service knows about `AIOrchestrator` but not about `GeminiProvider` or `PromptManager`
- The service returns domain models, not HTTP responses
- The service is pure Python — no FastAPI dependency

### Router Pattern

Each router is thin — it validates input, calls the service, serializes the response:

```python
# app/modules/requirement_analysis/router.py

from fastapi import APIRouter, Depends

from app.modules.requirement_analysis.service import (
    RequirementAnalysisService,
)
from app.modules.requirement_analysis.models import (
    RequirementInput,
    TestSuite,
)
from app.infrastructure.dependencies import get_req_analysis_service

router = APIRouter()


@router.post("/analyze", response_model=TestSuite)
async def analyze_requirements(
    input: RequirementInput,
    service: RequirementAnalysisService = Depends(get_req_analysis_service),
) -> TestSuite:
    """Analyze a feature requirement and generate test cases."""
    return await service.analyze(input)
```

---

## Alternatives Considered

### Alternative A: Monolithic Service Layer (Rejected)

Instead of separate modules, put all analysis logic in a single service with a type-switch.

```python
class AnalysisService:
    async def analyze(self, type: str, input: dict) -> dict:
        match type:
            case "requirement":
                return await self._analyze_requirement(input)
            case "openapi":
                return await self._analyze_openapi(input)
            case "failure":
                return await self._analyze_failure(input)
```

| Dimension | Monolithic | Feature Modules (Chosen) |
|---|---|---|
| **Module boundaries** | Implicit — separated by `match` cases | Explicit — separate packages with `__init__.py` exports |
| **Code organization** | One large file or directory | Each module independent |
| **Test isolation** | All tests in one test file | Per-module test directory |
| **Developer ergonomics** | Easy to start | Requires module creation ceremony |
| **Scalability (team)** | Poor — merge conflicts on same file | Excellent — parallel development |
| **Dead code detection** | Hard — `match` cases accumulate | Easy — delete the module directory |

**Decision:** Rejected. For three modules, monolithic might seem simpler. But the module pattern creates clear ownership, test isolation, and a predictable structure for future modules. The ceremony of creating a new package is a feature, not a bug — it forces the developer to think about the module's public API.

### Alternative B: Module Auto-Discovery (Rejected)

Modules are automatically discovered by scanning the `modules/` directory:

```python
import importlib, pkgutil, pathlib

for module in pkgutil.iter_modules(["app/modules"]):
    router = importlib.import_module(f"app.modules.{module.name}.router")
    app.include_router(router.router)
```

| Dimension | Auto-Discovery | Explicit Registration (Chosen) |
|---|---|---|
| **Boilerplate** | None — just create a module directory | One line per module in main.py |
| **Orphan detection** | Hard — deleted module still appears if file lingers | Impossible — not registered = not loaded |
| **Startup failure** | Discoverable module may fail at import time | Failure happens at explicit registration point |
| **Ordering** | Alphabetical only | Explicit ordering by registration sequence |
| **Prefix control** | Must use convention from module name | Explicit per-router prefix |
| **Debugging** | "Where is this route registered?" — search needed | "main.py line 42" — obvious |

**Decision:** Rejected. Auto-discovery saves minimal effort (3 lines per module) at the cost of explicit visibility. For a platform where every module is known at build time, explicit registration is clearer and more maintainable.

### Alternative C: Cross-Module Communication via Events (Deferred)

Modules communicate through an event bus rather than direct calls:

```python
# When requirement analysis completes, emit an event
event_bus.emit("analysis.completed", session_id=...)

# API test generation module subscribes
@event_bus.on("analysis.completed")
async def on_analysis_completed(event): ...
```

| Dimension | Event-Driven | Direct Calls/None (Chosen) |
|---|---|---|
| **Coupling** | Loose — modules only know event schemas | None for MVP — modules don't need to communicate |
| **Latency** | Higher — event serialization/deserialization | No cross-module calls in MVP |
| **Complexity** | Event bus, serialization, error handling | Zero — no cross-module communication |
| **Suitability** | Good for async dependent workflows | Perfect for independent feature modules |

**Decision:** Deferred. MVP modules have no reason to communicate. If a future use case arises (e.g., "generate API tests from requirements we already analyzed"), we'll evaluate event-driven vs. orchestration-based approaches at that point.

---

## Trade-offs

| Trade-off | Assessment |
|---|---|
| **Module independence** vs **Code duplication** | Some duplication across modules (similar service patterns, similar repository patterns) is acceptable. Better duplicated structure than coupled internals. |
| **Explicit registration** vs **Convenience** | Adding a new module requires 4 lines: create directory, write router, write service, register in main.py. The 4th line is the convenience cost. Acceptable. |
| **Module-private prompts** vs **Shared prompt library** | Each module has its own prompts directory. If prompts are shared across modules (e.g., JSON schema formatting), they go in `prompts/shared/`. Clear separation. |

---

## Consequences

### Positive

1. **Each module is a complete, testable unit** — can be developed and tested in isolation
2. **New modules follow a known pattern** — copy an existing module's structure, replace implementations
3. **No accidental coupling** — hard rules prevent module A importing module B's internals
4. **Shared infrastructure is obvious** — AI Orchestrator, repositories, config are in `app/ai/` and `app/infrastructure/`
5. **Team-scalable** — different developers can work on different modules without conflicts

### Negative

1. **Initial structure overhead** — three module directories with similar files
2. **No cross-module workflows in MVP** — you can't "take requirement analysis output and feed it to API test generation" without an explicit orchestration layer (which hasn't been designed yet)
3. **Module naming conventions must be enforced** — `snake_case` package names, not `kebab-case` or `PascalCase`

### Neutral

1. **Module count may grow** — 3 modules in MVP, potentially 10+ in future. The architecture scales linearly with module count.

---

## Implementation Impact

### New Files

```
app/
├── main.py                              # Module registration
├── domain/
│   └── models.py                        # Shared domain models
└── modules/
    ├── __init__.py
    ├── requirement_analysis/
    │   ├── __init__.py
    │   ├── router.py
    │   ├── service.py
    │   ├── models.py
    │   ├── prompts/
    │   │   └── v1/
    │   │       ├── system.md
    │   │       └── examples.md
    │   ├── repository.py
    │   └── tests/
    │       ├── __init__.py
    │       ├── test_router.py
    │       ├── test_service.py
    │       └── fixtures/
    ├── api_test_generation/
    │   └── ... (same structure)
    └── failure_analysis/
        └── ... (same structure)
```

### Modified Files

- `app/infrastructure/dependencies.py` — factory functions for DI (`get_req_analysis_service`, etc.)
- `app/infrastructure/database/models.py` — SQLAlchemy models for module entities

### Configuration

No module-specific configuration. Modules receive all configuration through injected dependencies.

---

## Testing Impact

### Per-Module Test Strategy

| Test Layer | What it validates | Mock Boundary | Speed |
|---|---|---|---|
| `test_router.py` | HTTP status codes, request validation, response format | Mock service layer | ⚡ Fast |
| `test_service.py` | Business logic, AI orchestration flow, persistence | Mock AI Orchestrator + Mock Repository | ⚡ Fast |
| `test_repository.py` | Data access, query correctness | SQLite test database | ⚡ Fast |
| Integration | End-to-end flow through all layers | Real repositories, mock AI | 🐢 Medium |

### Test Fixtures

```python
# app/modules/requirement_analysis/tests/conftest.py

@pytest.fixture
def mock_orchestrator():
    """Returns predictable analysis results without AI calls."""
    ...

@pytest.fixture
def mock_repository():
    """In-memory repository for testing."""
    ...

@pytest.fixture
def service(mock_orchestrator, mock_repository):
    """RequirementAnalysisService with all dependencies mocked."""
    return RequirementAnalysisService(
        orchestrator=mock_orchestrator,
        repository=mock_repository,
    )
```

### Cross-Module Test Isolation

Tests in `app/modules/requirement_analysis/tests/` must NOT import from `app/modules/api_test_generation/`. This is enforced by:
1. Clear directory boundaries
2. CI lint rule (`ruff` import checks)
3. Convention — if a test needs something from another module, it should be in shared domain models

---

## Future Evolution

| Phase | Change | Impact |
|---|---|---|
| **v0.6.0: Allure Report Analysis** | New module `allure_analysis` | Follows same structure — create directory, implement, register in main.py |
| **v0.6.0: Jira Bug Generator** | New module `jira_bug_generator` | Follows same structure |
| **v0.7.0: Test Data Generator** | New module `test_data_generator` | Follows same structure |
| **Cross-module workflows** | New `app/application/workflows/` directory | Orchestration-level services that compose multiple modules |
| **Plugin system** | Dynamic module loading from external packages | Major refactor — only when genuinely needed |

---

## Implementation Notes (2026-07-02)

The following deviations from the original ADR design exist in the current implementation:

1. **AI Orchestrator not implemented** — The `app/ai/orchestrator.py` described in this ADR was never built. Modules call `provider_registry.get()` and `provider.generate()` directly in their service layer. This means prompt loading, response validation, and error handling are duplicated per module. An orchestrator should be added when retries, caching, or multi-provider support are needed.

2. **No central DI wiring** — Services are constructed inside router `_get_service()` dependency functions rather than wired through a central DI module (`app/infrastructure/dependencies.py` or `app/di.py`). This makes it harder to use services outside a request context.

3. **Prompt directories at project root** — Prompts live in `prompts/analysis/<module>/v1/` at the project root rather than inside each module (`app/modules/<module>/prompts/v1/`). Both patterns work, but the project-root approach makes prompts easier to find and version independently.

4. **Tests requirement_analysis tests moved inside module** — As of 2026-07-02, requirement analysis tests are in `app/modules/requirement_analysis/tests/`, matching the API test generation pattern. Tests are discovered by adding `app/modules` to `testpaths` in `pyproject.toml`.

---

## Decision Rationale Summary

The Module Architecture is **justified** because:

1. **It solves a real problem** — without clear module boundaries, files accumulate in a flat directory and dependencies become tangled
2. **The cost is minimal** — the module structure is a directory convention enforced by convention, not a framework
3. **The value is immediate** — each MVP module can be developed, tested, and reasoned about independently
4. **It demonstrates engineering maturity** — feature-module architecture is the standard pattern for production web applications

**Abstraction question answers (per engineering rule):**

| Question | Answer |
|---|---|
| **What problem does this solve?** | Prevents tangled dependencies, unclear ownership, and test pollution across features |
| **Why is this necessary today?** | Three modules are being built simultaneously; boundaries prevent coupling from day one |
| **What simpler alternative exists?** | Flat directory with one service file per feature |
| **Why was that rejected?** | Flat structure doesn't prevent cross-imports, doesn't provide a pattern for new features, and makes test organization ad-hoc |
| **How does this help evolution?** | Adding a module is a predictable pattern; removing a module is deleting a directory |
