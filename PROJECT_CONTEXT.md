# AIA Capstone Project — Full Context Document
> **For:** Claude Code and any AI assistant picking up this project  
> **Author:** Jasbir Kaur (2302990), Applied Computing (FinTech), Singapore Institute of Technology  
> **Last updated:** 13 July 2026 (active build log)

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
│   ├── main.py                  # All 13 endpoints (v2.0.0)
│   └── .env                     # SUPABASE_URL, SUPABASE_KEY, DATABRICKS_HOST, DATABRICKS_TOKEN (not committed)
├── frontend/                    # React (Vercel) — 4 views
├── dify-data/                   # Dify DSL YAML exports for all workflows
├── evaluation/
│   ├── test_claims.json         # 20 test claims + ground truth
│   ├── run_evaluation.py        # 4 strategies × 20 claims = 80 MLflow runs
│   ├── metrics.py               # Hallucination detection + scoring functions
│   └── prompt_advisor.py        # Prompt optimisation agent
├── dsl_manager/
│   ├── parser.py                # Parses Dify YAML, extracts LLM/code/agent nodes
│   ├── diff.py                  # Diffs new DSL against stored version
│   ├── approvals.py             # Sign-off workflow
│   └── git_commit.py           # Commits approved changes to GitHub
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
| `status` | TEXT | pending, approved, rejected, under_review |
| `rejection_reason` | TEXT | |
| `assigned_officer` | TEXT | |
| `notes` | TEXT | |
| `created_at` | TIMESTAMP | |
| `diagnosis` | TEXT | **Added 2026-07-06** — plain-language diagnosis/condition for the claim. Needed because `RULE-HE-005` (Pre-existing Condition Exclusion) requires knowing what the condition actually is; originally there was no field anywhere in the schema for this, making the rule permanently unverifiable regardless of any other data. Nullable — most claims still won't have it populated. |
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
| `content_summary` | TEXT | **Added 2026-07-06** — plain-text summary of what the document actually states. Without this, this table only ever stored metadata (type/name/url), so a rule like `RULE-DI-007` ("incident must not be self-inflicted **as stated in medical report**") could never be confirmed no matter which document type was present — presence alone can't satisfy a rule that depends on document content. Nullable — most rows still won't have it. |

### `eligibility_rules`
| Column | Type | Notes |
|---|---|---|
| `rule_id` | TEXT PK | e.g. RULE-LI-001 |
| `policy_type` | TEXT | |
| `rule_name` | TEXT | |
| `rule_description` | TEXT | |
| `condition` | TEXT | |
| `is_mandatory` | BOOLEAN | FAIL = hard rejection |

24 rules: 5 life, 6 health, 6 critical illness, 7 disability.

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
| `prompt_version` | TEXT | From MLflow Prompt Registry e.g. life_rule_check_v1.2 |
| `mlflow_run_id` | TEXT | Links to MLflow run |
| `judge_completeness_score` | FLOAT | 0-1 |
| `judge_consistency_score` | FLOAT | 0-1 |
| `judge_hallucination_risk_score` | FLOAT | 0-1 (1 = no hallucination) |
| `judge_clarity_score` | FLOAT | 0-1 |
| `judge_overall_score` | FLOAT | Average of four |
| `assessed_at` | TIMESTAMP | |

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
- **24 eligibility rules** — 5 life, 6 health, 6 CI, 7 disability

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
  → rules_evaluated[], mandatory_rules_failed, hard_blockers_present
  ↓
Policy Document Analysis (LLM GPT-5.2, structured output)
  — uses full policy_data including policy_text
  → coverage_status, relevant_clauses[], applicable_exclusions[]
  ↓
Synthesise Final Verdict (LLM GPT-5.2, structured output)
  → recommendation (APPROVE/REJECT/REFER_FOR_FURTHER_REVIEW), confidence_level
  ↓
Format Final Report (LLM GPT-5.2, plain text)
  ↓
LLM-as-Judge (LLM GPT-5.2, structured output) ← Component 5
  → completeness, consistency, hallucination_risk, clarity scores (0-1 each)
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
- DSL YAML exports in `dify-data/`

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

