# AIA Capstone Project — Full Context Document
> **For:** Claude Code and any AI assistant picking up this project  
> **Author:** Jasbir Kaur (2302990), Applied Computing (FinTech), Singapore Institute of Technology  
> **Last updated:** 14 July 2026 (active build log)

---

## 1. Project Identity

| Field | Detail |
|---|---|
| **Project Title** | Governed Multi-Agent AI System for Insurance Claims Assessment |
| **Module** | BAC3004 Capstone Project, Singapore Institute of Technology (SIT) |
| **Student** | Jasbir Kaur, Matriculation No. 2302990 |
| **Programme** | Applied Computing (FinTech) |
| **Organisation** | AIA Singapore Pte. Ltd. (UEN: 201106386R) |
| **Project Period** | 5 January 2026 – 7 August 2026 |
| **Report Deadline** | 19 July 2026 |
| **Build Completion Target** | End of June 2026 |
| **Testing / UAT Target** | 1 July – 14 July 2026 |
| **Industry Supervisor** | Kartik-K Mahadevan, Associate Director, AI & Machine Learning, Technology – Data Architecture Development |
| **Academic Supervisor** | Assoc. Prof. Harminder Singh, SIT (harminder.singh@singaporetech.edu.sg) |
| **GitHub Repo** | https://github.com/jas12481/sit_capstone (public) |
| **MLflow Experiment** | /Users/jasclapforyou@gmail.com/Claims_Assessment_Prompting_Study |
| **MLflow Experiment ID** | 2726789194105433 |
| **Databricks Host** | https://dbc-0dc2996b-ae12.cloud.databricks.com |
| **MCP Server (cloud)** | https://sit-capstone.onrender.com |

---

## 2. Project Overview and Unique Contribution

### What This Project Is

A **governed multi-agent AI system** for AIA Singapore's insurance claims operations department. Claims officers interact with a custom web UI, submit natural language queries about claims and policies, and the system orchestrates specialised AI agents to retrieve data, reason over it, and produce structured, explainable, auditable outputs.

The system is modelled on a real internal AIA initiative. Live AIA data cannot be used for academic purposes — a synthetic dataset mirrors the real data structure without exposing proprietary information.

### The Unique Contribution

> **A reference implementation of the IMDA Model AI Governance Framework (2020) and MAS Guidelines on AI Risk Management for Financial Institutions (2025) for agentic AI in insurance claims operations — incorporating an empirical evaluation study of prompting strategies for hallucination mitigation, an LLM-as-Judge quality evaluation layer, a governed DSL change management system for AI workflow configurations, and a prompt optimisation agent for continuous quality improvement.**

This project makes **five distinct contributions:**

1. A working governed agentic AI system satisfying two Singapore regulatory frameworks
2. An empirical study comparing four prompting strategies across 20 test claims (hallucination rate, accuracy, clause reference validity) — tracked via MLflow on Databricks
3. An LLM-as-Judge automated quality scoring layer linked to MLflow after every assessment
4. A DSL change management system providing governed version control for Dify workflow configurations with mandatory human sign-off
5. A prompt optimisation agent that reads MLflow metrics and proposes targeted prompt improvements through the governed change management pipeline

### Context: Relationship to Kenix's Project

Kenix (business team intern) covers the end-to-end business process of AI-assisted claims handling. This project occupies the **AI engineering layer**:
- **Kenix:** How the business process should be redesigned around AI
- **Jasbir:** How the AI must be built, governed, evaluated, and audited to be safe in a regulated environment

These are complementary. The technical contributions cannot be made from the business process side.

### Why This Matters

AIA Singapore is a MAS-regulated financial institution. Any AI system used in claims processing must satisfy the MAS AI Risk Management Guidelines (2025). Generative AI in this context must be:
- **Governed** — traceable, auditable, satisfying MAS AIRG requirements
- **Explainable** — clause-level reasoning visible to officers, auditors, compliance
- **Consistent** — structured output constraints prevent free-form hallucination
- **Evaluated** — systematic measurement of quality via MLflow and LLM-as-Judge
- **Change-controlled** — any modification to AI logic must be signed off before deployment
- **Self-improving** — the system monitors its own quality and proposes improvements within governance bounds

---

## 3. Full System Components

The project has **eight major components:**

```
Component 1: Multi-Agent Assessment System (Dify)
Component 2: MCP Server (FastAPI)
Component 3: Database Layer (Supabase)
Component 4: MLflow Experiment Tracking + Prompt Registry (Databricks)
Component 5: LLM-as-Judge Quality Evaluation Layer
Component 6: DSL Change Management System
Component 7: Prompt Optimisation Agent
Component 8: Frontend (React + Vercel)
```

---

## 4. Regulatory and Research Foundation

### Primary Regulatory Frameworks

**1. IMDA Model AI Governance Framework, Second Edition (2020)**
- Singapore's foundational voluntary framework for responsible AI deployment
- Four pillars: Internal Governance, Human Involvement in AI Decision-Making, Operations Management, Stakeholder Communication
- URL: https://www.imda.gov.sg/-/media/imda/files/infocomm-media-landscape/sg-digital/tech-pillars/artificial-intelligence/second-edition-of-the-model-ai-governance-framework.pdf

**2. MAS Guidelines on AI Risk Management for Financial Institutions (November 2025)**
- Issued by MAS on 13 November 2025. Applies to ALL MAS-regulated financial institutions including AIA Singapore
- Covers: AI governance structures, AI risk management systems, AI lifecycle controls, capabilities and capacity
- Explicitly covers generative AI and agentic AI systems
- Complements MAS FEAT principles (Fairness, Ethics, Accountability, Transparency)
- URL: https://www.mas.gov.sg/publications/consultations/2025/consultation-paper-on-guidelines-on-artificial-intelligence-risk-management

### System-to-Regulatory Mapping

| IMDA Pillar | System Implementation |
|---|---|
| **Internal Governance** | Dify self-hosted; MLflow Prompt Registry; assessment_logs audit table; DSL Change Management System |
| **Human Involvement** | System recommends only (APPROVE/REJECT/REFER); REFER = mandatory human review; full reasoning trace visible; confidence levels guide human scrutiny; prompt optimisation agent suggests only, never auto-applies |
| **Operations Management** | JSON schema enum constraints (robustness); MLflow tracking (reproducibility); audit log (auditability); LLM-as-Judge (automated QA); chain-of-thought + grounding (hallucination control); prompt optimisation agent (monitoring and review) |
| **Stakeholder Communication** | Claims officers: assessment reports with clause refs; Management: dashboard + analytics; Auditors: full audit trail; Compliance: traceable structured outputs |

| MAS AIRG Area | System Implementation |
|---|---|
| **Governance Structures** | Defined roles: MCP (data), Dify (orchestration), MLflow (prompt), audit log (decisions), DSL system (change control) |
| **AI Risk Management Systems** | Human-over-the-loop; REFER for uncertainty; confidence logging; LLM-as-Judge quality gate |
| **AI Lifecycle Controls** | MLflow Prompt Registry versions every prompt; DSL Change Management requires sign-off for any workflow change; assessment_logs links every decision to prompt version |
| **Capabilities and Capacity** | Empirical evaluation study: 4 strategies × 20 claims = 80 MLflow runs; prompt optimisation agent continuously monitors and proposes improvements |

### Key Research Literature

**On LLM Hallucination:**
- Huang et al. (2025). Survey on hallucination in LLMs. ACM Trans. Inf. Syst., 43, 1-55.
- Frontiers in AI (2025). doi:10.3389/frai.2025.1622292
- arXiv:2601.02739 — Mitigating Prompt-Induced Hallucinations via Structured Reasoning

**On LLMOps and MLflow:**
- MLflow docs: https://mlflow.org/docs/latest/genai/
- Commey (2026). Evaluation-Driven Iteration for LLM Applications. arXiv:2601.22025
- Databricks MLflow prompt versioning: https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/

**On LLM-as-Judge:**
- Zheng et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS 2023.
- arXiv:2306.05685 — LLM-as-Judge for automated evaluation

**On AI Governance in Insurance:**
- Frontiers in AI (2025). doi:10.3389/frai.2025.1568266
- Databricks + Deloitte (2025). AI Governance for Insurance. https://databricks.com/blog
- Baker Tilly (2025). Regulatory Implications of AI for Insurance

**Citation format:** IEEE throughout the final report.

---

## 5. Core Design Principles

1. **Agents must reason, not just retrieve.** Every agent does something a database query cannot. This is the central argument for the agentic architecture.

2. **LLM reasoning over unstructured text is deliberate.** Schema is lean. `policy_text` contains the full contract. The LLM reads it to handle product-level differences rather than hardcoding logic into 60 separate structured schemas.

3. **Security and explainability drove platform selection.** Dify chosen over LangChain/LlamaIndex for: no sprawling dependency chain; visual workflow builder readable by non-technical stakeholders; aligns with MAS AIRG governance requirements.

4. **Data never leaves the controlled environment.** Dify self-hosted. No data through third-party servers. Essential for MAS compliance.

5. **MCP server is the only data access point.** Agents never query Supabase directly. Clean, auditable, governable layer — implements MAS AIRG "key AI risk management systems."

6. **Structured outputs with enum constraints prevent hallucination at the output layer.** Every inter-node LLM output uses JSON schema with enum values. This is a hallucination control mechanism.

7. **Human-over-the-loop by design.** System recommends, never decides. REFER is the default for uncertainty. Implements IMDA human-centric principle.

8. **Every change to AI logic must be signed off.** The DSL Change Management System enforces this. No prompt or code change can enter production without attribution and approval. Implements MAS AIRG lifecycle controls.

9. **The system monitors its own quality.** The prompt optimisation agent reads MLflow metrics and proposes improvements, but never auto-applies them. All suggestions enter the governed change management pipeline. Implements IMDA "Operations Management — monitoring and review."

---

## 6. Tech Stack

| Component | Technology | Notes |
|---|---|---|
| **LLM Orchestration** | Dify (self-hosted Docker) | 6 CPU, 8GB RAM. `http://localhost`. GPT-5.2 default |
| **Database** | Supabase (Singapore region, ap-southeast-1) | PostgreSQL with RLS on all tables |
| **Storage** | Supabase Storage (policy-documents bucket) | 1,000 policy PDFs |
| **MCP Server** | Python FastAPI | `mcp_server/main.py`. Supabase secret key bypasses RLS. Deployed on Render |
| **Frontend** | React + Vercel | Chat UI + Audit Log + Management Dashboard + DSL Change Management UI |
| **Authentication (DSL view)** | Okta (Integrator Free Plan) + NextAuth.js | SSO gating `/dsl` only; replaces free-text approver name with verified identity |
| **PDF Generation** | ReportLab (Python) | 1,000 legal contract PDFs |
| **Experiment Tracking** | MLflow + Databricks Community Edition | Prompt Registry, evaluation tracking, LLM-as-Judge metrics |
| **Version Control** | GitHub (sit_capstone, public) | Connected to Vercel for auto-deploy |
| **Editor / Terminal** | Cursor | Primary development environment |
| **LLM Provider** | OpenAI GPT-5.2 | All nodes — consistency across evaluation study |
| **Python Version** | 3.11 | Migrated from 3.9 |

### URLs
- Dify (local): `http://localhost`
- MCP Server (local): `http://localhost:8000`
- MCP Server (cloud): `https://sit-capstone.onrender.com`
- Dify → MCP (Docker): `http://host.docker.internal:8000`
- MLflow UI: `https://dbc-0dc2996b-ae12.cloud.databricks.com/ml/experiments/2726789194105433`

### Folder Structure
```
sit_capstone/
├── mcp_server/
│   ├── main.py                  # All 24 endpoints (v2.1.0)
│   └── .env                     # SUPABASE_URL, SUPABASE_KEY, DATABRICKS_HOST, DATABRICKS_TOKEN,
│                                 # GITHUB_TOKEN, GITHUB_REPO, GITHUB_GOVERNANCE_BRANCH (not committed)
├── frontend/                    # React (Vercel) — 4 views
├── dify-data/                   # FROZEN historical artifact only (2026-07-14) — no longer read by the
│                                 # running system; "current" workflow state lives in the dify-workflows
│                                 # Supabase Storage bucket instead (see §11, §14)
├── evaluation/
│   ├── test_claims.json         # 20 test claims + ground truth
│   ├── run_evaluation.py        # 4 strategies × 20 claims = 80 MLflow runs
│   ├── metrics.py               # Hallucination detection + scoring functions
│   └── prompt_advisor.py        # Prompt optimisation agent
├── dsl_manager/
│   ├── parser.py                # Parses Dify YAML, extracts LLM/code/agent nodes; parse_workflow_content()
│   │                             # (2026-07-14) parses in-memory YAML text, not just local files
│   ├── diff.py                  # Diffs new DSL against stored version
│   ├── approvals.py             # Sign-off workflow
│   ├── git_commit.py            # Per-node commits to main + whole-file snapshots to dsl-governance-history
│   └── __main__.py              # CLI: init/scan/approve/reject/list + snapshot/history (2026-07-14)
├── migrate_workflows_to_storage.py  # One-time dify-data/ → dify-workflows Storage seed (2026-07-14)
├── setup_mlflow.py              # One-time MLflow + Databricks setup script
├── generate_data.py
├── generate_pdfs.py
├── PROJECT_CONTEXT.md
└── README.md
```

---

## 7. Database Schema (Supabase)

All tables: RLS enabled. MCP server uses secret key. Frontend never touches Supabase directly.

### `policies`
| Column | Type | Notes |
|---|---|---|
| `policy_id` | TEXT PK | e.g. POL-LI-0001 |
| `customer_id` | TEXT | Loose reference — no customers table |
| `agent_id` | TEXT | Financial adviser |
| `policy_type` | TEXT | life, health, critical_illness, disability |
| `policy_name` | TEXT | One of 60 fictional products |
| `policyholder_name` | TEXT | |
| `sum_assured` | NUMERIC | SGD |
| `premium_amount` | NUMERIC | SGD |
| `premium_frequency` | TEXT | monthly, quarterly, annual |
| `start_date` | DATE | |
| `end_date` | DATE | |
| `status` | TEXT | active, lapsed, terminated |
| `pdf_url` | TEXT | Supabase Storage URL |
| `policy_text` | TEXT | ~17,000 chars full contract |
| `policy_summary` | TEXT | 200-300 word summary |
| `created_at` | TIMESTAMP | |

