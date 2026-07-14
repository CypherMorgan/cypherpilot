/** CI/CD failure log presets — one-click demo scenarios. */

import type { InputSourceType } from "@/modules/failure-analysis/types";

export interface FailurePreset {
  id: string;
  title: string;
  description: string;
  sourceType: InputSourceType;
  content: string;
  category: string;
}

export const FAILURE_PRESETS: FailurePreset[] = [
  {
    id: "assertion-error",
    title: "Assertion Error",
    description: "A pytest assertion failure in a login test",
    category: "assertion_error",
    sourceType: "stack_trace",
    content: `FAILED tests/integration/test_auth.py::test_login_success - AssertionError: assert 401 == 200

─── Test session summary ───────────────────────────────────────────
platform linux -- Python 3.12.4
rootdir: /workspace/app
plugins: asyncio-0.24.0, cov-5.0.0
collected 1 item

tests/integration/test_auth.py::test_login_success FAILED        [100%]

─── Log output ─────────────────────────────────────────────────────
INFO     2026-07-14 10:32:15 | test_auth.py:42 | Sending POST /api/v1/auth/login
INFO     2026-07-14 10:32:15 | test_auth.py:44 | Request body: {"email": "test@example.com", "password": "***"}
INFO     2026-07-14 10:32:15 | test_auth.py:46 | Response status: 401
INFO     2026-07-14 10:32:15 | test_auth.py:48 | Response body: {"detail":"Invalid credentials"}
ERROR    2026-07-14 10:32:15 | test_auth.py:50 | Expected 200, got 401

─── Stack trace ────────────────────────────────────────────────────
tests/integration/test_auth.py:60: in test_login_success
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
E   AssertionError: Expected 200, got 401
E   assert 401 == 200`,
  },
  {
    id: "timeout",
    title: "Test Timeout",
    description: "A long-running test that exceeded the time limit",
    category: "timeout",
    sourceType: "ci_log",
    content: `FAILED tests/integration/test_report_generation.py::test_generate_monthly_report - TimeoutError: Test exceeded 30s timeout

─── CI run details ─────────────────────────────────────────────────
Job: integration-tests (py3.12)
Runner: ubuntu-latest (GitHub Actions)
Duration: 32.4s
Timeout: 30s

─── Slow operations detected ───────────────────────────────────────
  • tests/integration/test_report_generation.py:85 — SQL query — 14.2s
  • tests/integration/test_report_generation.py:92 — PDF rendering — 8.7s
  • tests/integration/test_report_generation.py:103 — S3 upload — 5.1s

─── Last log lines ─────────────────────────────────────────────────
[10:45:12]  INFO | Generating report for period 2026-Q2...
[10:45:26]  INFO | Fetching 12,483 records from analytics_db
[10:45:40]  INFO | Aggregating data...
[10:45:42]  INFO | Rendering PDF template (A4, 24 pages)
[10:45:44] WARN  | Memory usage: 1.2 GB / 2.0 GB
[10:45:44]  INFO | Uploading to S3: reports/2026-Q2/monthly-report.pdf
[TIMEOUT] ❌ Job terminated after 30s`,
  },
  {
    id: "migration-conflict",
    title: "Database Migration Conflict",
    description: "Alembic revision conflict from parallel branches",
    category: "environment",
    sourceType: "ci_log",
    content: `ERROR: Alembic migration chain has a conflict

─── CI run details ─────────────────────────────────────────────────
Job: migrate-and-test
Runner: ubuntu-latest
Branch: merge-feature/flat-tables into main
Step: alembic upgrade head

─── Error output ───────────────────────────────────────────────────
alembic.util.exc.CommandError:
  Multiple branches in revision path detected.

  Current revision: 9a4b8f03e1d2 (head of branch A)
  Also at revision: 7c2d1a5b9f3e (head of branch B)

  These are the diverged revisions:

  +---> 7c2d1a5b9f3e (add_user_preferences_table)
  |     2026-07-10 14:30:00 — jane.doe

  |     9a4b8f03e1d2 (add_audit_log_indexes)
  |     2026-07-10 15:45:00 — john.smith
  |/
  |
  +---> 3e8f2c1a4b6d (previous_common_ancestor)
        2026-07-09 11:00:00 — jane.doe

─── Migration history ──────────────────────────────────────────────
$ alembic history
  <base> → 1a2b3c (init)
  1a2b3c → 2d3e4f (add_users_table)
  2d3e4f → 3e8f2c (add_projects_table)
  │
  ├── 3e8f2c → 9a4b8f (add_audit_log_indexes)  ← branch A (your PR)
  │
  └── 3e8f2c → 7c2d1a (add_user_preferences_table)  ← branch B (merged first)

─── Repo state ─────────────────────────────────────────────────────
$ git log --oneline --graph -10
  *   7a3f2b1 (HEAD -> merge-feature/flat-tables) Merge branch 'main'
  |\\
  | * 5c8d2e3 (main) Add user preferences table migration
  * | 4f1a2b3 Add audit log indexes migration
  |/
  o 9b7c2d1 Previous common ancestor

─── Resolution ────────────────────────────────────────────────────
  $ alembic merge -m "merge_heads" 9a4b8f 7c2d1a
  $ alembic upgrade head  # should succeed after merge`,
  },
  {
    id: "flaky-test",
    title: "Flaky Test",
    description: "An intermittently failing integration test",
    category: "assertion_error",
    sourceType: "plain_text",
    content: `FLAKY: tests/integration/test_notifications.py::test_send_email_notification
  Status: FAILED on attempt 1/3, PASSED on retry 2/3

─── Test history (last 10 runs) ────────────────────────────────────
Run #  | Status  | Duration | Timestamp
───────|─────────|──────────|────────────────────
  1    | PASS    | 1.2s     | 2026-07-14 09:00
  2    | PASS    | 0.9s     | 2026-07-14 09:15
  3    | FAIL    | 3.1s     | 2026-07-14 09:30  ←
  4    | PASS    | 1.1s     | 2026-07-14 09:45
  5    | FAIL    | 2.8s     | 2026-07-14 10:00  ←
  6    | PASS    | 1.0s     | 2026-07-14 10:15
  7    | PASS    | 1.2s     | 2026-07-14 10:30
  8    | FAIL    | 3.5s     | 2026-07-14 10:45  ←
  9    | PASS    | 1.1s     | 2026-07-14 11:00
 10    | FAIL    | 2.9s     | 2026-07-14 11:15  ← current

─── Failure output ─────────────────────────────────────────────────
tests/integration/test_notifications.py:78: in test_send_email_notification
    assert mock_smtp.sendmsg.call_count == 1
E   assert 0 == 1
E   +  where 0 = <MagicMock name='smtp.sendmsg' call_count>.call_count

─── Observations ───────────────────────────────────────────────────
  • Fails ~40% of the time (4/10 recent runs)
  • Always passes on retry
  • Duration is ~3x longer on failures → likely race condition
  • Suspected: SMTP mock cleanup races with async fixture teardown`,
  },
  {
    id: "crashloop-backoff",
    title: "K8s CrashLoopBackOff",
    description: "Container crashes on startup in staging cluster",
    category: "environment",
    sourceType: "ci_log",
    content: `STATUS: CrashLoopBackOff — pod qpilot-api-7d9f8c6b4-abcde

─── Cluster context ────────────────────────────────────────────────
Cluster: qpilot-staging (EKS us-east-1)
Namespace: qpilot-app
Deployment: qpilot-api (replicas: 3)
Image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/qpilot-api:0.4.0

─── Pod events ─────────────────────────────────────────────────────
  $ kubectl describe pod qpilot-api-7d9f8c6b4-abcde

  Events:
    Type     Reason     Age    From               Message
    ----     ------     ----   ----               -------
    Warning  BackOff    2m     kubelet            Back-off restarting
    Warning  CrashLoop  3m     kubelet            pod crashed 5 times
    Normal   Pulled     3m     kubelet            Successfully pulled image
    Normal   Created    3m     kubelet            Created container api
    Normal   Started    3m     kubelet            Started container

─── Container logs (last crash) ────────────────────────────────────
  $ kubectl logs --previous qpilot-api-7d9f8c6b4-abcde

  [2026-07-14 11:02:15] INFO: Starting QPilot API v0.4.0
  [2026-07-14 11:02:15] INFO: Connecting to database...
  [2026-07-14 11:02:15] ERROR: Could not connect to database
    sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
      connection to server at "postgres.staging.svc.cluster.local:5432"
      failed: could not translate host name to address

  [2026-07-14 11:02:15] ERROR: Startup checks failed. Exiting.
  [2026-07-14 11:02:15] INFO: Shutting down gracefully...

─── Service discovery check ────────────────────────────────────────
  $ kubectl get svc -n qpilot-infra postgres
  NAME       TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)
  postgres   ClusterIP   10.100.24.56  <none>        5432/TCP

  $ kubectl exec -it temp-pod -- nslookup postgres.qpilot-infra.svc.cluster.local
  Server:    10.100.0.10
  Address:   10.100.0.10#53
  ** server can't find postgres.qpilot-infra.svc.cluster.local: NXDOMAIN

─── Root cause ─────────────────────────────────────────────────────
  The pod is looking up postgres.staging.svc.cluster.local but the
  service is in the qpilot-infra namespace — should be:
    postgres.qpilot-infra.svc.cluster.local

  Fix: update DATABASE_URL in ConfigMap to use the correct namespace
    postgresql://user:pass@postgres.qpilot-infra.svc.cluster.local:5432/qpilot`,
  },
  {
    id: "env-mismatch",
    title: "Environment Mismatch",
    description: "Different Python versions between CI and dev",
    category: "environment",
    sourceType: "ci_log",
    content: `ERROR: Python version mismatch detected

─── CI run details ─────────────────────────────────────────────────
Job: lint-and-test (py3.11)
Runner: ubuntu-latest
Python: 3.11.9 (CI)
Branch: feature/add-ml-models

─── Error ──────────────────────────────────────────────────────────
  tests/unit/test_config.py:28: in test_feature_flags
    assert config.get("ml_models_enabled") is True
E   AssertionError: assert None is True

─── Root cause ─────────────────────────────────────────────────────
src/config.py uses \`sys.version_info\` to conditionally enable
features. The \`ml_models_enabled\` flag requires Python ≥ 3.12:

  src/config.py:45
      @property
      def ml_models_enabled(self) -> bool:
          return sys.version_info >= (3, 12)  # ← False on 3.11

─── Environment comparison ─────────────────────────────────────────
                 CI (3.11)   Developer machine (3.12)
─────────────── ─────────── ─────────────────────────
Python          3.11.9      3.12.4
OS              Ubuntu 24   macOS 14.5 (ARM)
Dependencies    ✅ sync     ✅ sync
Feature flags   ML: OFF     ML: ON

─── Suggested fix ──────────────────────────────────────────────────
Option 1: Update CI matrix to include Python 3.12
Option 2: Remove version gate — test ML features independently`,
  },
  {
    id: "db-connection",
    title: "Database Connection Failure",
    description: "Database unavailable during integration tests",
    category: "configuration",
    sourceType: "ci_log",
    content: `FAILED tests/integration/test_user_repository.py::test_create_user - OperationalError: could not connect to server

─── CI run details ─────────────────────────────────────────────────
Job: integration-tests
Runner: ubuntu-latest
Service: postgres:16 (container)

─── Error trace ────────────────────────────────────────────────────
  File "/workspace/app/src/infrastructure/database.py:42", in get_session
    async with async_session_maker() as session:
  File "sqlalchemy/ext/asyncio.py:1234", in __aenter__
    ...
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
  could not connect to server: Connection refused
    Is the server running on host "localhost" (127.0.0.1) and
    accepting TCP/IP connections on port 5432?

─── CI logs ────────────────────────────────────────────────────────
[11:02:15]  Starting PostgreSQL service container...
[11:02:15]  Pulling postgres:16 from ghcr.io
[11:02:20]  Error: postgres:16 not found in ghcr.io cache
[11:02:22]  Falling back to Docker Hub...
[11:02:35]  PostgreSQL container started (port: 5432)
[11:02:35]  Running migrations...
[11:02:38]  ⚠ Connection refused — is postgres accepting connections?
[11:02:40]  Starting pytest...
[11:02:41]  FAILED test_create_user

─── Service health ─────────────────────────────────────────────────
$ docker ps
CONTAINER ID   IMAGE        STATUS         PORTS
a1b2c3d4e5f6   postgres:16  Up 8 seconds   0.0.0.0:5432->5432/tcp

$ docker logs a1b2c3d4e5f6
2026-07-14 11:02:30.512 UTC [1] LOG:  database system was interrupted
2026-07-14 11:02:30.518 UTC [1] LOG:  performing crash recovery
2026-07-14 11:02:30.612 UTC [1] LOG:  database system ready

→ Database was still in recovery when the test started.`,
  },
  {
    id: "compilation-error",
    title: "Compilation Error",
    description: "TypeScript build failure in CI pipeline",
    category: "compilation",
    sourceType: "ci_log",
    content: `ERROR: Failed to compile frontend

─── CI run details ─────────────────────────────────────────────────
Job: build-and-test
Runner: ubuntu-latest
Step: npm run build (frontend/)
Exit code: 2

─── Compiler output ────────────────────────────────────────────────
src/components/DataGrid.tsx:124:18 - error TS2322: Type 'string | undefined'
  is not assignable to type 'string'.

    122    >
    123      {columns.map((col) => (
    124        <th key={col.key}>{col.label?.toUpperCase()}</th>
                                        ~~~~~~~~~~
    'col.label' is possibly 'undefined'.

  src/types/report.ts:42:3
    42   label?: string;
           ~~~~~~~~~~~~~
    The expected type comes from property 'label' which is
    declared here in type 'ColumnConfig'.

─── Changed files in this PR ───────────────────────────────────────
  src/components/DataGrid.tsx    (modified)
  src/types/report.ts             (modified)
  src/hooks/use-report-data.ts   (added)

─── git diff (relevant) ────────────────────────────────────────────
  src/types/report.ts
  -  label: string;
  +  label?: string;     ← Changed to optional, broke DataGrid

─── Build step log ─────────────────────────────────────────────────
$ npm run build
> qpilot-frontend@0.4.0 build
> tsc --noEmit && vite build

src/components/DataGrid.tsx:124:18 - error TS2322: ...
  ✗ Build failed after 12.4s`,
  },
  {
    id: "docker-pull-limit",
    title: "Docker Pull Rate Limit",
    description: "Docker Hub anonymous rate limit hit in CI",
    category: "environment",
    sourceType: "ci_log",
    content: `ERROR: build step 1 — docker pull — failed

─── CI run details ─────────────────────────────────────────────────
Job: build-and-push
Runner: ubuntu-latest
Step: docker compose build
Time: 2026-07-14 14:22:00 UTC

─── Error output ───────────────────────────────────────────────────
  $ docker pull python:3.12-slim

  3.12-slim: Pulling from library/python
  a0b1c2d3e4f5: Waiting
  ...
  error: denied: requested access to the resource is denied
  error: pull access denied for python:3.12-slim
  repository does not exist or may require 'docker login'

─── Docker Hub rate limit info ─────────────────────────────────────
  Docker Hub anonymous rate limit:
    • 100 pulls per 6 hours per IP address
    • After limit: HTTP 429 / "denied: requested access..."

  Current account: anonymous (no credentials configured)
  Pulls in window: 97 / 100 (estimated)

  Affected images in this build:
    • python:3.12-slim (base image)
    • node:22-alpine (frontend builder)
    • postgres:16 (test service)

─── CI agent IP ────────────────────────────────────────────────────
  Runner IP: 20.84.123.45 (shared GitHub Actions runner)
  Note: GitHub Actions runners share IP ranges with other
  organizations — rate limits are easily exhausted.

─── Suggested fixes ────────────────────────────────────────────────
  Option 1: Add Docker Hub credentials to CI secrets
    $ echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin
    → Authenticated users get 200 pulls/6h

  Option 2: Use a pull-through cache (ECR / GCR / Docker Registry Mirror)
    → Recommended for team CI: set up ECR pull-through cache for Docker Hub

  Option 3: Pin images to a private registry with retagged copies
    → Copy commonly used images to ECR/GCR and reference those`,
  },
  {
    id: "ssl-cert-expired",
    title: "SSL Certificate Expired",
    description: "Expired TLS cert breaks staging integration tests",
    category: "configuration",
    sourceType: "ci_log",
    content: `FAILED tests/integration/test_webhook_receiver.py::test_receive_stripe_webhook - SSLError: certificate expired

─── CI run details ─────────────────────────────────────────────────
Job: integration-tests
Runner: ubuntu-latest
Target: https://staging.example.com
Timestamp: 2026-07-14 09:15:00 UTC

─── Error trace ────────────────────────────────────────────────────
  tests/integration/test_webhook_receiver.py:42: in test_receive_stripe_webhook
    response = httpx.post(
              ^^^^^^^^^^^^
  httpx._exceptions.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED]
    certificate verify failed: certificate has expired

─── SSL certificate details ────────────────────────────────────────
  $ openssl s_client -connect staging.example.com:443 -servername staging.example.com 2>&1 | openssl x509 -noout -text

  Certificate:
      Subject: CN = *.example.com
      Issuer:  CN = R3, O = Let's Encrypt
      Validity:
          Not Before: Jul 14 00:00:00 2025 GMT
          Not After:  Jul 12 00:00:00 2026 GMT  ← EXPIRED 2 days ago
      Subject Alt Name: DNS:*.example.com, DNS:example.com

─── Certificate expiry check across all services ───────────────────
  Service                        | Expiry         | Status
  ───────────────────────────────|───────────────|────────
  *.example.com (staging)        | 2026-07-12    | ❌ EXPIRED
  *.example.com (production)     | 2026-09-15    | ✅ OK
  api.stripe.com (external call) | 2027-03-20    | ✅ OK

─── Certificate issuer ─────────────────────────────────────────────
  Issued by: Let's Encrypt (R3)
  Auto-renewal: managed by cert-manager in EKS
  cert-manager pod status:
    $ kubectl get pods -n cert-manager
    NAME                                       READY   STATUS
    cert-manager-cainjector-7d9f8c6b4-abcde    1/1     Running
    cert-manager-webhook-5e4f2a1b3c-xyz78      1/1     Running
    cert-manager-6b8f2c1a4d-efg45              1/1     Running

    $ kubectl get certificate -n qpilot-infra
    NAME              READY   REASON
    staging-tls       False   ✗ CertificateExpired  ← cert-manager failed to renew
    production-tls    True    ✓ Ready

─── cert-manager logs ──────────────────────────────────────────────
  $ kubectl logs -n cert-manager deploy/cert-manager --tail=20
  W0714 09:00:00.123456     1 controller.go:117] Certificate "staging-tls"
    is expired. Certificate not renewed, check:
    - DNS-01 challenge failed: no Route53 credentials found
    - Check Secret "route53-credentials" in namespace cert-manager

  → Route53 credentials Secret was deleted during namespace cleanup`,
  },
  {
    id: "secrets-expired",
    title: "Secrets Rotation Failure",
    description: "Expired AWS credentials break CI deployment step",
    category: "environment",
    sourceType: "ci_log",
    content: `ERROR: Failed to deploy — AWS SDK could not authenticate

─── CI run details ─────────────────────────────────────────────────
Job: deploy-to-staging
Runner: qpilot-self-hosted (EC2)
Step: aws eks update-kubeconfig
Trigger: push to main (merged PR #842)
Timestamp: 2026-07-14 16:30:00 UTC

─── Error output ───────────────────────────────────────────────────
  $ aws sts get-caller-identity

  An error occurred (ExpiredToken) when calling the GetCallerIdentity
  operation: The security token included in the request is expired

  Current IAM role: arn:aws:iam::123456789012:role/qpilot-ci-role
  Session expiry: 2026-07-14 12:00:00 UTC (expired 4h 30m ago)

─── CI pipeline timeline ───────────────────────────────────────────
  Step                          | Duration | Status
  ──────────────────────────────|──────────|───────
  Checkout                      | 12s      | ✅
  Install dependencies          | 45s      | ✅
  Run tests                     | 3m 20s   | ✅
  Build Docker image            | 2m 10s   | ✅
  Push to ECR                   | 35s      | ✅
  Configure AWS credentials ⚠  | 2s       | ✅ (refreshes at start)
  Update kubeconfig             | 5s       | ❌ ExpiredToken
  Deploy to EKS                 | —        | ⏭ skipped

  Total time: 7m 4s — failed at 6m 29s

─── Credential chain investigation ─────────────────────────────────
  $ aws sts assume-role --role-arn arn:aws:iam::...:role/qpilot-ci-role

  Credentials used were generated by GitHub Actions OIDC:
    • Role: qpilot-ci-role
    • Max session duration: 5h (configured in IAM)
    • Actual session duration before use: 4h 30m

  OIDC provider: token.actions.githubusercontent.com
  Audience: sts.amazonaws.com

─── GitHub Actions OIDC config ─────────────────────────────────────
  .github/workflows/deploy.yml:
    - name: Configure AWS Credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: arn:aws:iam::123456789012:role/qpilot-ci-role
        role-session-name: qpilot-deploy-$\{{ github.run_id }}
        aws-region: us-east-1
        role-duration-seconds: 5400  # ← 1.5h (session duration 90 min)

  → The CI workflow sets role-duration-seconds to 5400 (1.5h), but the
    actual pipeline run takes 6.5h due to a long test suite & build queue.
    The credentials expire before the deploy step runs.

─── Fix ─────────────────────────────────────────────────────────────
  Increase role-duration-seconds to 28800 (8h) in deploy.yml:
    role-duration-seconds: 28800
  Also set max session duration to 12h on the IAM role:
    aws iam update-role --role-name qpilot-ci-role --max-session-duration 43200
  Or use a separate shorter-lived role for the build vs deploy steps`,
  },
];
