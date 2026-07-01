# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Read this first

`PROJECT_CONTEXT.md` in the repo root is the authoritative, full-detail project spec (regulatory
framing, full database schema, all 16 Dify sub-workflows, MLflow setup, six governance layers, build
status/timeline). Read it in full before making non-trivial changes to Dify workflow configs, MLflow
tracking, or DSL artifacts — this CLAUDE.md only covers what's needed to navigate and run the code.

This is a SIT capstone project: a governed multi-agent AI system for AIA Singapore insurance claims
assessment, built to satisfy the IMDA Model AI Governance Framework and MAS AI Risk Management
Guidelines. All data (policies, claims, PDFs) is synthetic — no real AIA data is used.

## Commands

**MCP server (FastAPI)** — the sole data-access point for agents/frontend:
```bash
cd mcp_server && uvicorn main:app --reload --port 8000
```
Cloud instance: `https://sit-capstone.onrender.com`. All endpoints use query params, not path params —
deliberate, because Dify's HTTP node has a bug handling path variables.

**Frontend (Next.js 14 + Tailwind)**:
```bash
cd frontend
npm run dev      # http://localhost:3000
npm run build
npm run lint
```
Copy `frontend/.env.local.example` to `.env.local`. `next.config.js` rewrites `/api/mcp/:path*` to the
MCP server (`MCP_BASE_URL`) so the browser never sees the raw MCP URL. The Chat view's Dify calls are
proxied the same way, through `app/api/dify/chat/route.ts`, using server-only `DIFY_URL` /
`DIFY_API_KEY` env vars (no `NEXT_PUBLIC_` prefix — never put a real secret behind that prefix, it
ships to the browser).

The `/dsl` route additionally requires Okta/NextAuth env vars (`OKTA_CLIENT_ID`, `OKTA_CLIENT_SECRET`,
`OKTA_ISSUER`, `NEXTAUTH_SECRET`, `NEXTAUTH_URL`) — see Architecture below. Generate `NEXTAUTH_SECRET`
with `openssl rand -base64 32`; it's read implicitly by NextAuth via that exact env var name (never
referenced directly in `lib/auth.ts`), and must be set in every environment (dev and each deployment
target can have their own distinct value — they don't need to match).

**Python environment**: a `venv/` already exists in the repo root with `mlflow`, `faker`, and
`reportlab` installed. `requirements.txt` only lists the MCP server's direct deps (fastapi, uvicorn,
supabase, python-dotenv, pydantic, requests, pyyaml) — it does **not** include mlflow/faker/reportlab,
which back `mlflow_tracker.py`, `generate_data.py`, and `generate_pdfs.py` respectively. Install those
separately if setting up a fresh environment.

**DSL Change Management CLI** (`dsl_manager/`), run from repo root, talks to the MCP server over HTTP
(`MCP_BASE_URL`, default `http://localhost:8000`):
```bash
python -m dsl_manager init --file dify-data/Life_Assess_Claim.yml --by <name>       # baseline hashes, first run only
python -m dsl_manager scan --file dify-data/Life_Assess_Claim.yml --by <name>       # detect changes vs baseline, submit for approval
python -m dsl_manager list-pending [--workflow <name>]
python -m dsl_manager show <approval_id>                                            # full diff
python -m dsl_manager approve <approval_id> --by <name> --reason "<justification>"  # commits to GitHub on success
python -m dsl_manager reject <approval_id> --by <name> --reason "<justification>"
```
`--by` / `--reason` are mandatory everywhere sign-off applies — a deliberate governance control, not
boilerplate to remove.

**MLflow / Databricks setup**: `python setup_mlflow.py` (one-time; auto-detects username, creates the
experiment, logs a test run). Tracking URI is `"databricks"`; credentials live in `mcp_server/.env`
(`DATABRICKS_HOST`, `DATABRICKS_TOKEN`).

No test suite exists in this repo yet.

## Architecture

**Data flow**: Frontend (Next.js) → Dify orchestrator (chat workflow, hosted separately in Dify) →
domain sub-workflows → MCP server (FastAPI, `mcp_server/main.py`, single file, all endpoints) →
Supabase (Postgres, RLS enabled). `mcp_server/routers.py` and `mcp_server/database.py` exist but are
currently empty (0 bytes) — everything lives in `main.py`; don't assume logic is split out there.

**No secrets reach the browser.** Every frontend view goes through a server-side proxy: `lib/mcp.ts` →
the `/api/mcp/*` rewrite (`next.config.js`) → the MCP server for Supabase/Databricks data, and
`chat/page.tsx` → `app/api/dify/chat/route.ts` → Dify for the chat orchestrator. Both hold their
respective keys server-only. If you add a new external call from a client component, proxy it the same
way — don't read a secret into a `NEXT_PUBLIC_*` var, since anything with that prefix ships in the
client bundle.