### All 19 Endpoints (corrected 2026-07-13 — table had drifted from the actual file)

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
| `/assessment-logs` | POST | Write assessment result to audit log |
| `/assessment-logs` | GET | Query audit log (management dashboard) |
| `/workflow-nodes` | GET | Stored DSL nodes for a workflow |
| `/workflow-nodes` | POST | Store node after approval |
| `/change-approvals` | GET | Pending/approved changes |
| `/change-approvals` | POST | Create change approval request |
| `/change-approvals/{id}/approve` | POST | Approve + trigger git commit |
| `/change-approvals/{id}/reject` | POST | Reject change |
| `/dsl/status` | GET | DSL scan status (server-side scan of `dify-data/`) |
| `/dsl/scan` | POST | Server-side DSL scan trigger (frontend DSL Management view) |

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
GITHUB_TOKEN=[personal access token for git commits]
GITHUB_REPO=jas12481/sit_capstone
```

---

## 11. Component 3 — Database Layer (Supabase)

- **Region:** Singapore (ap-southeast-1)
- **RLS:** Enabled on all 7 tables
- **Access:** MCP server only (secret key bypasses RLS)
- **Tables:** policies, claims, claim_documents, eligibility_rules, assessment_logs, workflow_nodes, change_approvals

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

### Dify Implementation

**Node name:** `llm_judge` | **Model:** GPT-5.2 | **Structured Output:** ON

**JSON Schema:**
```json
{
  "type": "object",
  "properties": {
    "completeness_score": {"type": "number", "minimum": 0, "maximum": 1},
    "consistency_score": {"type": "number", "minimum": 0, "maximum": 1},
    "hallucination_risk_score": {"type": "number", "minimum": 0, "maximum": 1},
    "clarity_score": {"type": "number", "minimum": 0, "maximum": 1},
    "overall_score": {"type": "number", "minimum": 0, "maximum": 1},
    "completeness_reasoning": {"type": "string"},
    "consistency_reasoning": {"type": "string"},
    "hallucination_reasoning": {"type": "string"},
    "clarity_reasoning": {"type": "string"},
    "flagged_issues": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["completeness_score", "consistency_score", "hallucination_risk_score",
               "clarity_score", "overall_score", "flagged_issues"]
}
```

**System Prompt:** You are a quality assurance evaluator for an AI insurance claims assessment system. Evaluate reports on four dimensions: completeness, consistency, hallucination risk, and clarity. Be strict and objective. Do not score above 0.8 unless the report is genuinely excellent in that dimension.

**User Prompt:** Evaluate this assessment report. Claim type: {{claim_type}}. Applicable eligibility rules: {{eligibility_rules}}. Policy type: {{policy_type}}.

ASSESSMENT REPORT:
{{format_final_report.text}}

Score each dimension 0.0-1.0 and identify specific issues.

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

- `dsl_manager/parser.py` — reads YAML, extracts nodes, computes SHA256 hashes. This is the single
  source of truth for node extraction — `mcp_server/main.py`'s `/dsl/scan` endpoint imports these same
  functions rather than re-implementing them, so the CLI and the frontend-triggered scan always agree
  on what counts as "changed."
- `dsl_manager/diff.py` — human-readable before/after diff
- `dsl_manager/approvals.py` — create_approval, approve_change, reject_change
- `dsl_manager/git_commit.py` — GitHub API commit with attribution metadata

### Audit Trail Chain

```
Assessment decision → prompt_version → change_approvals record → git_commit_hash → exact prompt text
```

An auditor can trace any assessment back to who approved the prompt that produced it.

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

**2. Audit Log View** *(compliance and audit stakeholders)* — table of assessment_logs, filters (date, workflow type, recommendation, confidence, judge score threshold), expandable rows with full details + judge scores, link to MLflow run

**3. Management Dashboard** *(business stakeholders)* — claims volume by type, recommendation distribution chart, LLM-as-Judge score trend over time, confidence by workflow type, anomaly flags, workload by officer

**4. DSL Change Management View** *(IT governance)* — all workflows with current version and last commit, pending changes with full diff, approval form (verified identity + reason mandatory), approval history with Git commit links

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
| MCP server v2.1.0 (14 endpoints) | ✅ Done | All core + assessment-logs + workflow-nodes + change-approvals + /claims/domain |
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
| UAT + SUS | 🔲 July 2026 | AIA Technology team, target SUS > 68 |
| Final report | 🔲 July 2026 | Deadline 19 July 2026 |

---

## 21. Timeline

| Period | Target |
|---|---|
| **Late June** | DSL Change Management System — `dsl_manager/` modules (`parser.py`, `diff.py`, `approvals.py`, `git_commit.py`); Okta SSO for `/dsl` |
| **Done (2026-07-06/07)** | Frontend — all 4 views; MLflow Prompt Registry (79 prompts) + local viewer; 6 new Dify apps (3 product capabilities + 3 research-only); full dataset consistency backfill; 4-strategy research harness (18/20 final); 3-app product-capability harness (14/15 final); `evaluation/prompt_advisor.py` run for real (8 pending approvals) |
| **Done (2026-07-13)** | `claims_history`/`customer_history` orchestrator intents (2 new shared sub-workflows, 6-intent orchestrator, 3 real routing-bug fixes); `/claims`/`/policies` 404-on-empty backend fix, deployed and confirmed live; stale `Test_Orchestrator-1.yml` deleted, single canonical orchestrator file — full build scope now considered complete |
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

*Last updated: 13 July 2026. Any AI assistant or developer picking up this project must read this document in full before making changes to the codebase, Dify workflow configurations, MLflow tracking setup, or DSL artifacts.*