### `claims`
| Column | Type | Notes |
|---|---|---|
| `claim_id` | TEXT PK | e.g. CLM-0001 |
| `policy_id` | TEXT FK | → policies |
| `customer_id` | TEXT | Denormalised |
| `claim_type` | TEXT | life, health, critical_illness, disability |
| `claim_category` | TEXT | See below |
| `claim_date` | DATE | Submitted |
| `incident_date` | DATE | Event/diagnosis |
| `claim_amount` | NUMERIC | SGD |
| `approved_amount` | NUMERIC | |
| `payment_date` | DATE | |
| `status` | TEXT | pending, approved, rejected, under_review. Randomly assigned at data-generation time (`generate_data.py`'s `CLAIM_STATUS_POOL`, weighted ~3:2:1:1 approved:pending:under_review:rejected) — **not** derived from `eligibility_rules`, so it's not ground truth against anything the assessment pipeline computes. **Write-back added 2026-07-16:** a claim's first real assessment while `status == "pending"` finalizes it (APPROVE→approved, REJECT→rejected, REFER_FOR_FURTHER_REVIEW→under_review) — see `POST /assessment-logs` in §10. Already-decided claims are never touched by this — re-assessing one is an audit re-check, not intake, and must never silently overwrite the existing record. This makes the write-back self-limiting: once a claim's status is set (by write-back or by the original random label), later re-assessments of the same claim can't overwrite it again |
| `rejection_reason` | TEXT | On write-back, derived from the primary failed mandatory rule in the assessment's `rule_checks` (e.g. *"Accidental Death Evidence: required death-claim documents not evidenced as complete"*). **Fixed 2026-07-16:** at data-generation time, this was drawn from one shared 8-reason pool applied to every domain — e.g. a life claim could be randomly assigned "Survival period not satisfied" (a critical_illness-only concept) or "Diagnosis does not meet the clinical criteria defined in the policy" (unmodelable by any rule, any domain, at the time). `generate_data.py`'s `valid_rejection_reasons()` now draws from a domain-and-category-aware pool matching the actual rule set (see `eligibility_rules` below); `fix_rejection_reasons.py` was a one-time correction for the 227 already-generated rejected claims (61 reassigned, plus 17 `claim_documents` rows removed where a claim's own "insufficient documents" reason was contradicted by a document actually being present) |
| `assigned_officer` | TEXT | |
| `notes` | TEXT | |
| `created_at` | TIMESTAMP | |
| `diagnosis` | TEXT | **Added 2026-07-06** — plain-language diagnosis/condition for the claim. Needed because `RULE-HE-005` (Pre-existing Condition Exclusion) requires knowing what the condition actually is; originally there was no field anywhere in the schema for this, making the rule permanently unverifiable regardless of any other data. **Backfilled for life/critical_illness/disability 2026-07-16** (`backfill_claim_evidence_v2.py`) — was health-only until then, meaning the new `RULE-LI-006`/`RULE-CI-007`/`RULE-DI-008` pre-existing-condition rules would otherwise always return UNKNOWN. |
| `condition_is_pre_existing` | BOOLEAN | **Added 2026-07-06** — resolves `RULE-HE-005` definitively once set. Nullable — absence means "unknown," which a careful assessor should still treat as unable to confirm the rule, not as a pass. |

**Claim categories:**
- life: death, accidental_death, total_permanent_disability
- health: hospitalisation, surgical, outpatient, emergency
- critical_illness: cancer, heart_attack, stroke, kidney_failure, major_organ_transplant
- disability: total_temporary_disability, total_permanent_disability, partial_permanent_disability, occupational_disability

### `claim_documents`
| Column | Type | Notes |
|---|---|---|
| `document_id` | UUID PK | |
| `claim_id` | TEXT FK | |
| `document_type` | TEXT | |
| `document_name` | TEXT | |
| `pdf_url` | TEXT | |
| `uploaded_at` | TIMESTAMP | |
| `content_summary` | TEXT | **Added 2026-07-06** — plain-text summary of what the document actually states. Without this, this table only ever stored metadata (type/name/url), so a rule like `RULE-DI-007` ("incident must not be self-inflicted **as stated in medical report**") could never be confirmed no matter which document type was present — presence alone can't satisfy a rule that depends on document content. **Health had zero rows in this table at all until 2026-07-16** (`medical_report` backfilled for `RULE-HE-007`), and life only had documents for `accidental_death` — `death`/`total_permanent_disability` categories got `death_certificate`/`tpd_medical_certification` the same day, for `RULE-LI-007`/`RULE-LI-008`. |

### `eligibility_rules`
| Column | Type | Notes |
|---|---|---|
| `rule_id` | TEXT PK | e.g. RULE-LI-001 |
| `policy_type` | TEXT | |
| `rule_name` | TEXT | |
| `rule_description` | TEXT | |
| `condition` | TEXT | |
| `is_mandatory` | BOOLEAN | FAIL = hard rejection |

30 rules: 8 life, 7 health, 7 critical illness, 8 disability (originally 24: 5/6/6/7 — 6 added
2026-07-16, see below).

**Rule-coverage review and additions (2026-07-16).** Cross-referencing all 8 synthetic
`rejection_reason` categories (`generate_data.py`) against what the rule set could actually
verify found real, precise gaps — not evenly distributed:
- `RULE-LI-006` Pre-existing Condition Exclusion (life, `death`/`total_permanent_disability`
  categories only — not `accidental_death`)
- `RULE-LI-007` Death Certificate Evidence (life, `death` category only)
- `RULE-LI-008` TPD Medical Certification (life, `total_permanent_disability` category only —
  doubles as both a documentation check and a clinical/severity-definition check)
- `RULE-CI-007` Pre-existing Condition Exclusion (critical_illness — CI previously had none)
- `RULE-DI-008` Pre-existing Condition Exclusion (disability — disability previously had none)
- `RULE-HE-007` Medical Documentation Required (health — health previously had zero
  documentation requirement at all; `RULE-HE-004` only checks facility approval)

Deliberately **not** added: a health "clinical criteria" rule — health policies aren't
diagnosis-restricted the way critical_illness is (no covered-illness list concept), so a
rule there would be artificial. That rejection reason is correctly excluded from health's
pool in `generate_data.py` instead (see below).

All 6 new rules required **zero Dify workflow changes** — `rule_by_rule_eligibility_check`
fetches rules dynamically per `policy_type` via `/eligibility-rules?policy_type=X`, so new
rows are picked up automatically. Verified live: adding `RULE-HE-007` alone (before its
backing data existed) correctly flipped a real health assessment from APPROVE to REJECT,
confirming the new rule was evaluated with zero workflow changes.

### `assessment_logs` *(Governance — audit trail)*
| Column | Type | Notes |
|---|---|---|
| `log_id` | UUID PK | |
| `claim_id` | TEXT | |
| `workflow_type` | TEXT | life, health, critical_illness, disability |
| `recommendation` | TEXT | APPROVE, REJECT, REFER_FOR_FURTHER_REVIEW |
| `confidence_level` | TEXT | HIGH, MEDIUM, LOW |
| `mandatory_rules_failed` | INTEGER | |
| `total_rules_passed` | INTEGER | |
| `coverage_conclusion` | TEXT | |
| `model_version` | TEXT | e.g. gpt-5.2 |
| `prompt_version` | TEXT | From MLflow Prompt Registry e.g. life_rule_check_v1.2. **Note (found 2026-07-16):** the value Dify actually sends is a static default baked into each workflow's `prepare_assessment_log_payload` node (e.g. `life_assess_claim_v1.0`) — never bumped by Dify itself when the underlying prompt changes. `main.py`'s `PROMPT_VERSION_BUMPS` overrides the known-stale value server-side going forward (not retroactive — see §10) |
| `mlflow_run_id` | TEXT | Links to MLflow run. **Fixed 2026-07-16** — was always empty for every real assessment (confirmed: 0 of 345 rows populated) because nothing in the live Dify pipeline ever created an MLflow run; the evaluation harness created its own, but never wired that ID back into the matching row. `POST /assessment-logs` now creates a real Databricks run itself (`_log_assessment_to_mlflow_and_persist` in `main.py`) and persists the ID here — see §10 for why this is a `BackgroundTask`, not synchronous |
| `judge_completeness_score` | FLOAT | 0-1 |
| `judge_consistency_score` | FLOAT | 0-1 |
| `judge_hallucination_risk_score` | FLOAT | 0-1 (1 = no hallucination) |
| `judge_clarity_score` | FLOAT | 0-1 |
| `judge_overall_score` | FLOAT | **Redesigned 2026-07-15/16** — genuinely deterministic now: a dedicated `compute_judge_overall` code node computes the simple average of the 4 sub-scores. Previously the judge LLM invented this number itself in the same call as the sub-scores, with no defined relationship to them — a "fake" composite metric with no formula behind it (see §13) |
| `assessed_at` | TIMESTAMP | |
| `rule_checks` | JSONB | **Added 2026-07-15** (`ALTER TABLE assessment_logs ADD COLUMN rule_checks jsonb;`) — array of `{rule_id, rule_name, result (PASS/FAIL/UNKNOWN/NOT_APPLICABLE), is_mandatory, reason, evidence_fields[]}`, one entry per eligibility rule evaluated. Closes a real logic gap: `rule_by_rule_eligibility_check` always computed this per-rule reasoning, but it was discarded after `compute_rule_counts` reduced it to just two integers (`mandatory_rules_failed`/`total_rules_passed`) — a claim could land on REFER_FOR_FURTHER_REVIEW with zero visibility into *which* rule caused it or why. Now persisted end-to-end (all 4 `*_Assess_Claim` workflows) and consumed by `Explain_Assessment_Reasoning` to cite specific rules instead of speaking generically. `AssessmentLogCreate.rule_checks` accepts `Union[str, List[dict]]` — Dify's HTTP node sends it as a native JSON array, not a pre-serialized string as originally assumed |
| `status_cross_check` | TEXT | **Added 2026-07-16** (`ALTER TABLE assessment_logs ADD COLUMN status_cross_check text;` + `status_cross_check_note text;`) — CONSISTENT or MISMATCH, computed only when the assessed claim already had a decided `status` (the complementary case to the write-back above — never both on the same row). Purely observational: computed entirely server-side in `POST /assessment-logs`, after the fact, from data already in the request — no Dify workflow changes needed and none touch the verdict. On MISMATCH, `status_cross_check_note` holds a plain-language reason (e.g. *"recorded status is 'rejected' (reason: Policy was lapsed at time of incident), but AI recommendation is 'APPROVE'"*). Written via a separate, isolated `UPDATE` after the main insert (own try/except) specifically so a missing column on an un-migrated deployment can never break the core assessment-log write |
| `status_cross_check_note` | TEXT | See above — only set on MISMATCH |

### `assessment_explanations` *(Explain Assessment Reasoning — added 2026-07-14)*
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `log_id` | TEXT FK | → assessment_logs.log_id — **not** claim_id-keyed like fraud/missing-docs below, because one claim can have multiple assessment_logs rows and an explanation is tied to one specific verdict, not the claim in general |
| `claim_id` | TEXT | Denormalised, for lookup convenience |
| `explanation_text` | TEXT | Plain-language explanation, now cites specific `rule_checks` entries by rule name/ID rather than speaking generically |
| `generated_by` | TEXT | |
| `generated_at` | TIMESTAMP | |

### `missing_documentation_checks` *(Missing Documentation Advisor — added 2026-07-14)*
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `claim_id` | TEXT | Keyed by claim, like fraud checks — reflects the claim's current state, not one specific assessment run |
| `all_requirements_met` | BOOLEAN | |
| `missing_documents` | JSONB | Array of `{document_type, linked_rule_id, reason}` |
| `submitted_documents_summary` | TEXT | |
| `checked_by` | TEXT | |
| `checked_at` | TIMESTAMP | |

Frontend shows this feature for `REFER_FOR_FURTHER_REVIEW` rows always — the workflow's own prompt
frames its purpose as "what's still required to complete assessment," which only applies when
assessment couldn't be completed. **Extended to REJECT rows 2026-07-16**, scoped via
`rule_checks.evidence_fields` — shown only when the primary failed mandatory rule's evidence pointed at
`claim_documents` rather than `policy_record`/`claim_record`, a deterministic signal that the rejection
was document-related (see §16).

### `fraud_risk_checks` *(Fraud/Anomaly Risk Signals)*
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `claim_id` | TEXT | |
| `risk_level` | TEXT | LOW, MEDIUM, HIGH |
| `flags` | JSONB | Array of `{signal, explanation}` |
| `recommended_action` | TEXT | proceed_normally, flag_for_investigation |
| `checked_by` | TEXT | |
| `checked_at` | TIMESTAMP | |

### `workflow_nodes` *(DSL Change Management)*
| Column | Type | Notes |
|---|---|---|
| `node_id` | UUID PK | |
| `workflow_name` | TEXT | e.g. "Life Claims Assessment" |
| `workflow_version` | TEXT | e.g. "v1.3" |
| `node_type` | TEXT | llm, code, agent |
| `node_name` | TEXT | e.g. "rule_by_rule_eligibility_check" |
| `node_content` | TEXT | Full prompt text or code |
| `content_hash` | TEXT | SHA256 — used for change detection |
| `committed_at` | TIMESTAMP | |
| `committed_by` | TEXT | |
| `git_commit_hash` | TEXT | |

### `change_approvals` *(DSL Change Management)*
| Column | Type | Notes |
|---|---|---|
| `approval_id` | UUID PK | |
| `node_id` | UUID FK | → workflow_nodes.node_id (the stored node's own PK — **not** Dify's internal per-node ID from the YAML, which isn't a UUID) |
| `workflow_name` | TEXT | |
| `node_name` | TEXT | |
| `node_type` | TEXT | llm, code, agent — added 2026-07-02, was missing from initial schema |
| `changed_by` | TEXT | Who submitted (can be "prompt_advisor_agent") |
| `approved_by` | TEXT | Who signed off |
| `change_reason` | TEXT | Mandatory justification |
| `diff_content` | TEXT | Before vs after |
| `new_content` | TEXT | Full new node content — added 2026-07-02, needed so `/change-approvals/{id}/approve` can promote to `workflow_nodes` without re-parsing the diff |
| `new_hash` | TEXT | SHA256 of `new_content` — added 2026-07-02, same reason |
| `status` | TEXT | pending, approved, rejected |
| `approved_at` | TIMESTAMP | |
| `git_commit_hash` | TEXT | After approval — only ever set via the `dsl_manager` CLI's `approve` command; the server-side `/change-approvals/{id}/approve` endpoint does not commit to GitHub |
| `created_at` | TIMESTAMP | |

---

## 8. Synthetic Data

- **1,000 policies** — 60 fictional products (15 per type), ~85% active
- **1,522 claims** — type-specific frequency based on MOH/LIA Singapore statistics
- **1,000 policy PDFs** — 11-page legal contracts (~23KB each)
- **30 eligibility rules** (originally 24: 5 life, 6 health, 6 CI, 7 disability — 6 added 2026-07-16, see §7)

**Claim frequency (MOH/LIA Singapore):**
- Health: avg 4.0/policy | Disability: avg 1.0/policy | CI: avg 0.5/policy | Life: avg 0.3/policy

**Products (60 total):**
- Life (15): AIA LifeGuard Essential/Plus/Premier, SecureLife 300/600/Platinum, WholeCover Basic/Premier, FamilyShield Income, MortgageGuard, SeniorGuard 65, BusinessGuard Term, EndowSave 20/25, ConvertTerm Plus
- Health (15): AIA MediShield Basic/Standard/Gold/Gold Max/Platinum, HealthPlus Essential/Comprehensive/Premier, CareShield Basic/Family, CancerCare Protect, MaternaCare, SeniorCare Shield, GlobalCare Elite, WellnessPlus Rider
- CI (15): AIA CI Essential 5/Protect 10/36/53, CI MultiClaim, EarlyCI Basic/Premier, CancerGuard Plus, HeartGuard Plus, CI Monthly Income, CI Protect 360, SeniorCI Cover, CI FamilyCare, CI BusinessGuard, DreadDisease Premier
- Disability (15): AIA DisabilityGuard Basic/Plus/Premier, IncomeShield Basic/Plus/Premier, TotalCover Disability, OccupationProtect, ExecutiveDisability, FreelanceShield, AccidentDisability, RehabPlus Disability, PartialDisability Cover, SeniorDisability Shield, GroupDisability SME

---

## 9. Component 1 — Multi-Agent Assessment System (Dify)

### System Architecture

```
User (Claims Officer) — Web UI (React, Vercel)
    ↓ natural language query
Orchestrator Chatbot (Dify advanced-chat workflow — Test_Orchestrator_1-1.yml)
    ↓ followup_router → query_type_router → intent_identifier → domain routing
    ├── life_agent   → [Life_Claim_Details, Life_Policy_Details,
    │                    Life_Claim_and_Policy_Details, Life_Assess_Claim, Claims_History]
    ├── health_agent → [Health_Claim_Details, Health_Policy_Details,
    │                    Health_Claim_and_Policy_Details, Health_Assess_Claim, Claims_History]
    ├── ci_agent     → [CI_Claim_Details, CI_Policy_Details,
    │                    CI_Claim_and_Policy_Details, CI_Assess_Claim, Claims_History]
    ├── disability_agent → [Disability_Claim_Details, Disability_Policy_Details,
    │                        Disability_Claim_and_Policy_Details, Disability_Assess_Claim, Claims_History]
    └── customer_history_agent → [Customer_History]   (bypasses domain resolution entirely —
                                   a customer can hold policies across multiple domains)
            ↓ all sub-workflows call
    MCP Server (FastAPI — Render cloud)
            ↓
    Supabase (PostgreSQL + Storage)
            ↓ assessments also write to
    assessment_logs → MLflow (Databricks)
```

### Refactored Workflow Design (June 2026)

The original monolithic 32-node workflow was refactored into four focused sub-workflows per insurance type, totalling 16 sub-workflows. All 16 are built and exported as DSL YAMLs. The orchestrator routes to them via 4 domain agent nodes (life_agent, health_agent, ci_agent, disability_agent), each holding 4 tools.

**All 16 sub-workflows:**

| Workflow | Purpose | Status |
|---|---|---|
| `Life_Claim_Details` | Fetch + format claim details | ✅ Done |
| `Life_Policy_Details` | Fetch + format policy details | ✅ Done |
| `Life_Claim_and_Policy_Details` | Fetch + format both combined | ✅ Done |
| `Life_Assess_Claim` | Full assessment + judge + audit log | ✅ Done |
| `Health_Claim_Details` | Fetch + format claim details | ✅ Done |
| `Health_Policy_Details` | Fetch + format policy details | ✅ Done |
| `Health_Claim_and_Policy_Details` | Fetch + format both combined | ✅ Done |
| `Health_Assess_Claim` | Full assessment + judge + audit log | ✅ Done |
| `CI_Claim_Details` | Fetch + format claim details | ✅ Done |
| `CI_Policy_Details` | Fetch + format policy details | ✅ Done |
| `CI_Claim_and_Policy_Details` | Fetch + format both combined | ✅ Done |
| `CI_Assess_Claim` | Full assessment + judge + audit log | ✅ Done |
| `Disability_Claim_Details` | Fetch + format claim details | ✅ Done |
| `Disability_Policy_Details` | Fetch + format policy details | ✅ Done |
| `Disability_Claim_and_Policy_Details` | Fetch + format both combined | ✅ Done |
| `Disability_Assess_Claim` | Full assessment + judge + audit log | ✅ Done |

**Standard output pattern across all workflows:**
```json
{"answer": "...", "suggestion_context": "..."}
```
The orchestrator uses `answer` for display and `suggestion_context` to build follow-up suggestions.

### Two Additional Shared Sub-Workflows (added 2026-07-13)

Beyond the 16 domain-specific workflows above, two new orchestrator intents were added — `claims_history`
(list all claims under one policy) and `customer_history` (all policies/claims for a customer, which may
span multiple policy types). Each is backed by **one shared Dify app**, not four domain-specific
duplicates — a deliberate correction after an initial per-domain-duplicate design was rejected as
unnecessary, since neither capability's logic actually differs by policy type:

| Workflow | Purpose | Registration |
|---|---|---|
| `Claims_History` | Fetch all claims for a given `policy_id`, format as a table + narrative | Registered as a shared tool on **all four** domain agents (`life_agent`/`health_agent`/`ci_agent`/`disability_agent`) |
| `Customer_History` | Fetch all policies **and** claims for a given `customer_id` (two parallel HTTP calls), cross-reference, explicitly tolerant of the customer holding policies in more than one domain | Called by a dedicated `customer_history_agent`, which bypasses per-domain resolution entirely |

Both follow the same shape as the other sub-workflows: Start → extract ID(s) (Code) → HTTP fetch(es) →
format response (LLM, structured output) → build suggestion context (LLM) → merge `{answer,
suggestion_context}` (Code) → End.

### Assessment Flow (Life_Assess_Claim)

```
Start (claim_id)
  ↓
Fetch Claim → Extract Claim Fields (Code)
  ↓
Fetch Policy → Extract Policy Fields (Code)
  ↓
Fetch Eligibility Rules (policy_type=life, returns 5 rules)
  ↓
Rule-by-Rule Eligibility Check (LLM GPT-5.2, structured output)
  — uses policy_summary not full policy_text (token limit)
  → rule_checks[] ({rule_id, rule_name, result, is_mandatory, reason, evidence_fields[]})
  ↓
compute_rule_counts (Code — deterministic)
  → mandatory_rules_failed, total_rules_passed, mandatory_unknown_count, all_not_applicable
    (counted in code from rule_checks, not LLM-recalled — see §15's deterministic-over-LLM pattern)
  ↓
Policy Document Analysis (LLM GPT-5.2, structured output)
  — uses full policy_data including policy_text
  → coverage_status, relevant_clauses[], applicable_exclusions[]
  ↓
Synthesise Final Verdict (LLM GPT-5.2, structured output)
  → recommendation (APPROVE/REJECT/REFER_FOR_FURTHER_REVIEW), confidence_level
  ↓
Format Final Report (LLM GPT-5.2, structured output)
  ↓
LLM-as-Judge (LLM GPT-5.2, structured output) ← Component 5, redesigned 2026-07-15/16
  — now grounded in real claim_record + policy_record, not just the generated report/verdict
  → judge_completeness/consistency/hallucination_risk/clarity_score (1.0-5.0 each) + judge_comments
  ↓
compute_judge_overall (Code — deterministic, new 2026-07-16)
  → judge_overall_score = simple average of the 4 sub-scores (previously LLM-invented, no formula)
  ↓
prepare_assessment_log_payload (Code) — assembles claim_id, verdict fields, judge scores,
  judge_overall_score, and rule_checks (JSON-serialized) into one payload
  ↓
POST to /assessment-logs (HTTP → MCP)
  ↓
Merge answer + suggestion_context (Code)
  ↓
End
```

### Hallucination Controls

1. JSON schema + enum constraints on all recommendation fields
2. Chain-of-thought: "show your working with exact values, calculate days between dates explicitly"
3. Grounding: "only derive from provided context, cite specific clauses"
4. Rules filtered by policy_type — model sees only 5-7 rules not all 24
5. Rule check and policy analysis are separate nodes — prevents cross-contamination
6. LLM-as-Judge scores hallucination risk on every run

### Critical Technical Notes for Dify

- HTTP nodes use **params not path variables** — Dify string handling bug with path params
- Rule-by-Rule node receives `policy_summary` not full `policy_data` — 272K token limit
- Policy Document Analysis receives full `policy_data` including `policy_text`
- Synthesise Verdict receives `structured_output` objects from both D5 and D6 nodes
- All four workflows published in Dify and available as tools for the orchestrator
- **DSL YAML exports are canonically in the `dify-workflows` Supabase Storage bucket, not
  `dify-data/`** (see §14) — `dify-data/*.yml` on local disk is a frozen historical artifact only,
  never read by the running system, and must never be edited as if it were current. Doing so once
  (2026-07-16) silently regressed the `rule_checks` persistence fix, because the local copy predated
  it — see §14's gotcha note before ever editing one of these workflow files directly again
- **Deliberate design boundary (2026-07-16): test/eval-only behavior should never be threaded through
  as a Dify Start-node input.** First attempt at the `claims.status` write-back opt-out (§10, §7) added
  `skip_status_update` as an optional Start-node field on all 4 `*_Assess_Claim` workflows — rejected
  before it shipped. Two problems: it would show up as a real input field on a production app real
  claims officers interact with, for a concern they have no reason to know about; and it's a flag
  someone testing manually in Dify's own run panel could easily forget to set, silently defaulting to
  "mutate real data." The fix that shipped instead keeps the Dify workflows completely untouched — the
  write-back always fires the same way for everyone, and the one caller that actually needs
  non-destructive repeat runs (`run_evaluation.py`'s combined strategy) snapshots/restores
  `claims.status` itself via a direct Supabase call around the Dify request, rather than the workflow
  needing to know it's being tested
- **Target-leakage fix (2026-07-16): `claim_record_json` no longer includes `status`/`rejection_reason`.**
  `extract_claims_fields` (node `1779138546683`, identical across all 4 workflows) used to
  `json.dumps()` the raw claim record wholesale into `claim_record_json` — the single variable all 5
  downstream LLM nodes (`rule_by_rule_eligibility_check`, `policy_document_analysis`,
  `synthesize_final_verdict`, `format_final_report`, `llm_judge`) read as "the claim." `status`/
  `rejection_reason` are the claim's *outcome* (a prior, unverified label, or what the write-back
  itself sets) — not evidence a rule can check — so no node deriving a fresh, independent verdict
  should be able to see the very outcome it's supposed to be producing. Caught via a real live
  incident: the rule-checker referenced `claim_record.status` in its reasoning and **deferred to a
  stale status over a genuinely-present document**, downgrading a rule that should have passed. (The
  stale status was itself self-inflicted test contamination from an earlier debugging session, but the
  behavior it exposed — the model trusting old status over fresh evidence when they conflict — is a
  real, general risk given `status` is largely random, see above.) Fixed with one line: `claim_record_json`
  now serializes `{k: v for k, v in c.items() if k not in ("status", "rejection_reason")}` instead of
  the raw record — a single choke point, so all 5 downstream nodes are fixed at once. Verified live:
  zero `claim_record.status`/`rejection_reason` references anywhere in a real assessment's
  `evidence_fields` afterward.

### Orchestrator Architecture (Test_Orchestrator_1-1.yml — canonical, final working version ✅)

Originally built entirely in Dify's advanced-chat UI. The `claims_history`/`customer_history` addition
(2026-07-13) was different: Claude Code hand-edited the exported YAML directly (node-by-node, fully
validated via `yaml.safe_load` + `ast.parse` on every embedded code block after each stage), then Jasbir
re-imported into Dify and reselected the UUID-dependent tool references via the UI dropdown (Dify assigns
these at publish time, so they can't be predicted/pre-filled in generated YAML). An older file,
`Test_Orchestrator-1.yml`, existed briefly as an intermediate export during this process and has since
been **deleted** — `Test_Orchestrator_1-1.yml` is the sole, confirmed-canonical orchestrator file.

**75 nodes, 17 conversation variables (added `customer_id`, `awaiting_customer_id`). All nodes use
GPT-5.2. Passes all test cases as of 2026-07-13, confirmed live through the actual Vercel chat UI (not
just Dify's own Run panel).**

**Key routing flow:**
```
User Input
  → detect_fresh_id_in_query (Code) — regexes query for CLM-/POL-/CUST- patterns → has_fresh_id
  → followup_router (LLM, structured_output, memory ON) — is_followup / reuse_last_intents / needs_ids
  → if/else_followup
      [fresh_id_override: has_fresh_id is true] → (same target as [new query] below — a fresh ID in the
          current message always forces re-extraction/re-classification, overriding the LLM's own
          is_followup judgment; see "Deterministic routing-bug fixes" below for why this exists)
      [followup] → va_prepare_followup_context_reuse → IF/ELSE 3
          [claims] → if_followup_has_no_ids → if_followup_reuse_last_intents
          [faq]   → faq_followup_explainer → answer
      [new query] → query_type_router (LLM, structured_output) — claims_operations / general_faq / unknown
          [claims_operations] → extract_claim_policy_ids (Code) — also extracts customer_id, no domain
                                                                     prefix since a customer can span
                                                                     multiple policy types
                              → ID waiting logic (claim / policy / customer)
                              → intent_identifier (LLM, structured_output) — claim_details / policy_details /
                                  claim_and_policy_details / assess_claim / claims_history / customer_history
                              → compute_requires_ids → ID availability gates (incl. customer-only bucket)
                              → prepare_intents_for_iteration → va_clear_awaiting_flags
                              → if_needs_domain_lookup
                                  [true: CLM present, domain empty] → domain_lookup (HTTP GET /claims/domain)
                                                                     → parse_domain_response (Code)
                                                                     → va_set_domain_from_lookup
                                  [false] → (pass through)
                              → Iteration
                                  → map_intent → IF/ELSE 13 (5 cases, evaluated top-to-bottom, first match wins)
                                      [customer_history: intent_name is "customer_history"] → customer_history_agent → format_response
                                      [life]        → life_agent        → format_response
                                      [health]      → health_agent      → format_response
                                      [CI]          → ci_agent          → format_response
                                      [disability]  → disability_agent  → format_response
                                      [no domain]   → unknown_answer_iter → format_response
                              → unpack_iteration_results → va_save_last_result_context
                              → multi_aggregator_llm → generate_followups → validate_followups
                              → global_cleanup → compose_final_answer → multi_answer → va_set_claims_final
          [general_faq]       → faq_answer_llm → faq_answer → va_set_faq_type
          [unknown]           → unknown_answer
```

**Conversation variables (17):** `claim_id`, `policy_id`, `customer_id`, `intended_domain`,
`awaiting_claim_id`, `awaiting_policy_id`, `awaiting_customer_id`, `pending_intent_list`,
`pending_primary_intent`, `last_intent_list`, `last_primary_intent`, `last_combined_sections`,
`last_answer_type`, `last_faq_answer`, `effective_query`, `pending_query`, `pending_intents_json`

**`last_answer_type` values:** `claims` (for claims path) and `faq` (for FAQ path). `IF/ELSE 3` uses `contains` matching so these are compatible with longer values like `claims_operations`.

**CLM-only domain routing (resolved):** When only a Claim ID is given with no Policy ID, `intended_domain` would be empty and `IF/ELSE 13` would fall through to `unknown_answer_iter`. Fixed via 4-node domain lookup step (`if_needs_domain_lookup` → `domain_lookup` → `parse_domain_response` → `va_set_domain_from_lookup`) calling `GET /claims/domain` on the MCP server, inserted between `va_clear_awaiting_flags` and `Iteration`.

**Prompt calibration notes:**
- `followup_router`: memory enabled (window 3-5); expanded `is_followup=true` patterns to cover "explain/elaborate/clarify/further"; `needs_ids=false` when followup; boolean output type enforced explicitly in output contract; later extended with Customer-ID-aware override rules (a stored Policy ID/Domain from a prior turn must not be treated as reason to call a fresh Customer-ID message a followup)
- `query_type_router`: HOW/WHAT/WHY questions → `general_faq`; hard gate against returning `unknown` for insurance queries; never-unknown rule added
- `intent_identifier`: removed "Requires a Claim ID" from all original 4 intent definitions; classify by intent not by ID availability; no-ID examples added; examples disclaimer added; **CRITICAL DISAMBIGUATION section added 2026-07-13** — classify using only the current message's own content, never let a stale Policy ID/Domain/Customer ID from prior conversation turns pull the classification toward the wrong intent; explicit rule that a Customer ID mention always wins toward `customer_history` over stale policy/domain context; explicit scoping rules distinguishing `claims_history` (one named policy) from `customer_history` (a customer's overall relationship, possibly multi-domain)

**Remaining minor issue:** When `unknown_answer_iter` path runs (no domain match), `compose_final_answer` may prepend `unknown_answer##` to output — cosmetic formatting issue, does not affect routing or data correctness.

### Deterministic Routing-Bug Fixes (2026-07-13) — `claims_history`/`customer_history` rollout

Adding the two new intents surfaced a recurring class of bug: **the LLM's own classification/judgment
was unreliable for what is actually a deterministic routing decision**, at GPT-5.2's default temperature.
Consistent with this project's existing hallucination-control philosophy (structured outputs, enum
constraints), each instance was fixed by moving the decision into deterministic code rather than
rewording the prompt further:

1. **`is_followup` unreliability** — a message containing a fresh Customer ID was sometimes still
   classified `is_followup=true`, reusing stale conversation context instead of re-extracting/
   re-classifying. Fixed with `detect_fresh_id_in_query` (a Code node, pure regex, no LLM) feeding a new
   first-priority case on `if/else_followup` that deterministically overrides the LLM's own judgment
   whenever the current message contains a CLM-/POL-/CUST- pattern.
2. **`IF/ELSE 13` case-ordering bug** — Dify if-else nodes evaluate cases top-to-bottom, first match
   wins. The new `customer_history` case was initially added *last*, after the four domain cases (which
   match on `conversation.intended_domain`, a value that persists across turns). A stale
   `intended_domain` from an earlier turn (e.g. "health") therefore matched before the correctly-
   classified `customer_history` intent was ever checked, misrouting to a domain agent instead of
   `customer_history_agent`. Fixed by moving the `customer_history` case to first position (case IDs,
   not list order, are what edges reference — safe to reorder without touching any edge).
3. **Backend false-404 on legitimate empty results** — `GET /claims`/`GET /policies` in
   `mcp_server/main.py` originally 404'd on *any* empty result set, including valid list-style filters
   (e.g. `customer_id` for a real customer with zero claims). This made `customer_history` falsely report
   "not found" for a customer who simply has no claims yet. Fixed (see §10) to only 404 when a specific
   `claim_id`/`policy_id` is queried directly and returns nothing — a genuine "doesn't exist" case — and
   return `[]`/200 for every other empty-result filter combination, matching the convention already used
   by `/claim-documents`.

**Operational lesson worth keeping (not a code fix, a debugging-process one):** after these fixes were
confirmed correct on the Dify canvas, a `customer_history` query still failed via the live Vercel chat
while working fine inside Dify's own builder UI. This was **not** a regression — Dify's external chat
API always serves the app's last **published** version, while Dify's own Run/Preview panel runs the
current **draft** canvas regardless of publish state. The actual cause was simply that the orchestrator
hadn't been re-published after the edits. **Whenever "works in Dify's UI but not through the live
product" is reported again, check Publish status first**, before suspecting env vars, API keys, or
routing logic.

---

## 10. Component 2 — MCP Server (FastAPI v2.1.0)

All endpoints use **query parameters** (not path parameters).

**Local start:**
```bash
cd mcp_server && uvicorn main:app --reload --port 8000
```

**Cloud:** https://sit-capstone.onrender.com

### All 28 Endpoints (corrected 2026-07-16 — added `/explanations` and `/missing-documentation-checks`)

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Server status + version |
| `/claims` | GET | Filtered claims |
| `/claims/domain` | GET | Domain + linked policy ID for a Claim ID (orchestrator routing) |
| `/policies` | GET | Filtered policies (includes policy_text) |
| `/eligibility-rules` | GET | Rules filtered by policy_type |
| `/assessment` | GET | Claim + linked policy + rules combined |
| `/claim-documents` | GET | Documents for a claim — returns `[]` (not 404) if none exist |
| `/fraud-risk-checks` | GET | Query logged fraud/anomaly risk-signal results |
| `/fraud-risk-checks` | POST | Write a fraud/anomaly risk-signal result |
| `/explanations` | GET | Query assessment explanations, filterable by `log_id`/`claim_id` — added 2026-07-14 |
| `/explanations` | POST | Write an assessment explanation, keyed by `log_id` — added 2026-07-14 |
| `/missing-documentation-checks` | GET | Query missing-documentation checks by `claim_id` — added 2026-07-14 |
| `/missing-documentation-checks` | POST | Write a missing-documentation check — added 2026-07-14 |
| `/assessment-logs` | POST | Write assessment result to audit log — `rule_checks` field added 2026-07-15 (`Union[str, List[dict]]`, since Dify sends it as a native array). **2026-07-16:** also finalizes `claims.status` for a claim that was `pending` (write-back), or computes `status_cross_check` for a claim that already had a decided status (observe-only, see §7) — mutually exclusive per request. `?skip_status_update=true` opts a caller out of the write-back only (never the cross-check, which is harmless) — used by `evaluation/run_evaluation.py`'s "combined" strategy, which snapshots/restores `claims.status` around the call instead of relying on any Dify-side flag (deliberately kept out of the Dify workflows themselves — see §9). Also overrides a known-stale `prompt_version` (`PROMPT_VERSION_BUMPS`, see §7) and schedules a real MLflow run via `BackgroundTasks` — **not synchronous**: a live Databricks round-trip (`mlflow.start_run` + several `log_param`/`log_metric` calls) measured at 13+ seconds even with a warm tracker, so `mlflow_run_id` is absent on the immediate response and only appears on a subsequent `GET` once the background task finishes. Requires `mlflow`/`databricks-sdk` (added to `requirements.txt` 2026-07-16) to actually install on Render's next deploy |
| `/assessment-logs` | GET | Query audit log (management dashboard); `log_id` filter added 2026-07-14 for Explain's row-specificity fix |
| `/workflow-nodes` | GET | Stored DSL nodes for a workflow |
| `/workflow-nodes` | POST | Store node after approval |
| `/change-approvals` | GET | Pending/approved changes |
| `/change-approvals` | POST | Create change approval request |
| `/change-approvals/{id}/approve` | POST | Approve + trigger git commit |
| `/change-approvals/{id}/reject` | POST | Reject change |
| `/dsl/status` | GET | DSL scan status (reads the `dify-workflows` Supabase Storage bucket, not disk) |
| `/dsl/scan` | POST | Server-side DSL scan trigger (frontend DSL Management view) |
| `/dsl/upload` | POST | Upload a workflow YAML directly into the `dify-workflows` Storage bucket (multipart) |
| `/dsl/snapshot-files` | GET | List workflow files eligible for a whole-file snapshot |
| `/dsl/snapshots` | GET | Whole-file snapshot commit history for one workflow, read live from GitHub |
| `/dsl/snapshots` | POST | Commit current Storage content of one/all workflows to the governance branch |
| `/dsl/snapshots/node-diff` | GET | Node-level diff: latest snapshot vs. current — only nodes that differ |

**404-on-empty convention fixed (2026-07-13):** `/claims` and `/policies` originally raised a 404 on
*any* empty result, including valid list-style filters (e.g. `customer_id`, `policy_id`-only,
`claim_type`) where zero results is a legitimate answer, not an error — this caused `customer_history` to
falsely report "not found" for a real customer with zero claims. Both endpoints now only 404 when a
specific `claim_id`/`policy_id` is queried directly and returns nothing (a genuine "doesn't exist" case);
every other empty-result filter combination returns `[]`/200, matching the convention `/claim-documents`
already used. Committed in `f81a4ea`, pushed to `origin/main`, and confirmed live against
`https://sit-capstone.onrender.com`.

### Environment Variables (mcp_server/.env)
```
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_KEY=[service_role_secret_key]
DATABRICKS_HOST=https://dbc-0dc2996b-ae12.cloud.databricks.com
DATABRICKS_TOKEN=[365-day personal access token]
GITHUB_TOKEN=[personal access token for git commits — also gates whole-file snapshot commits]
GITHUB_REPO=jas12481/sit_capstone
GITHUB_GOVERNANCE_BRANCH=dsl-governance-history   # optional, defaults to this name
```
**Not yet mirrored to Render** (deploy gap, see §14 and §20): `GITHUB_TOKEN`/`GITHUB_REPO` only exist
in the local `.env` as of 2026-07-14. Also requires `python-multipart` (added to `requirements.txt`
2026-07-14 for `/dsl/upload`'s multipart file handling) to actually install on Render's next deploy.

---

## 11. Component 3 — Database Layer (Supabase)

- **Region:** Singapore (ap-southeast-1)
- **RLS:** Enabled on all 10 tables
- **Access:** MCP server only (secret key bypasses RLS)
- **Tables:** policies, claims, claim_documents, eligibility_rules, assessment_logs, workflow_nodes,
  change_approvals, plus three added 2026-07-14 for the product-capability apps (§7): fraud_risk_checks,
  assessment_explanations, missing_documentation_checks
- **Storage buckets:** `policy-documents` (public, 1,000 policy PDFs) and **`dify-workflows`** (private,
  added 2026-07-14 — the sole "current version" source of truth for all 25 Dify workflow YAMLs; see §14.
  Private because only the MCP server's service-role key ever touches it, same bypass-RLS mechanism used
  for the database tables — no bucket policies needed)

---

## 12. Component 4 — MLflow + Databricks

### Three Functions

1. **Prompt Registry** — version control for all system prompts
2. **Experiment Tracking** — logs every evaluation run (parameters + metrics + artifacts)
3. **Production Audit Link** — every assessment_logs entry links to an MLflow run via `mlflow_run_id`

### Connection Details
- Databricks host: `https://dbc-0dc2996b-ae12.cloud.databricks.com`
- Username: `jasclapforyou@gmail.com`
- Experiment: `/Users/jasclapforyou@gmail.com/Claims_Assessment_Prompting_Study`
- Experiment ID: `2726789194105433`
- Token: 365-day personal access token stored in `mcp_server/.env`
- Setup script: `setup_mlflow.py` in repo root

### Prompt Registry Naming Convention
```
workspace.default.{workflow_name}_{node_name}_v1_0
```
Actual registered examples (from `evaluation/register_prompts.py`, run 2026-07-06 — 79 prompts,
covering all 16 production workflows plus the 6 new apps):
```
workspace.default.life_assess_claim_rule_by_rule_eligibility_check_v1_0
workspace.default.life_assess_claim_policy_document_analysis_v1_0
workspace.default.life_assess_claim_synthesize_final_verdict_v1_0
workspace.default.life_assess_claim_llm_judge_v1_0
workspace.default.health_assess_claim_rule_by_rule_eligibility_check_v1_0
... (same pattern per policy type: rule_by_rule_eligibility_check / policy_document_analysis /
    synthesize_final_verdict / llm_judge / extract_response_focus_assess / format_final_report /
    build_assessment_suggestion_context, plus the equivalent nodes in each *_Claim_Details /
    *_Policy_Details / *_Claim_and_Policy_Details workflow, plus Test_Orchestrator-1's 8 nodes,
    plus the 6 new apps' nodes e.g. workspace.default.cot_research_cot_recommendation_v1_0)
```
This corrects two things discovered during implementation, not just cosmetic:
1. **The registry is Unity Catalog-backed**, which requires fully-qualified 3-level names
   (`catalog.schema.name`) — a bare name is rejected by the API with a misleading
   `INVALID_PARAMETER_VALUE: name is not a valid name` error that reads like a character-set
   complaint but is actually about the missing catalog/schema prefix. `workspace.default` is the
   catalog/schema used (confirmed working against the live registry).
2. **Periods are rejected within a name segment** (`"...cannot contain spaces, periods, forward
   slashes, or control characters"`), so the version suffix is `_v1_0`, not `_v1.0` as originally
   drafted — the underscore form is a technical requirement, not a style choice.
3. The node names use the *actual* Dify node titles as they exist in the YAML (e.g.
   `rule_by_rule_eligibility_check`), not the shorter illustrative names originally sketched here
   (e.g. `rule_check`) — `register_prompts.py` is fully mechanical/generic (walks every `llm`-type
   node via `dsl_manager.parser.parse_workflow()`, no per-node hand-mapping table to maintain), which
   was the explicit design goal so it keeps working automatically as new workflows/nodes are added.

When prompts are updated via DSL Change Management, increment version. Log `prompt_version` to `assessment_logs`.

### Prompt Registry UI — Databricks Free Edition gap, and the local mirror workaround

The registry itself is fully real and queryable (confirmed via `evaluation/list_prompt_registry.py` — all
79 prompts, full version history) but **this Databricks Free Edition workspace has no browsable UI for
it**. Investigated directly rather than assumed:
- Checked Catalog Explorer's Models tab and the `Claims_Assessment_Prompting_Study` experiment's own tab
  list (Runs / Models / Traces) — no Prompts tab in either.
- Per Databricks' own docs, the Prompts tab requires (a) the experiment tagged with
  `mlflow.promptRegistryLocation` = `catalog.schema` — confirmed via API this tag did not exist, then set
  it to `workspace.default` directly via `MlflowClient().set_experiment_tag(...)`; and (b) the schema-level
  `EXECUTE` and `MANAGE` Unity Catalog privileges — confirmed via
  `GET /api/2.1/unity-catalog/permissions/schema/workspace.default` that the account only has
  `CREATE_FUNCTION, CREATE_MATERIALIZED_VIEW, CREATE_MODEL, CREATE_TABLE, CREATE_VOLUME, USE_SCHEMA` —
  **`EXECUTE` and `MANAGE` are both missing**. Also confirmed via `GET /api/2.1/unity-catalog/catalogs`
  that no `main` catalog exists in this workspace (only `workspace`, `samples`, `system`), so the "trial
  accounts get `main.default`" note in Databricks' docs doesn't apply here regardless.
- Couldn't find an official source stating plainly "Free Edition has no Prompt Registry UI" one way or
  the other — the official Free Edition limitations page doesn't mention MLflow/GenAI features at all.
  Left as an accepted, unresolved ambiguity (missing privileges vs. a Beta-feature gate vs. a hard Free
  Edition limit) rather than chased further — a deliberate scope decision, not an oversight.

**Workaround (self-hosted local mirror, not a fix to the above):**
- `evaluation/sync_prompt_registry_local.py` — reads every prompt + full version history from Databricks,
  then replays it into a separate, self-hosted MLflow server (`mlflow server --backend-store-uri
  sqlite:///...`), which *does* render a normal Prompts UI since it's not Unity-Catalog-backed. Re-run
  after any real prompt change on Databricks to refresh the mirror (note: re-running without a real
  change creates duplicate-but-identical version numbers locally — harmless for browsing, just not a
  strict 1:1 version-count mirror).
- `evaluation/start_local_prompt_registry.sh` — starts the local server at `http://127.0.0.1:5001`,
  backed by `mlflow_local_registry/mlflow.db` (gitignored — generated data, not source).
- Databricks stays the actual source of truth for governance (`assessment_logs.mlflow_run_id` links only
  to Databricks runs); the local server is a browsing convenience only, evaluated and explicitly scoped
  down from an earlier, abandoned plan to permanently deploy this to Render with a Postgres backend and
  HTTP Basic Auth (built and locally verified working, then deliberately discarded in favor of the
  simpler localhost-only approach once the Free Edition ambiguity above was found not worth resolving
  via extra infrastructure).

### Evaluation Experiment — Parameters and Metrics

**Parameters per run:**
```
strategy        direct | chain_of_thought | structured_output | combined
policy_type     life | health | critical_illness | disability
claim_id        test claim identifier
model_name      gpt-5.2
prompt_version  from MLflow Prompt Registry
```

**Metrics per run:**
```
recommendation_correct              1/0 vs ground truth
hallucinated_rule_count             rule IDs not in eligibility_rules table
hallucinated_clause_count           clause refs not found in policy_text
mandatory_rules_correctly_identified 1/0 correct mandatory rules flagged
valid_clause_references             count of clause refs that exist in policy_text
confidence_level_numeric            HIGH=1.0 MEDIUM=0.5 LOW=0.0
judge_completeness                  LLM-as-Judge score 0-1
judge_consistency                   LLM-as-Judge score 0-1
judge_hallucination_risk            LLM-as-Judge score 0-1
judge_clarity                       LLM-as-Judge score 0-1
judge_overall                       average of four judge scores
```

**Artifacts per run:**
- Full assessment report (text)
- Raw structured output JSON
- LLM-as-Judge evaluation JSON

---

## 13. Component 5 — LLM-as-Judge Quality Evaluation Layer

### What It Is

After every assessment, an additional LLM node reads the full report and scores it on four dimensions. Scores logged to both `assessment_logs` and MLflow. Runs in production AND during the evaluation study.

### Four Dimensions

| Dimension | What It Checks | Score |
|---|---|---|
| **Completeness** | All rules checked, checklist present, payable amount calculated, next action clear | 1.0-5.0 |
| **Consistency** | Recommendation aligns with rule verdicts, confidence matches failure count | 1.0-5.0 |
| **Hallucination Risk** | Rule IDs valid, clause numbers plausible, all figures traceable to input | 1.0-5.0 (5 = no hallucination) |
| **Clarity** | Professional language, usable as case note, recommendation unambiguous | 1.0-5.0 |

**Correction (confirmed 2026-07-06 from the actual deployed `llm_judge` node prompt during evaluation-harness
build):** the real scale is **1.0–5.0**, not 0-1 as originally drafted here — `evaluation/metrics.py` and
`evaluation/prompt_advisor.py` (`JUDGE_SCORE_FIELDS`) both match the actual deployed behavior. Across
`prompt_advisor.py`'s first real run (all 4 `*_Assess_Claim` workflows, 20-run window each),
`hallucination_risk` came back weakest for every workflow (3.95-4.12/5.0), which is what drove its 8
real submitted `change_approvals` suggestions — see §15.

### Dify Implementation (redesigned 2026-07-15/16 — see "Grounding Redesign" below for why)

**Node name:** `llm_judge` | **Model:** GPT-5.2 | **Structured Output:** ON

**JSON Schema (current, actual):**
```json
{
  "type": "object",
  "properties": {
    "judge_completeness_score": {"type": "number"},
    "judge_consistency_score": {"type": "number"},
    "judge_hallucination_risk_score": {"type": "number"},
    "judge_clarity_score": {"type": "number"},
    "judge_comments": {"type": "string"}
  },
  "required": ["judge_completeness_score", "judge_consistency_score",
               "judge_hallucination_risk_score", "judge_clarity_score", "judge_comments"]
}
```
Note: `judge_overall_score` is deliberately **not** part of this schema — see below.

**System Prompt (current):** *"You are an internal quality judge for assessment reports. You are given
the actual claim record and policy record for this claim, alongside the AI-generated final report and
verdict. Score the final report on four dimensions, each 1.0-5.0, using these anchors: completeness
(5 = all required elements present and clearly explained ... 1 = major required elements missing);
consistency (5 = fully consistent ... 1 = narrative and verdict actively contradict each other);
hallucination risk, higher = lower risk / safer — cross-check every factual statement in the report
against the claim record and policy record provided below; a statement not directly supported by those
records is a hallucination (5 = every factual claim is directly traceable ... 1 = the report states
specific facts that contradict or are absent from the claim/policy record); clarity (5 = clear,
well-organized ... 1 = confusing or ambiguous). ... Do not compute or return an overall score - that is
computed separately from your four dimension scores."*

**User Prompt (current):** claim record + policy record (full JSON, same `claim_record_json`/
`policy_record_json` variables `rule_by_rule_eligibility_check` already uses) + the generated final
report + verdict payload.

**`compute_judge_overall` (new code node, deterministic):**
```python
def _to_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default

def main(judge=None):
    judge = judge or {}
    scores = [
        _to_float(judge.get("judge_completeness_score")),
        _to_float(judge.get("judge_consistency_score")),
        _to_float(judge.get("judge_hallucination_risk_score")),
        _to_float(judge.get("judge_clarity_score")),
    ]
    overall = sum(scores) / len(scores) if scores else 0.0
    return {"judge_overall_score": round(overall, 2)}
```
Sits between `llm_judge` and `prepare_assessment_log_payload` in the graph; the latter now takes
`judge_overall_score` as its own parameter (sourced from this node) instead of reading
`judge.get("judge_overall_score")`.

### Grounding Redesign (2026-07-15/16) — the previous design was measuring the wrong thing

Jasbir flagged the Dashboard's "Avg Judge Score"/"Avg Hallucination Risk" cards as "feeling fake" and
asked how they were actually measured. Pulling the real deployed `llm_judge` prompt (as it existed
before this fix) surfaced three concrete logic gaps, not just a vague quality concern:

1. **No grounding.** The judge only ever received the `format_final_report` narrative (LLM-written
   prose: `executive_summary`, `rule_summary`, `risk_flags`, `audit_notes`) and the verdict — both
   already LLM output. It never saw `claim_record`, `policy_record`, or `rule_checks`. So
   "hallucination risk" could not mean "did the report state something false about this claim" — there
   was nothing real to check against. It was actually measuring internal narrative self-consistency, a
   much weaker thing wearing a stronger label.
2. **No rubric anchors.** "Score 1.0-5.0" with zero definition of what a 2 vs. a 4 means — the same
   report could plausibly score differently across runs for no principled reason.
3. **`judge_overall_score` was a free 5th number the LLM invented**, not a computed aggregate of the
   other four — no guaranteed relationship to completeness/consistency/hallucination/clarity at all.

**Fix:** grounded the judge in the real `claim_record`/`policy_record` (Jasbir's choice over the
lighter-weight `rule_checks`/`evidence_fields`-only option, for stronger fact-checking beyond just
rule-linked evidence), added explicit rubric anchors per dimension, and moved `judge_overall_score` to
a deterministic code node (simple average — Jasbir's choice over a hallucination-weighted formula, for
transparency/simplicity in the capstone writeup) — the same deterministic-over-LLM-judgment pattern
used elsewhere in this project (§15).

**Verified live post-redesign (2026-07-16):** one fresh assessment per domain, all 4 succeeded end to
end; in every case `judge_overall_score` matched the exact average of the 4 sub-scores, and
`rule_checks` persisted correctly alongside it. Hallucination-risk scores on these first grounded runs
came back notably lower/riskier (2/5 on 3 of 4) than the historical ~4/5 norm — evidence the redesigned
judge is now actually catching unsupported statements it structurally could not have detected before,
not a regression.

**A mistake made and caught while building this:** the redesign was first applied on top of the local
`dify-data/*.yml` copies, which (per the `dify-data/` staleness note in §14) predated the `rule_checks`
persistence fix — silently regressing it. Caught by Jasbir asking "is this reading from the dify-data
folder??" about the Workflow Snapshots diff view, which surfaced the mismatch. Fixed by rebuilding the
redesign on top of the correct baseline (the latest `dsl-governance-history` GitHub snapshot for each
file, confirmed to have `rule_checks` intact) instead, with a surgical patch (one added parameter, one
changed line) to `prepare_assessment_log_payload` rather than a wholesale rewrite, specifically to avoid
clobbering domain-specific defaults or extraction logic a second time. `dify-data/` was reverted to its
committed state and is not to be edited again — Storage/GitHub snapshots are the only valid editing
baseline going forward.

---

## 14. Component 6 — DSL Change Management System

### What It Is

A governed version control system for Dify workflow configurations. Parses exported DSL YAMLs, detects changes to LLM/code/agent nodes, requires named sign-off before committing to the database and GitHub. The most original component of the project.

### The Full Flow

```
1. Export DSL from Dify → dify-data/ folder
2. python dsl_manager/parser.py --file dify-data/Life_Assess_Claim.yml
3. Parser extracts LLM nodes (prompt text) + code nodes (code content)
4. SHA256 hash each node's content
5. Compare against stored hash in workflow_nodes table
6. If changed → generate diff → create change_approvals entry (status=pending)
7. Frontend DSL Management view shows diff + approval form
8. Approver's identity is verified via Okta SSO (see Component 8) — the name field is no longer free
   text; only the justification/reason is manually entered → Approve or Reject
9. If Approved:
   - Update workflow_nodes with new content + hash
   - Increment prompt_version in MLflow Prompt Registry
   - Commit to GitHub: "[APPROVED] {workflow} — {node}: {reason} | By: {approver}" — **currently only
     happens via the `dsl_manager` CLI's `approve` command; the frontend's approve action (server-side
     `/change-approvals/{id}/approve`) does not yet commit to GitHub.** Deliberately deferred until a
     dedicated branch exists for DSL governance commits.
   - Store git_commit_hash in change_approvals (CLI path only, for now)
   - Future assessment_logs reference new prompt_version
10. If Rejected: log rejection, no changes committed
```

### Modules

- `dsl_manager/parser.py` — reads YAML, extracts nodes, computes SHA256 hashes. `parse_workflow(path)`
  is now a thin wrapper around `parse_workflow_content(yaml_text, workflow_name_fallback)` (added
  2026-07-14) — the actual extraction logic lives in the latter so it can parse YAML already in memory
  (downloaded from Supabase Storage or fetched from GitHub) as well as a local file. This is the single
  source of truth for node extraction — `mcp_server/main.py`'s `/dsl/scan` and the new node-diff
  endpoint both import these same functions rather than re-implementing them.
- `dsl_manager/diff.py` — human-readable before/after diff (`compute_diff`), reused for both node-level
  approval diffs and the new whole-file-snapshot node-diff comparison
- `dsl_manager/approvals.py` — create_approval, approve_change, reject_change
- `dsl_manager/git_commit.py` — GitHub API commits with attribution metadata. Two independent
  mechanisms live here now (see below): per-node approved-snippet commits to `main`
  (`commit_approved_change`), and whole-file snapshots to a dedicated branch (`commit_workflow_snapshot`,
  `list_workflow_snapshots`, `get_file_content_at_ref`, `ensure_governance_branch`).

### Audit Trail Chain

```
Assessment decision → prompt_version → change_approvals record → git_commit_hash → exact prompt text
```

An auditor can trace any assessment back to who approved the prompt that produced it.

### Whole-File Version History (added 2026-07-13/14) — Supabase Storage + Dedicated GitHub Branch

A second, independent governance mechanism alongside the node-level approval flow above. Where the
approval flow tracks and signs off individual *extracted node* changes, this tracks the **whole workflow
file** as a real, diffable version history — built because Jasbir wanted a place where every version of
every workflow is committed for visibility/auditability, decoupled from `main` so governance commits
never mix with regular app-code commits, and because GitHub's own compare view gives "version
comparison... for free" once the history exists.

**Storage migration — disk is no longer the source of truth.** `dify-data/*.yml` on local disk is now a
**frozen historical artifact only** — kept permanently in the repo for the report's before/after
narrative, but never read by the running system. The **`dify-workflows` Supabase Storage bucket** (see
§11) is the sole "current version" source for all 25 workflows. `/dsl/scan`, `/dsl/status`,
`/dsl/snapshot-files`, `/dsl/snapshots` (POST), and `/dsl/snapshots/node-diff` all read from/write to
Storage exclusively. `migrate_workflows_to_storage.py` (repo root) was the one-time script that seeded
the bucket from disk on 2026-07-13 — safe to re-run (upsert), not part of any ongoing flow.

**Whole-file snapshots — `dsl-governance-history` branch.** `commit_workflow_snapshot(repo_path,
content, committed_by, reason)` commits raw file bytes (from Storage, downloaded by the caller — the
function itself has no opinion on the content's source) to a dedicated branch, auto-created off `main`
on first use via `ensure_governance_branch()`. Every commit is a full point-in-time version of that
workflow at the same `dify-data/{name}.yml` path used before the Storage migration (kept for continuity
with history already on the branch). Triggered via `POST /dsl/snapshots` (one file or all) from the
frontend's **Workflow Snapshots** tab, or `python -m dsl_manager snapshot --file <path>|--all --by
<name> --reason "<text>"` from the CLI.

**Known GitHub API gotcha, already fixed:** GitHub's commits API `?path=` filter excludes any commit
where the file's git tree didn't actually change — guaranteed true for a workflow's very first snapshot
(freshly forked off `main`, then immediately re-committed with identical content). That baseline commit
is 100% real (reachable, has a valid SHA) but invisible to path-filtered history. Fixed by having
`list_workflow_snapshots()` match on the commit message's `[SNAPSHOT] {filename}:` prefix instead of
relying on git's tree-diff — finds every snapshot regardless of whether content actually changed.

**Node-level comparison — `GET /dsl/snapshots/node-diff`.** Jasbir explicitly wanted "just the nodes
that are different, not the entire files" when comparing the latest snapshot against the current
version — not a raw whole-file text diff. Fetches the latest snapshot's content via
`get_file_content_at_ref()` (new — reads a file at a specific commit SHA, not just commit metadata) and
the current content from Storage, parses both with `parse_workflow_content()`, and returns only nodes
whose content hash actually differs (`added`/`changed`/`removed`), each with a proper diff via the
existing `compute_diff()`. Rendered in the frontend under "Changes Since Last Snapshot," reusing the
existing per-type `NodeContentViewer`/`DiffViewer` components — no new diff-rendering logic.

**Upload page — `POST /dsl/upload`.** Lets Jasbir add/update a workflow YAML directly through the
frontend, landing in the Storage bucket immediately — no manual file placement or backend/server access
needed for day-to-day workflow updates. Validates the upload is real, parseable Dify DSL (via
`parse_workflow_content`) before accepting; rejects non-`.yml`/`.yaml` files and unparseable YAML with a
clear error. Requires `python-multipart` (added to `requirements.txt` 2026-07-14).

**Deliberately still CLI-only, not extended to this mechanism:** the server-side
`/change-approvals/{id}/approve` endpoint still does not commit to GitHub (per the original deferral,
§ above) — that gap is about the *node-level approval* flow specifically, unaffected by any of the
whole-file snapshot work above, which is its own separate, already-fully-wired mechanism (both CLI and
frontend can trigger a snapshot commit).

**Gotcha, learned the hard way (2026-07-16): never edit `dify-data/*.yml` and treat it as current.**
It's a frozen historical artifact that stopped being updated once the Storage migration landed — later
fixes (e.g. the `rule_checks` persistence fix, 2026-07-15) were applied to a different set of files
(repo-root export copies) and uploaded straight to Storage, never synced back into `dify-data/`. Editing
`dify-data/` directly and assuming it reflects reality will silently regress whatever changes it missed.
**The only valid editing baseline is either the current Storage bucket content, or the latest commit on
the `dsl-governance-history` branch for that file** (`git_commit.get_file_content_at_ref`) — both are
verifiable via `/dsl/snapshots/node-diff` before trusting them as a starting point. This is exactly what
happened building the LLM-as-Judge grounding redesign (§13) — caught before it reached Dify, but only
because the resulting Storage diff looked suspicious enough to double-check.

**Frontend polish (2026-07-16):** the Workflow Snapshots tab no longer displays the `dify-data/` prefix
anywhere (dropdown, headers, snapshot-result list) — Jasbir flagged it as misleading given the actual
source is the `dify-workflows` Storage bucket. A `displayName()` helper in `dsl/page.tsx` strips the
prefix for display only; the API calls underneath still send `dify-data/{name}` (the real GitHub commit
path, kept for continuity with existing snapshot history — an internal detail, not user-facing).

---

## 15. Component 7 — Prompt Optimisation Agent

### What It Is

A Python script (`evaluation/prompt_advisor.py`) that monitors MLflow quality metrics and proposes targeted prompt improvements. It works entirely within the governance framework — suggestions go through the DSL Change Management System for human sign-off. The agent suggests, the human decides.

### Why It Matters

Closes the continuous improvement loop. Without it, prompt improvements rely on the developer manually reviewing MLflow results. With it, the system surfaces specific, data-driven improvement suggestions automatically — directly implementing MAS AIRG "capabilities and capacity — continuous improvement" and IMDA "Operations Management — monitoring and review."

### The Full Flow (as actually implemented, run for real 2026-07-07)

```
python evaluation/prompt_advisor.py --workflow life_assess_claim   # or --workflow all
  ↓
GET /assessment-logs?workflow_type=X&limit=20 (the real production audit trail, not MLflow runs
directly — MLflow research-study runs don't carry judge scores the same way)
  ↓
Average the 4 judge score fields across those logs; pick the lowest-scoring dimension
  ↓
Map that dimension → responsible node(s) via a fixed table:
  hallucination_risk → rule_by_rule_eligibility_check, policy_document_analysis
  clarity            → format_final_report
  completeness / consistency → synthesize_final_verdict
  ↓
Look up each node's current prompt: MlflowClient().search_prompt_versions(name) → latest version →
mlflow.genai.load_prompt(name, version=latest)
  ↓
Append a deterministic, heuristic guardrail clause for that dimension (no live LLM call drafts
this — see Key Design Decision below)
  ↓
POST to MCP /change-approvals:
  changed_by = "prompt_advisor_agent"
  diff_content = dsl_manager.diff.compute_diff(old, new, node_name, "llm")  (reused, not reimplemented)
  workflow_name, node_name, new_content, new_hash
  ↓
Human sees suggestion in DSL Management UI (frontend/app/dsl/page.tsx — no frontend changes needed)
  ↓
Reviews diff → Approves or Rejects
  ↓
If Approved → standard DSL change management flow
```

**Real result of running this against all 4 production workflows**: every single one came back with
`hallucination_risk` as the weakest dimension (3.95-4.12/5.0 average) — 8 real pending `change_approvals`
rows created (2 nodes × 4 workflows), each with the guardrail: *"cite only rule IDs, clause references,
and document types that literally appear in the provided input data — never invent, infer, or assume an
identifier that isn't explicitly present."*

### Key Design Decision

The agent deliberately does not auto-apply changes. Under IMDA and MAS AIRG, AI systems in high-stakes domains must maintain human oversight. A prompt change in an eligibility assessment system is equivalent to a rule change in underwriting — it must be reviewed by a named person.

**Second, discovered-during-build design decision**: the improvement itself is a **deterministic heuristic
template per dimension** (`DIMENSION_AUGMENTATIONS` in the script), not an LLM-drafted rewrite as
originally sketched here. Reason: no OpenAI API key exists anywhere in this repo's env files, and none of
the 6 new Dify apps built this session are suited to free-form prompt-authoring (they're all hardcoded for
claim assessment or research-recommendation tasks, not general text generation). This still fully
satisfies the governance requirement — the suggestion still lands as a PENDING row requiring human
sign-off — it's just template-based rather than model-generated.

### Key Functions (actual, `evaluation/prompt_advisor.py`)

```python
find_weakest_dimension(workflow_type, limit=20)  # averages 4 judge fields from GET /assessment-logs
find_node_id(workflow_name, node_name)           # looks up the stored node's real UUID via GET /workflow-nodes
draft_improved_prompt(workflow_type, node_name, dimension, dry_run) # loads current prompt, appends
                                                                     # DIMENSION_AUGMENTATIONS text,
                                                                     # posts to /change-approvals
run_for_workflow(workflow_type, dry_run)         # orchestrates the above per workflow
```

### Regulatory Mapping

| Framework | Requirement | Implementation |
|---|---|---|
| IMDA Pillar 3 | Operations Management — monitoring | Agent monitors quality metrics continuously |
| IMDA Pillar 3 | Human oversight maintained | Agent suggests only, human approves |
| MAS AIRG | Capabilities and capacity | System demonstrates self-assessment and governed improvement |

---

## 16. Component 8 — Frontend (React + Vercel)

### Four Views

**1. Chat Interface** — natural language query input, message history, routing visibility panel (which workflow ran), loading state for long assessments

**2. Audit Log View** *(compliance and audit stakeholders)* — table of assessment_logs, filters (date, workflow type, recommendation, confidence, judge score threshold), expandable rows with full details + judge scores, link to MLflow run. Row expansion is keyed on the real `log_id` PK (fixed 2026-07-14 — the type had a fabricated `.id` field that never existed in real data, so every row's key was `undefined` and clicking one row expanded all of them).

**AI Insights** *(consolidated 2026-07-14, redesigned into a compact menu 2026-07-14/15)* — one column
per row replacing three previously-separate always-visible columns, to reduce clutter as more
product-capability apps were wired in:
- **Assessment Explanation** (`Explain_Assessment_Reasoning`) — on-demand plain-language walkthrough of
  one specific verdict, rendered via `react-markdown`. Keyed by `log_id`, not `claim_id` (a claim can
  have multiple assessment_logs rows; an explanation is tied to one specific run) — required threading
  `log_id` through the Start node, `extract_claim_id` code, HTTP params, and `/assessment-logs?log_id=`
  after discovering the feature always explained a claim's *newest* assessment regardless of which row
  was clicked. Now cites specific rules by name using the persisted `rule_checks` data (§7) instead of
  speaking generically. A hallucination-risk-score misinterpretation was also fixed here — the prompt
  described a high (safe) score as "relatively elevated" (implying danger) when higher actually means
  safer per this project's convention.
- **Missing Documentation** (`Missing_Documentation_Advisor`) — shown for `REFER_FOR_FURTHER_REVIEW`
  rows always, and **REJECT rows since 2026-07-16** where the primary failed mandatory rule's
  `evidence_fields` pointed at `claim_documents` rather than `claim_record`/`policy_record`
  (`isMissingDocsRelevant()` in `audit/page.tsx`) — a deterministic signal that the rejection was
  document-related, not a coverage/eligibility finding the Advisor has nothing useful to say about.
  Client-side only, no backend change needed (`rule_checks` was already being fetched). The
  REFER-specific "documents present but still referred" paradox note stays REFER-only — it doesn't
  apply to a document-related REJECT, which by construction has a missing/failed document rule.
- **Fraud/Anomaly Risk Signals** — click-to-recheck, with timestamp and a success flash on the badge.

The trigger button shows a status dot per capability; clicking opens a dropdown to view/run/recheck any
of the three, then expands the row to the relevant section. Three visual options (dropdown menu / icon
cluster / expand-in-place pill) were mocked up as a Claude Artifact against real CLM-0802 data before
building, so Jasbir could compare before committing to one.

**Status cross-check indicator (new 2026-07-16)** — a small amber warning icon next to the verdict
badge, shown only when `assessment_logs.status_cross_check === 'MISMATCH'` (§7), with the reason as a
tooltip; the expanded row shows the full note, or a quiet "✓ agrees with recorded status" line for
CONSISTENT rows. Deliberately not a 4th AI Insights menu item — it's automatic/observational, not an
on-demand action like the other three, so it doesn't belong in that menu's view/run/recheck pattern.

**3. Management Dashboard** *(business stakeholders)* — recommendation distribution, claims volume by
domain, LLM-as-Judge score trend (last 30 runs), confidence distribution, **Rule Failure Analysis**
(new 2026-07-16 — most frequently failed eligibility rules from persisted `rule_checks`, mandatory rules
in red/non-mandatory in amber, plus a recent-failures feed; captioned with how many assessments have
rule-level data since coverage only grows from the persistence fix's rollout date forward), **Missing
Documentation** (new 2026-07-16 — completeness split, most commonly missing document types, claims
still missing docs), **Status Cross-Check** (new 2026-07-16 — consistent-vs-mismatch split and a list of
claims where fresh AI judgment disagrees with an already-recorded status, deduped to the latest
assessment per claim; only covers already-decided claims, since a freshly-`pending` claim's status gets
finalized by the write-back instead — see §7), **Repeat-Assessment Consistency** (new 2026-07-16 —
groups `assessment_logs` by `claim_id` + `prompt_version`, checks whether repeated runs, each identified
by its own `log_id`, land on the same recommendation; mostly a testing/QA signal since a real claim is
normally only assessed once. Validating this against production data surfaced a real limitation, called
out directly in the panel: `prompt_version` is currently a static per-workflow label that's never bumped
when the underlying prompt actually changes, so some "inconsistent" groups may reflect real development
changes between runs rather than genuine LLM flakiness — e.g. `CLM-0008` shows 13 runs under
`health_assess_claim_v1.0` with 10 APPROVE/3 REJECT, spanning several real prompt edits made this
session that were never reflected in the version label), and Fraud/Anomaly Risk Signals (risk level distribution,
recent flags, high-risk claims needing follow-up — accumulates as claims are checked via the Audit Log,
not a full-portfolio scan).

**KPI cards (fixed 2026-07-16):** "Total Assessments" now shows **distinct claims assessed**, with
total runs as a sub-label — the raw row count was inflated by heavy repeat dev-testing of the same
handful of claims (e.g. one claim assessed 19 times) and read as a misleading headline number for a
management-facing stat. "Avg Judge Score"/"Avg Hallucination Risk" now average over a **trailing window
of the last 50 assessments** instead of all-time — an all-time average over hundreds of historical rows
stays dominated by old data for a long time after any judge/prompt redesign (like §13's grounding fix),
making the cards look unresponsive to real changes; the trailing window matches the "last 30 runs"
convention the trend chart below it already used.

**4. DSL Change Management View** *(IT governance)* — four tabs as of 2026-07-14: **Pending Approvals**
(node-level diffs, approval form with verified identity + mandatory reason), **History** (approved/
rejected past changes), **Stored Nodes** (per-workflow node browser), and **Workflow Snapshots** (new —
upload a workflow YAML directly to the `dify-workflows` Storage bucket; take/browse whole-file version
snapshots on the `dsl-governance-history` GitHub branch; "Changes Since Last Snapshot" node-level diff
against the current version — see §14)

### Authentication (Okta SSO — DSL Change Management view only)

Added 2026-07-02. The DSL Change Management view is gated behind Okta login via NextAuth.js — Chat,
Audit Log, and Dashboard remain open with no login required (a deliberate scope decision: only the
governance/sign-off actions need a verified identity). `middleware.ts` protects the `/dsl` route and
redirects unauthenticated visitors to Okta; on successful login, the approver's verified name/email
from Okta replaces what used to be a free-text "your name" field in both the scan trigger and the
approval sign-off form. The justification/reason field remains free text — only identity is meant to
be verified, not the written reason.

Backing Okta org: a free **Integrator Free Plan** org (`https://integrator-1939264.okta.com`), created
specifically for this project. Okta's own onboarding explicitly flags this plan as "not recommended for
production uses" — accepted as a known, documented limitation of the capstone deployment; a real AIA
deployment would use a properly licensed Okta org. Client ID/secret and issuer URL are stored as
`OKTA_CLIENT_ID` / `OKTA_CLIENT_SECRET` / `OKTA_ISSUER` (server-only env vars, mirrored in both
`frontend/.env.local` and Vercel's project environment variables — they are not synced automatically
between the two).

---

## 17. Evaluation Study Design

### Objective

Empirically compare four prompting strategies for LLM-based insurance claims assessment. Produce domain-specific findings on hallucination mitigation. The combined strategy (current design) is expected to outperform all others — this validates the design choices made throughout the build.

### Four Strategies

| Strategy | Description |
|---|---|
| **Direct** | "Assess this claim and give a recommendation" — no structure, no reasoning |
| **Chain-of-Thought** | "Check each rule in order, show your working with exact values" |
| **Structured Output** | JSON schema + enum constraints, no explicit reasoning |
| **Combined (current)** | Chain-of-thought + structured output + grounding instructions |

### Test Set — 20 Claims (5 per type)

| Scenario | Expected Recommendation |
|---|---|
| Clear APPROVE — active policy, all rules pass | APPROVE |
| Clear REJECT — policy lapsed (mandatory rule fail) | REJECT |
| REFER — rules pass, documentation missing | REFER |
| Edge case — claim just after waiting period, amount at limit | Context-dependent |
| Validation test — wrong claim type for workflow | REJECT or error |

### MLflow Experiment Structure
```
Experiment: Claims_Assessment_Prompting_Study (ID: 2726789194105433)
├── direct_life_CLM-XXXX
├── cot_life_CLM-XXXX
├── structured_life_CLM-XXXX
├── combined_life_CLM-XXXX
└── ... (80 runs: 4 strategies × 20 claims)
```

### Expected Findings
- Direct: highest hallucination, lowest accuracy, lowest judge scores
- CoT alone: improved accuracy, free-form hallucinations persist
- Structured output alone: low hallucination, misses nuance on edge cases
- Combined: lowest hallucination, highest accuracy, highest judge scores — validates design

---

## 18. Governance Framework (The Reusable Contribution)

### Title

"A Technical Governance Framework for Agentic AI in Regulated Financial Services"

### Six Governance Layers

```
Layer 1: Data Access Governance (MCP Server)
  → No direct DB access from agents; governed, auditable API layer
  → MAS AIRG: "key AI risk management systems" | IMDA: Internal Governance

Layer 2: Output Governance (Structured Schemas)
  → JSON schema + enum constraints on all inter-node outputs
  → Prevents hallucinated recommendations
  → IMDA: "Operations Management — Robustness"

Layer 3: Prompt Governance (MLflow Prompt Registry)
  → Every system prompt versioned; prompt_version logged with every decision
  → MAS AIRG: "AI lifecycle controls"

Layer 4: Decision Governance (Audit Log + LLM-as-Judge)
  → Every assessment logged with model version, prompt version, judge scores
  → IMDA: "Operations Management — Auditability"
  → MAS AIRG: "oversight of AI risk management"

Layer 5: Change Governance (DSL Change Management System)
  → Every modification to AI workflow logic requires named sign-off
  → MAS AIRG: "AI lifecycle controls — change management"
  → IMDA: "Internal Governance — accountability"

Layer 6: Continuous Improvement Governance (Prompt Optimisation Agent)
  → Reads MLflow metrics, proposes improvements via change_approvals
  → Never auto-applies — all suggestions require human approval
  → MAS AIRG: "capabilities and capacity — continuous improvement"
  → IMDA: "Operations Management — monitoring and review"
```

### What Makes This Reusable

Any financial institution deploying agentic AI can apply these six layers regardless of orchestration platform. Technology-agnostic — applicable to LangChain, LlamaIndex, or any future platform. This is the academic contribution beyond the specific AIA implementation.

---

## 19. Stakeholder Map

| Stakeholder | How System Serves Them |
|---|---|
| **Claims Officer** | Chat interface; reports with clause refs, documentation checklists, next action |
| **Claims Manager** | Management dashboard — volume, recommendation rates, quality trends, workload |
| **Compliance Officer** | Audit log — every decision traceable to rules, clauses, model version, prompt version |
| **Internal Auditor** | assessment_logs + change_approvals + MLflow links — complete decision and change history |
| **IT / AI Engineer** | MLflow tracking + DSL Change Management — prompt versions, model performance, change control |
| **Business Team (Kenix)** | Orchestrator chatbot + dashboard — real-time claim status, domain-routed assessments, management summaries |

---

## 20. Build Status

| Component | Status | Notes |
|---|---|---|
| Supabase schema (7 tables) | ✅ Done | policies, claims, claim_documents, eligibility_rules, assessment_logs, workflow_nodes, change_approvals |
| Synthetic data | ✅ Done | 1,000 policies, 1,522 claims, 1,000 PDFs, 24 rules |
| MCP server v2.1.0 (28 endpoints, see §10) | ✅ Done | All core + assessment-logs + workflow-nodes + change-approvals + /claims/domain + DSL Storage/snapshot endpoints + explanations + missing-documentation-checks |
| MCP cloud deployment | ✅ Done | https://sit-capstone.onrender.com |
| MLflow + Databricks connection | ✅ Done | Experiment ID: 2726789194105433 |
| setup_mlflow.py | ✅ Done | Auto-detects username, creates experiment, logs test run |
| Life_Claim_Details workflow | ✅ Done | Tested; answer + suggestion_context output |
| Life_Policy_Details workflow | ✅ Done | Tested; structured response |
| Life_Claim_and_Policy_Details workflow | ✅ Done | Tested; combined response |
| Life_Assess_Claim workflow | ✅ Done | End-to-end works; LLM-as-Judge integrated |
| LLM-as-Judge (all Assess_Claim workflows) | ✅ Done | Scores produced and logged |
| Health_Claim_Details workflow | ✅ Done | |
| Health_Policy_Details workflow | ✅ Done | |
| Health_Claim_and_Policy_Details workflow | ✅ Done | |
| Health_Assess_Claim workflow | ✅ Done | |
| CI_Claim_Details workflow | ✅ Done | |
| CI_Policy_Details workflow | ✅ Done | |
| CI_Claim_and_Policy_Details workflow | ✅ Done | |
| CI_Assess_Claim workflow | ✅ Done | |
| Disability_Claim_Details workflow | ✅ Done | |
| Disability_Policy_Details workflow | ✅ Done | |
| Disability_Claim_and_Policy_Details workflow | ✅ Done | |
| Disability_Assess_Claim workflow | ✅ Done | |
| Orchestrator Chatbot | ✅ Done | Test_Orchestrator_1-1.yml (75 nodes, 17 conversation variables — canonical, sole file); all test cases pass; CLM-only domain routing resolved via /claims/domain; followup/intent/router prompts calibrated |
| `claims_history` / `customer_history` intents | ✅ Done | 2 new shared sub-workflows (`Claims_History.yml`, `Customer_History.yml`); orchestrator extended to 6 intents; 3 deterministic routing-bug fixes (fresh-ID override, `IF/ELSE 13` case-order, backend 404-on-empty fix); confirmed working live via the actual Vercel chat (not just Dify's Run panel) |
| 3 new product-capability Dify apps | ✅ Done | `Explain_Assessment_Reasoning` (dual-mode: explains a logged verdict, or does a fresh walkthrough if none exists), `Fraud_Anomaly_Risk_Signals`, `Missing_Documentation_Advisor` — each independently valuable, none produce an APPROVE/REJECT/REFER recommendation. Built manually in Dify UI from generated DSL, imported, tested against real claim data; prompts recalibrated once each (Fraud app was over-flagging any 2+-claim customer; Missing Docs app was hallucinating non-existent rule IDs for generic real-world doc requirements) |
| 3 new research-only Dify apps | ✅ Done | `Direct_Research`, `CoT_Research`, `Structured_Research` — minimal single-LLM-node apps isolating the 2×2 (reasoning × structure) design for the prompting-strategy study; Combined reuses the existing 4 production `*_Assess_Claim` workflows unchanged |
| MLflow Prompt Registry | ✅ Done | `evaluation/register_prompts.py` — 79 LLM prompts registered as `workspace.default.{workflow}_{node}_v1_0` (UC-qualified naming, see §12) |
| Local MLflow Prompt Registry viewer | ✅ Done | Databricks Free Edition has no browsable Prompts UI (investigated, see §12) — `evaluation/sync_prompt_registry_local.py` mirrors all 79 prompts/109 versions into a self-hosted local server; `evaluation/start_local_prompt_registry.sh` launches it at `http://127.0.0.1:5001` |
| `GET /claim-documents` endpoint | ✅ Done | `mcp_server/main.py` — returns `[]` (not 404) for a claim with no documents, a deliberate deviation from the file's other 404-on-empty endpoints |
| Full dataset consistency backfill | ✅ Done | `backfill_claim_evidence.py` — added `claims.diagnosis`, `claims.condition_is_pre_existing`, `claim_documents.content_summary` columns; backfilled all ~1034 health / 83 CI / 353 disability / 18 life-accidental_death claims (not just test-case claims), fixing a structural gap where 3 of 4 policy types could never produce a clean, evidence-backed APPROVE |
| Evaluation study — 4-strategy research harness | ✅ Done | `evaluation/test_claims.json` (20 cases) + `metrics.py` + `run_evaluation.py`; final validated Combined result 18/20 (90%), mismatch detection 4/4 (100%); Direct/CoT/Structured recorded per condition. 3 real production-workflow bugs found and fixed along the way: missing `claim_documents` visibility, domain-mismatch detection, non-deterministic rule counting (see `evaluation/results/`) |
| Product-capability evaluation harness | ✅ Done | `evaluation/product_test_cases.json` (15 cases) + `product_metrics.py` + `run_product_evaluation.py`; final validated: Missing Docs Advisor 5/5, Fraud/Anomaly Signals 4/5, Explain Assessment Reasoning 5/5 |
| dsl_manager/ (parser, diff, approvals, git) | ✅ Done | parser, diff, approvals, git_commit, __main__ CLI |
| evaluation/prompt_advisor.py | ✅ Done | Deterministic heuristic-based (no LLM call — no OpenAI key available, see §15); real run against all 4 production workflows created 8 pending `change_approvals` rows, all correctly flagging `hallucination_risk` as weakest dimension |
| Frontend — all 4 views | ✅ Done | Next.js 14, Tailwind, Recharts — Chat, Audit Log, Dashboard, DSL Management |
| Dify key removed from client bundle | ✅ Done | Chat view now proxies through `app/api/dify/chat/route.ts`; was previously `NEXT_PUBLIC_DIFY_API_KEY`, shipped to the browser — rotated after the fix |
| DSL scan/extraction consolidated | ✅ Done | `mcp_server/main.py` now imports `dsl_manager/parser.py` + `diff.py` instead of duplicating extraction logic; fixed a `node_id` UUID bug and missing `change_approvals` columns (`node_type`, `new_content`, `new_hash`) surfaced by the fix |
| Okta SSO for DSL Change Management | ✅ Done | NextAuth.js + Okta Integrator Free Plan org; gates `/dsl` only; verified identity replaces free-text approver name |
| Whole-file workflow version history | ✅ Done | `dsl-governance-history` GitHub branch, dedicated from `main`; `commit_workflow_snapshot`/`list_workflow_snapshots`/`ensure_governance_branch` in `git_commit.py`; new "Workflow Snapshots" frontend tab; CLI `snapshot`/`history` subcommands. Fixed a real GitHub API gotcha (path-filtered commit history silently excludes no-op-content commits — matched on commit message prefix instead). Committed `7982d70` |
| `dify-data/` → Supabase Storage migration | ✅ Done | New private `dify-workflows` bucket is now the sole "current version" source for `/dsl/scan`, `/dsl/status`, `/dsl/snapshot-files`, snapshot-taking, and node-diff — zero disk dependency. `dify-data/*.yml` on disk kept permanently as a frozen historical artifact only (Jasbir's explicit choice, for the report's before/after narrative), never read by the running system. One-time seed via `migrate_workflows_to_storage.py` (all 25 files, re-run-safe). `parse_workflow_content()` added to `dsl_manager/parser.py` so parsing works on in-memory YAML text (Storage/GitHub), not just local files |
| Node-level snapshot comparison | ✅ Done | `GET /dsl/snapshots/node-diff` — latest GitHub snapshot vs. current Storage content, node-level only (not raw whole-file diff), reusing `parse_workflow_content`/`compute_diff`; "Changes Since Last Snapshot" section in the frontend |
| Workflow upload page | ✅ Done | `POST /dsl/upload` (multipart, validates real Dify DSL before accepting) + frontend upload card in the Workflow Snapshots tab — add/update a workflow directly from the browser, no manual file placement or backend access needed. Added `python-multipart` dependency |
| Governance review pass (2026-07-13/14 session) | ✅ Done | 12 real pending `change_approvals` reviewed and actioned: 5 approved (deterministic rule-count fix formalized across Life/Health/Disability/CI, plus a Disability `policy_document_analysis` baseline correction) + 4 approved (`claim_documents`/`content_summary` visibility fix, same 4 workflows) + 7 rejected (unapplied `prompt_advisor_agent` hallucination-guardrail proposals — general guardrails already present and judged sufficient). All via CLI with real GitHub commits |
| **Deploy gap:** Storage/snapshot work not yet live on Render | 🔲 Open | `GITHUB_TOKEN`/`GITHUB_REPO`/`GITHUB_GOVERNANCE_BRANCH` only in local `mcp_server/.env` as of 2026-07-14, not yet mirrored to Render's dashboard; `python-multipart` needs to install on Render's next deploy for `/dsl/upload` to work live |
| `Explain_Assessment_Reasoning` / `Missing_Documentation_Advisor` frontend integration | ✅ Done | Both wired into the Audit Log's consolidated "AI Insights" menu (§16); `assessment_explanations`/`missing_documentation_checks` tables + 4 new MCP endpoints (§7, §10); fixed a real bug where Explain always explained a claim's newest assessment regardless of which row was clicked (required `log_id` threading end-to-end) and a hallucination-risk-score interpretation bug in Explain's prompt |
| `rule_checks` persistence fix | ✅ Done | Closed a real logic gap: per-rule reasoning was always computed by `rule_by_rule_eligibility_check` but discarded after `compute_rule_counts` reduced it to two integers — a claim could land on REFER with zero visibility into which rule caused it. Now persisted (`assessment_logs.rule_checks`, §7) across all 4 `*_Assess_Claim` workflows and used by Explain to cite specific rules |
| Audit Log "AI Insights" consolidation | ✅ Done | Replaced 3 separate always-visible columns (Explanation/Missing Docs/Fraud) with one compact menu — 3 visual options mocked as a Claude Artifact against real claim data before building; fixed a real row-expansion bug (`log.id` never existed, fabricated field → every row shared the same `undefined` key) along the way |
| LLM-as-Judge grounding redesign | ✅ Done | See §13 — judge now grounded in real `claim_record`/`policy_record` with explicit rubric anchors instead of scoring an ungrounded narrative; `judge_overall_score` now a deterministic average via new `compute_judge_overall` code node instead of an LLM-invented number. Verified live across all 4 domains post-redesign. A mid-build mistake (redesign applied on top of a stale `dify-data/` copy, regressing `rule_checks`) was caught and fixed before reaching Dify — see §14's gotcha note |
| Dashboard — Rule Failure Analysis + Missing Documentation panels | ✅ Done | New sections using the now-persisted `rule_checks` and `missing_documentation_checks` data (§16); KPI cards fixed to show distinct-claims count + trailing-50-run averages instead of misleading all-time/raw-row numbers |
| DSL page — `dify-data/` label cleanup | ✅ Done | Workflow Snapshots tab no longer shows the `dify-data/` prefix anywhere in the UI (§14) — cosmetic only, underlying API contract unchanged |
| `claims.status` write-back + status cross-check | ✅ Done | `POST /assessment-logs` finalizes a `pending` claim's status on its first real assessment (§7, §10), and computes an observe-only `status_cross_check` for already-decided claims — mutually exclusive per request, neither ever influences the verdict. Dify workflows deliberately left untouched (§9's design-boundary note) — `run_evaluation.py`'s combined strategy snapshots/restores `claims.status` itself instead of relying on a Dify-side flag. New Dashboard "Status Cross-Check" panel + Audit Log mismatch warning icon (§16). Committed `86310c8` (write-back), `16a6459` (cross-check) |
| Repeat-Assessment Consistency + Missing Docs REJECT-scoping | ✅ Done | New Dashboard panel grouping `assessment_logs` by `claim_id`+`prompt_version` to check whether repeated runs agree (§16) — surfaced a real `prompt_version`-staleness limitation, documented in the panel itself. Missing Documentation Advisor now also shown on REJECT rows where `rule_checks.evidence_fields` points at `claim_documents` (§7, §16) — closes the previously-deferred REJECT-scoping idea. Both client-side only, no backend/Dify changes. Committed `16a6459` |
| `mlflow_run_id` wiring + `prompt_version` staleness fix | ✅ Done | `POST /assessment-logs` now creates a real Databricks MLflow run per assessment (previously 0/345 real rows had one — the evaluation harness's own runs were never connected back) and overrides the known-stale `prompt_version` default server-side (§7, §10). MLflow logging runs as a `BackgroundTask` — found it took 13+ seconds even warm, unacceptable to block a chat response on. `mlflow`/`databricks-sdk` added to `requirements.txt`. Committed `a35bb6e` |
| `judge_comments` persistence | ✅ Done | The judge's qualitative reasoning per score was computed on every assessment but never sent past Dify at all — `write_assessment_log`'s body never referenced it. Now logged as an MLflow artifact (not a new `assessment_logs` column) alongside `rule_checks`. Required a small Dify edit (one field added to `prepare_assessment_log_payload`'s output + `write_assessment_log`'s body, all 4 workflows) — the one fix this session that couldn't be done server-side only, since the MCP server has zero visibility into a field Dify never sent it |
| Eligibility-rules coverage review (Phases 1-3) | ✅ Done | Full review of all 24 (then-existing) rules against the 8 synthetic `rejection_reason` categories found real, precisely-scoped gaps (§7). **Phase 1:** 6 new rules added (`RULE-LI-006/007/008`, `RULE-CI-007`, `RULE-DI-008`, `RULE-HE-007`) — zero Dify changes needed, rules fetched dynamically. **Phase 2:** `backfill_claim_evidence_v2.py` backfills the data those rules need (diagnosis/pre-existing for life/CI/disability, documents for health and life's death/TPD categories) — consistency-aware, not just presence-filling. **Phase 3:** `fix_rejection_reasons.py` corrects the 227 already-generated rejected claims to match the real rule set (61 reassigned, 17 contradicting documents removed) and `generate_data.py` fixed for future correctness (domain-and-category-aware pool, not one shared list). Verified: 0 mismatches/contradictions remain across all 227 rejected claims. Committed `bb395e1` |
| Target-leakage fix (`claim_record_json`) | ✅ Done | `status`/`rejection_reason` — the claim's outcome, not evidence — were included in the single variable feeding all 5 downstream LLM nodes, discovered via a real incident where the rule-checker deferred to a stale status over a genuinely-present document. Fixed at the one choke point (`extract_claims_fields`), all 4 workflows, verified live (§9) |
| **Deploy gap:** write-back/cross-check not yet live on Render | 🔲 Open | Same pattern as the Storage/snapshot deploy gap above — local MCP server only until the latest `main` is deployed |
| UAT + SUS | 🔲 July 2026 | AIA Technology team, target SUS > 68 |
| Final report | 🔲 July 2026 | Deadline 19 July 2026 |

---

## 21. Timeline

| Period | Target |
|---|---|
| **Late June** | DSL Change Management System — `dsl_manager/` modules (`parser.py`, `diff.py`, `approvals.py`, `git_commit.py`); Okta SSO for `/dsl` |
| **Done (2026-07-06/07)** | Frontend — all 4 views; MLflow Prompt Registry (79 prompts) + local viewer; 6 new Dify apps (3 product capabilities + 3 research-only); full dataset consistency backfill; 4-strategy research harness (18/20 final); 3-app product-capability harness (14/15 final); `evaluation/prompt_advisor.py` run for real (8 pending approvals) |
| **Done (2026-07-13)** | `claims_history`/`customer_history` orchestrator intents (2 new shared sub-workflows, 6-intent orchestrator, 3 real routing-bug fixes); `/claims`/`/policies` 404-on-empty backend fix, deployed and confirmed live; stale `Test_Orchestrator-1.yml` deleted, single canonical orchestrator file — full build scope now considered complete |
| **Done (2026-07-13/14)** | Whole-file workflow version history (`dsl-governance-history` GitHub branch); migrated DSL "current version" source of truth from local disk to a new private Supabase Storage bucket (`dify-workflows`), `dify-data/` kept as a frozen historical artifact only; node-level snapshot-vs-current comparison; workflow upload page (Storage-backed, no manual file placement); 12-item governance review pass (5+4 approved, 7 rejected, real GitHub commits). Committed `7982d70` + `983b561`. Not yet deployed to Render — local-only until env vars mirrored |
| **Done (2026-07-14/15)** | `Explain_Assessment_Reasoning`/`Missing_Documentation_Advisor` integrated into the Audit Log frontend (`assessment_explanations`/`missing_documentation_checks` tables, 4 new MCP endpoints); fixed Explain's row-specificity bug (`log_id` threading) and a hallucination-risk-score interpretation bug; fixed a real Audit Log row-expansion bug (`log.id` → `log.log_id`); closed the `rule_checks` persistence logic gap across all 4 `*_Assess_Claim` workflows; consolidated 3 separate Audit Log columns into one "AI Insights" menu |
| **Done (2026-07-16)** | LLM-as-Judge grounding redesign — judge now scores against real `claim_record`/`policy_record` with explicit rubric anchors, `judge_overall_score` computed deterministically (§13); caught and fixed a mid-build regression from editing a stale `dify-data/` copy, now documented as a standing gotcha (§14); Dashboard gained Rule Failure Analysis + Missing Documentation panels and fixed misleading KPI cards (distinct-claims count, trailing-50-run averages) (§16); DSL page's Workflow Snapshots tab no longer shows the `dify-data/` prefix; 56-claim backfill run across all 4 domains to seed fresh test data (55/56 succeeded, one transient 422 resolved on retry); `claims.status` write-back for pending claims + observe-only status cross-check for already-decided claims, both computed server-side with the Dify workflows deliberately left untouched (§7, §9, §10); new Dashboard "Status Cross-Check" panel (§16); Repeat-Assessment Consistency Dashboard panel, which surfaced a real `prompt_version`-staleness limitation while being validated against production data; Missing Documentation Advisor extended to document-related REJECT rows via `rule_checks.evidence_fields` (§7, §16); fixed `mlflow_run_id` (was 0/345 real rows populated — nothing in the live pipeline ever created an MLflow run) and the stale `prompt_version` default, both server-side, MLflow logging as a `BackgroundTask` after discovering it took 13+ seconds even warm (§7, §10); `judge_comments` persistence via MLflow artifact (§10, §13); full eligibility-rules coverage review — 6 new rules, a two-domain-wider backfill (`backfill_claim_evidence_v2.py`), and a rejection-reason correction pass across all 227 rejected claims (§7, §8, §20); target-leakage fix removing `status`/`rejection_reason` from `claim_record_json`, the single variable feeding all 5 assessment LLM nodes (§9) |
| **July 1-14** | UAT with AIA Technology team; SUS questionnaire |
| **July 15-19** | Final report submission |

---

## 22. Final Report Structure

1. Introduction — project background, objectives, scope
2. Literature Review — AI in insurance; LLMs and agentic AI; LLM hallucination; platform selection; LLMOps + MLflow; LLM-as-Judge; AI governance (IMDA + MAS AIRG); Model Context Protocol; AI change management in regulated systems
3. System Architecture — eight components, six governance layers, design decisions
4. Regulatory Alignment — IMDA and MAS AIRG mapping tables
5. Implementation — all workflows, MCP server, MLflow, LLM-as-Judge, DSL system, prompt optimisation agent
6. Evaluation Study — methodology, 4 strategies × 20 claims, results, hallucination analysis
7. UAT and SUS Results
8. Governance Framework — six-layer reusable framework
9. Discussion — findings, limitations, future work
10. Conclusion

**Central argument:** The combined prompting strategy (chain-of-thought + structured output + grounding) produces the lowest hallucination rate and highest quality scores across all four insurance claim types. The six-layer governance framework provides a reusable reference implementation of the IMDA Model Framework and MAS AIRG Guidelines for agentic AI in regulated financial services.

**Citation format:** IEEE

---

*Last updated: 14 July 2026. Any AI assistant or developer picking up this project must read this document in full before making changes to the codebase, Dify workflow configurations, MLflow tracking setup, or DSL artifacts.*