**Okta SSO gates `/dsl` only** (chosen deliberately over gating the whole app — see Conventions). The
pieces: `middleware.ts` (route matcher `['/dsl/:path*']`, redirects unauthenticated requests to Okta
sign-in), `lib/auth.ts` (shared `authOptions`, JWT session strategy, Okta OIDC provider), the route
handler at `app/api/auth/[...nextauth]/route.ts`, and `components/SessionProviderWrapper.tsx` (wraps
the whole app in `layout.tsx` so `useSession()` works client-side). `dsl/page.tsx` calls `useSession()`
and uses `session.user.name` (falling back to email) wherever the UI used to have a free-text "your
name" input — both the scan trigger and the `ApprovalForm` sign-off name field. This replaced manual
name entry with a verified identity; the "reason/justification" field is still free text by design —
only identity is meant to be verified, not the justification itself.

The Okta org backing this is a free **Integrator Free Plan** org (Okta's own UI explicitly says "not
recommended for production uses" — accepted as a known limitation for a capstone deployment, not
something to silently work around). A few non-obvious things about this specific org, worth knowing
before touching Okta config again:
- **Federation Broker Mode and per-user/group app assignment are mutually exclusive** — Okta will
  refuse to let you assign the app to anyone while FBM is on ("It is not possible to assign users to an
  AppInstance that has Federation Broker Mode enabled"). FBM is currently **off**, with the app
  assigned directly to the one real user. If you want group-based UAT access later (recommended over
  per-person assignment — create a group, assign the app to the group, manage membership instead),
  FBM must stay off for that too.
- **The `default` Authorization Server needs at least one Access Policy** (Security → API → default →
  Access Policies) or every single login fails with a generic "Policy evaluation failed" `access_denied`
  error, regardless of correct credentials/MFA. A policy assigned to "All clients" permitting
  `authorization_code` exists now — don't delete it.
- **The `default` Authorization Server's built-in `sub` claim was previously overridden** with a broken
  expression (`(appuser != null) ? appuser.userName : app.clientId` — `appuser` isn't valid Okta
  Expression Language, causing `server_error (The 'sub' system claim could not be evaluated.)` on every
  token exchange). It's fixed to `user.getInternalProperty("id")` (Security → API → default → Claims).
  If Okta login ever starts failing again with that exact error, check this claim first before assuming
  it's a code regression.

**Dify orchestration** lives outside this repo (in the Dify UI/Docker instance) and is version-tracked
here only as YAML exports under `dify-data/`. There are 16 domain sub-workflows (4 per insurance type —
life/health/critical_illness/disability — each with Claim_Details, Policy_Details,
Claim_and_Policy_Details, Assess_Claim variants) plus one orchestrator (`Test_Orchestrator-1.yml`) that
LLM-classifies intent and routes to the right sub-workflow. The `*_Assess_Claim` workflows are the
core: fetch claim + policy + eligibility rules → LLM rule-by-rule eligibility check → LLM policy
document analysis → LLM verdict synthesis (APPROVE/REJECT/REFER_FOR_FURTHER_REVIEW) → LLM-as-Judge
quality scoring → POST to `/assessment-logs`. Structured outputs with JSON-schema enum constraints are
used at every inter-node boundary — this is the primary hallucination-control mechanism, not
incidental, per `PROJECT_CONTEXT.md` §5.

**DSL Change Management has two entry points that share one extraction implementation.** There are two
ways to trigger a scan:
1. `dsl_manager/` — a local CLI (`parser.py`, `diff.py`, `approvals.py`, `git_commit.py`,
   `__main__.py`). Parses one YAML file client-side and talks to the MCP server's generic CRUD
   endpoints (`POST /workflow-nodes`, `POST /change-approvals`).
2. `mcp_server/main.py`'s `/dsl/scan` + `/dsl/status` endpoints (bottom of the file) — scans every
   `*.yml` in `dify-data/` **on the server's own filesystem**. This is what the frontend's DSL
   Management view (`frontend/app/dsl/page.tsx` → `lib/mcp.ts: scanDslFolder/getDslStatus`) calls.

Both call the *same* `parse_workflow()` / `hash_content()` (from `dsl_manager/parser.py`) and
`compute_diff()` (from `dsl_manager/diff.py`) — `mcp_server/main.py` imports them (it prepends the repo
root to `sys.path` at import time so the sibling `dsl_manager` package resolves regardless of the
server's cwd). **Node-extraction/hashing/diff logic must only ever be changed in `dsl_manager/`** —
don't reimplement it in `main.py` again, or the two entry points will silently start detecting
different things as "changed."

Both entry points also populate the same `change_approvals` fields (`node_type`, `new_content`,
`new_hash`), so `/change-approvals/{id}/approve`'s promotion-to-`workflow_nodes` step fires identically
regardless of which path created the pending approval. **These three columns aren't in the schema
documented in `PROJECT_CONTEXT.md` §7 — they were added via `ALTER TABLE change_approvals ADD COLUMN`
after the code's assumption that they existed went unverified until the first real "changed node" ever
hit that insert.** If you ever recreate this table from scratch, add them, or the scan/approve flow will
fail with a Postgrest "column not found" error identical to what surfaced the first time.

`change_approvals.node_id` is a UUID FK to `workflow_nodes.node_id` (the Postgres-generated PK for a
stored node) — **it is not the same thing as a parsed node's own `node_id` field**, which is Dify's
internal per-node identifier from the YAML (a non-UUID string, e.g. a timestamp). Both the CLI
(`__main__.py::cmd_scan`) and the server (`main.py`'s `/dsl/scan`) look up the *stored* node's real UUID
(`existing["node_id"]`) when a node has changed, and pass `None` when a node is brand new (no stored row
yet to reference). Don't put the Dify-internal `node_id` from `parse_workflow()` directly into this
field — Postgres will reject it with an "invalid input syntax for type uuid" error.

The CLI additionally commits to GitHub (`git_commit.py`) and re-stashes the resulting `git_commit_hash`
onto `workflow_nodes` after approving — the server-side `/change-approvals/{id}/approve` endpoint does
not touch GitHub at all, so approvals made from the frontend DSL view update Supabase but never produce
a commit. This is a deliberate, temporary gap: there's no dedicated GitHub branch for DSL governance
commits yet — don't add server-side git-commit-on-approve until that's set up and asked for.

**Database** (Supabase, Postgres, RLS on all tables, MCP server uses the secret/service key to bypass
RLS): `policies`, `claims`, `claim_documents`, `eligibility_rules` are domain data (synthetic — 1,000
policies / 1,522 claims / 24 eligibility rules, generated by `generate_data.py` with `random.seed(42)`
and Singapore-statistics-based claim-frequency weighting per policy type). `assessment_logs` is the
governance audit trail for every AI recommendation, linking to an MLflow run via `mlflow_run_id` plus
four LLM-as-Judge scores. `workflow_nodes` / `change_approvals` back the DSL Change Management System
above. Full column-level schema is in `PROJECT_CONTEXT.md` §7 — check it before writing new queries
rather than guessing column names.

**MLflow / Databricks** (`mlflow_tracker.py`, `setup_mlflow.py`) serves three roles: prompt version
registry (every system prompt versioned; `prompt_version` logged with every assessment), experiment
tracking for the prompting-strategy evaluation study (direct / chain-of-thought / structured-output /
combined, across the 4 claim types — the `evaluation/` scripts referenced in `PROJECT_CONTEXT.md` are
not yet built), and the production audit link (`assessment_logs.mlflow_run_id`). `MLflowTracker` is
non-strict by default (`strict=False`): if Databricks credentials are missing or logging fails, it
prints a warning and returns `None` rather than raising — don't assume a `None` run_id means anything
broke upstream.

**Frontend** (`frontend/app/`) is a Next.js 14 App Router project with four routed views: `chat/`,
`audit/` (assessment_logs browser), `dashboard/` (Recharts analytics), `dsl/` (diff viewer via
`react-diff-viewer-continued` + approval form, scan trigger). `frontend/components/ui/` exists but is
currently empty — there's no shared component library yet, each page is largely self-contained.
`frontend/lib/mcp.ts` is the typed client for the MCP server; `frontend/lib/fmt.ts` has date formatting
that assumes Supabase timestamps may be missing a timezone suffix and forces UTC.

## Conventions specific to this repo

- Don't add a data-access path that bypasses the MCP server for Supabase/Databricks data, or the Dify
  proxy route for Dify calls — they're the intended governance/audit chokepoints (MAS AIRG / IMDA
  alignment is a stated project requirement).
- New LLM-facing structured output should use JSON schema + enum constraints, matching the existing
  pattern — a deliberate hallucination-control decision (`PROJECT_CONTEXT.md` §5), not a style choice.
- Prompt/DSL changes belong in the `dsl_manager` / `/dsl/scan` approval flow, not ad-hoc edits to
  `dify-data/*.yml` followed by a plain `git commit`.
- `mcp_server/.env` and `frontend/.env.local` hold live credentials (Supabase, Databricks, GitHub
  token, Dify API key, Okta client secret, NextAuth secret) and are gitignored — never commit them or
  echo their contents into generated files.
- Env vars added locally must be mirrored in the corresponding deployed platform's dashboard (Vercel
  for frontend vars, Render for MCP server vars) — they don't sync automatically, and a rename on one
  side without the other breaks the deployed app silently. This bit us with the Dify key rename and
  the Okta/NextAuth vars.
- `/dsl` is intentionally the only route gated by Okta — don't extend the `middleware.ts` matcher to
  other routes without being asked; Chat/Audit Log/Dashboard staying open was a deliberate scope
  decision, not an oversight.
