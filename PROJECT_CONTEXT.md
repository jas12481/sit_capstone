# AIA Capstone Project — Full Context Document
> **For:** Claude Code and any AI assistant picking up this project  
> **Author:** Jasbir Kaur (2302990), Applied Computing (FinTech), Singapore Institute of Technology  
> **Last updated:** May 2026

---

## 1. Project Identity

| Field | Detail |
|---|---|
| **Project Title** | AI Agentic Workflow Development for Insurance Claims Operations |
| **Module** | BAC3004 Capstone Project, Singapore Institute of Technology (SIT) |
| **Student** | Jasbir Kaur |
| **Programme** | Applied Computing (FinTech) |
| **Organisation** | AIA Singapore Pte. Ltd. |
| **Project Period** | 5 January 2026 – 7 August 2026 |
| **Report Deadline** | 19 July 2026 |
| **Build Completion Target** | End of June 2026 |
| **Testing / UAT Target** | 1 July to 14 July 2026 |
| **Industry Supervisor** | Kartik-K Mahadevan, Associate Director AI & Machine Learning, Technology – Data Architecture Development |
| **Academic Supervisor** | Assoc. Prof. Harminder Singh, SIT |
| **GitHub Repo** | `https://github.com/jas12481/sit_capstone` (public) |

---

## 2. Project Overview and Unique Contribution

### What This Project Is

A **governed multi-agent AI system** for AIA Singapore's insurance claims operations department. Claims officers interact with a custom web UI, submit natural language queries about claims and policies, and the system orchestrates specialised AI agents to retrieve data, reason over it, and produce structured, explainable, auditable outputs.

The system is modelled on a real internal AIA initiative. Because live AIA data cannot be used for academic purposes, the capstone uses a **synthetic dataset** that mirrors real data structure without exposing proprietary information.

### The Unique Contribution

> **A reference implementation of the IMDA Model AI Governance Framework (2020) and MAS Guidelines on AI Risk Management for Financial Institutions (2025) for agentic AI in insurance claims operations — incorporating an empirical evaluation study of prompting strategies for hallucination mitigation, an LLM-as-Judge quality evaluation layer, and a governed DSL change management system for AI workflow configurations.**

This project makes four distinct contributions:
1. A working governed agentic AI system satisfying two Singapore regulatory frameworks
2. An empirical study comparing four prompting strategies across 20 test claims (hallucination rate, accuracy, clause reference validity)
3. An LLM-as-Judge automated quality scoring layer linked to MLflow
4. A DSL change management system providing governed version control for Dify workflow configurations

### Context: Relationship to Kenix's Project

Kenix (business team) covers the end-to-end business process of AI-assisted claims handling. This project occupies the **AI engineering layer**:
- **Kenix:** How the business process should be redesigned around AI
- **Jasbir:** How the AI must be built, governed, evaluated, and audited to be safe in a regulated environment

These are complementary. The technical contributions (governance framework + evaluation study + LLM-as-Judge + DSL change management) cannot be made from the business process side.

### Why This Matters

AIA Singapore is a MAS-regulated financial institution. Any AI system used in claims processing must satisfy the MAS AI Risk Management Guidelines (2025). Generative AI in this context must be:
- **Governed** — traceable, auditable, satisfying MAS AIRG requirements
- **Explainable** — clause-level reasoning visible to officers, auditors, compliance
- **Consistent** — structured output constraints prevent free-form hallucination
- **Evaluated** — systematic measurement of quality via MLflow and LLM-as-Judge
- **Change-controlled** — any modification to AI logic must be signed off before deployment

---

## 3. Full System Components

The project has **seven major components**:

```
Component 1: Multi-Agent Assessment System (Dify)
Component 2: MCP Server (FastAPI)
Component 3: Database Layer (Supabase)
Component 4: MLflow Experiment Tracking + Prompt Registry (Databricks)
Component 5: LLM-as-Judge Quality Evaluation Layer
Component 6: DSL Change Management System
Component 7: Frontend (React + Vercel)
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
| **Human Involvement** | System recommends only (APPROVE/REJECT/REFER); REFER = mandatory human review; full reasoning trace visible; confidence levels guide human scrutiny |
| **Operations Management** | JSON schema enum constraints (robustness); MLflow tracking (reproducibility); audit log (auditability); LLM-as-Judge (automated quality assurance); chain-of-thought + grounding (hallucination control) |
| **Stakeholder Communication** | Claims officers: assessment reports with clause refs; Management: dashboard + analytics; Auditors: full audit trail; Compliance: traceable structured outputs |

| MAS AIRG Area | System Implementation |
|---|---|
| **Governance Structures** | Defined roles: MCP (data), Dify (orchestration), MLflow (prompt), audit log (decisions), DSL system (change control) |
| **AI Risk Management Systems** | Human-over-the-loop; REFER for uncertainty; confidence logging; LLM-as-Judge quality gate |
| **AI Lifecycle Controls** | MLflow Prompt Registry versions every prompt; DSL Change Management requires sign-off for any workflow change; assessment_logs links every decision to prompt version |
| **Capabilities and Capacity** | Empirical evaluation study: 4 strategies × 20 claims = 80 MLflow runs demonstrating measured capability |

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

2. **LLM reasoning over unstructured text is deliberate.** Schema is lean. `policy_text` contains the full contract. The LLM reads it to handle product-level differences rather than hardcoding logic into structured fields.

3. **Security and explainability drove platform selection.** Dify chosen over LangChain/LlamaIndex for: no sprawling dependency chain; visual workflow builder readable by non-technical stakeholders; aligns with MAS AIRG governance requirements.

4. **Data never leaves the controlled environment.** Dify self-hosted. No data through third-party servers. Essential for MAS compliance.

5. **MCP server is the only data access point.** Agents never query Supabase directly. Clean, auditable, governable layer — implements MAS AIRG "key AI risk management systems."

6. **Structured outputs with enum constraints prevent hallucination at the output layer.** Every inter-node LLM output uses JSON schema with enum values. This is a hallucination control mechanism.

7. **Human-over-the-loop by design.** System recommends, never decides. REFER is the default for uncertainty. Implements IMDA human-centric principle.

8. **Every change to AI logic must be signed off.** The DSL Change Management System enforces this. No prompt or code change can enter production without attribution and approval. Implements MAS AIRG lifecycle controls.

---

## 6. Tech Stack

| Component | Technology | Notes |
|---|---|---|
| **LLM Orchestration** | Dify (self-hosted Docker) | 6 CPU, 8GB RAM. `http://localhost`. GPT-5.2 default |
| **Database** | Supabase (Singapore region, ap-southeast-1) | PostgreSQL with RLS on all tables |
| **Storage** | Supabase Storage (policy-documents bucket) | 1,000 policy PDFs |
| **MCP Server** | Python FastAPI | `mcp_server/main.py`. Supabase secret key bypasses RLS |
| **Frontend** | React + Vercel | Chat UI + Audit Log + Management Dashboard + DSL Change Management UI |
| **PDF Generation** | ReportLab (Python) | 1,000 legal contract PDFs |
| **Experiment Tracking** | MLflow + Databricks Community Edition | Prompt Registry, evaluation tracking, LLM-as-Judge metrics |
| **Version Control** | GitHub (sit_capstone, public) | Connected to Vercel for auto-deploy |
| **Editor / Terminal** | Cursor + Warp | |
| **LLM Provider** | OpenAI GPT-5.2 | All nodes — consistency across evaluation study |

### Local Development URLs
- Dify: `http://localhost`
- MCP Server: `http://localhost:8000`
- Dify → MCP: `http://host.docker.internal:8000` (from inside Docker)
- MLflow UI: Databricks Community Edition

### Folder Structure
```
sit_capstone/
├── mcp_server/
│   ├── main.py                  # All endpoints including assessment-logs, workflow-nodes
│   └── .env                     # SUPABASE_URL, SUPABASE_KEY (not committed)
├── frontend/                    # React (Vercel) — 3 views + DSL management UI
├── dify-data/                   # Dify DSL YAML exports for all workflows
├── evaluation/
│   ├── test_claims.json         # 20 test claims + ground truth
│   ├── run_evaluation.py        # 4 strategies × 20 claims = 80 MLflow runs
│   └── metrics.py               # Hallucination detection + scoring functions
├── dsl_manager/
│   ├── parser.py                # Parses Dify YAML, extracts LLM/code/agent nodes
│   ├── diff.py                  # Diffs new DSL against stored version
│   ├── approvals.py             # Sign-off workflow
│   └── git_commit.py           # Commits approved changes to GitHub
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
| `judge_completeness_score` | FLOAT | LLM-as-Judge score 0-1 |
| `judge_consistency_score` | FLOAT | LLM-as-Judge score 0-1 |
| `judge_hallucination_risk_score` | FLOAT | LLM-as-Judge score 0-1 (1 = no hallucination) |
| `judge_clarity_score` | FLOAT | LLM-as-Judge score 0-1 |
| `judge_overall_score` | FLOAT | Average of four dimensions |
| `assessed_at` | TIMESTAMP | |

**Purpose:** Satisfies MAS AIRG auditability. Every AI decision traceable. Links to MLflow for full context. Judge scores enable quality trend monitoring over time.

### `workflow_nodes` *(DSL Change Management)*
| Column | Type | Notes |
|---|---|---|
| `node_id` | UUID PK | |
| `workflow_name` | TEXT | e.g. "Life Claims Assessment" |
| `workflow_version` | TEXT | e.g. "v1.3" |
| `node_type` | TEXT | llm, code, agent |
| `node_name` | TEXT | e.g. "rule_by_rule_eligibility_check" |
| `node_content` | TEXT | Full prompt text or code |
| `content_hash` | TEXT | SHA256 of node_content — used for change detection |
| `committed_at` | TIMESTAMP | |
| `committed_by` | TEXT | Name of person who committed |
| `git_commit_hash` | TEXT | GitHub commit SHA |

### `change_approvals` *(DSL Change Management)*
| Column | Type | Notes |
|---|---|---|
| `approval_id` | UUID PK | |
| `node_id` | UUID FK | → workflow_nodes |
| `workflow_name` | TEXT | |
| `node_name` | TEXT | |
| `changed_by` | TEXT | Who submitted the change |
| `approved_by` | TEXT | Who signed off |
| `change_reason` | TEXT | Mandatory justification |
| `diff_content` | TEXT | What changed (before vs after) |
| `status` | TEXT | pending, approved, rejected |
| `approved_at` | TIMESTAMP | |
| `git_commit_hash` | TEXT | GitHub commit SHA after approval |

---

## 8. Synthetic Data

- **1,000 policies** — 60 fictional products (15 per type), realistic status distribution (85% active)
- **1,522 claims** — type-specific frequency based on MOH/LIA Singapore statistics
- **1,000 policy PDFs** — 11-page legal contracts (~23KB each)
- **24 eligibility rules** — 5 life, 6 health, 6 CI, 7 disability

**Claim frequency justification (MOH and LIA Singapore):**
- Health: avg 4.0/policy
- Disability: avg 1.0/policy
- Critical illness: avg 0.5/policy
- Life: avg 0.3/policy

**60 Products:**
- Life (15): AIA LifeGuard Essential/Plus/Premier, SecureLife 300/600/Platinum, WholeCover Basic/Premier, FamilyShield Income, MortgageGuard, SeniorGuard 65, BusinessGuard Term, EndowSave 20/25, ConvertTerm Plus
- Health (15): AIA MediShield Basic/Standard/Gold/Gold Max/Platinum, HealthPlus Essential/Comprehensive/Premier, CareShield Basic/Family, CancerCare Protect, MaternaCare, SeniorCare Shield, GlobalCare Elite, WellnessPlus Rider
- Critical Illness (15): AIA CI Essential 5/Protect 10/36/53, CI MultiClaim, EarlyCI Basic/Premier, CancerGuard Plus, HeartGuard Plus, CI Monthly Income, CI Protect 360, SeniorCI Cover, CI FamilyCare, CI BusinessGuard, DreadDisease Premier
- Disability (15): AIA DisabilityGuard Basic/Plus/Premier, IncomeShield Basic/Plus/Premier, TotalCover Disability, OccupationProtect, ExecutiveDisability, FreelanceShield, AccidentDisability, RehabPlus Disability, PartialDisability Cover, SeniorDisability Shield, GroupDisability SME

---

## 9. Component 1 — Multi-Agent Assessment System (Dify)

### System Architecture

```
User (Claims Officer) — Web UI (React, Vercel)
    ↓ natural language query
Orchestrator Chatbot (Dify Agent node)
    ↓ routes to specialist agent
    ├── Claims Assessment Agent (Dify Workflow — main routing)
    │       ├── Life Claims Assessment ✅ COMPLETE
    │       ├── Health Claims Assessment ✅ COMPLETE
    │       ├── Critical Illness Assessment ✅ COMPLETE
    │       └── Disability Assessment ✅ COMPLETE
    ├── Document Generation Agent 🔲
    └── Claims Intelligence Agent 🔲
            ↓ all agents call
    MCP Server (FastAPI)
            ↓
    Supabase
            ↓ every assessment also runs
    LLM-as-Judge → scores logged to assessment_logs + MLflow
```

### The Four Sub-Workflows (All Complete)

Each has identical structure with type-specific prompts:

```
Start (user_query, claim_id [optional], policy_id [optional])
  ↓
Classify Intent (LLM, structured output)
  → intent: CLAIM_ONLY | POLICY_ONLY | BOTH | ASSESS
  → extracted_claim_id, extracted_policy_id
  ↓
IF/ELSE Route by Intent
  ├── CLAIM_ONLY → Fetch Claim → Format Response → Answer
  ├── POLICY_ONLY → Fetch Policy → Format Response → Answer
  ├── BOTH → Fetch Claim + Policy (parallel) → Format Combined → Answer
  └── ASSESS:
        ↓ Fetch Claim (HTTP → MCP)
        ↓ Extract Claim Fields (Code node)
        ↓ Fetch Policy (HTTP → MCP)
        ↓ Extract Policy Fields (Code node)
        ↓ Fetch Eligibility Rules (HTTP → MCP, type hardcoded per workflow)
        ↓ Rule-by-Rule Eligibility Check (LLM GPT-5.2, structured output)
             — uses policy_summary not full policy_text (token limit)
             → rules_evaluated[], mandatory_rules_failed, hard_blockers_present
        ↓ Policy Document Analysis (LLM GPT-5.2, structured output)
             — uses full policy_data including policy_text
             → coverage_status, relevant_clauses[], applicable_exclusions[]
        ↓ Synthesise Final Verdict (LLM GPT-5.2, structured output)
             → recommendation, assessors_summary, confidence_level, rules_summary[]
        ↓ Format Final Report (LLM GPT-5.2, plain text)
        ↓ LLM-as-Judge Quality Check (LLM GPT-5.2, structured output) ← NEW
             → completeness, consistency, hallucination_risk, clarity scores
        ↓ Write to assessment_logs (HTTP → MCP POST /assessment-logs)
        ↓ Answer node
```

### Hallucination Controls

1. JSON schema with enum constraints on all recommendation fields
2. Chain-of-thought: "show your working with exact values, calculate days between dates"
3. Grounding instructions: "only derive from provided context, cite specific clauses"
4. Eligibility rules filtered by policy_type — model sees only 5-7 rules not all 24
5. Separated reasoning nodes — Rule-by-Rule and Policy Document Analysis are distinct
6. LLM-as-Judge automated hallucination risk scoring after every assessment

### Assessment Output Format

Every report contains:
- Rules assessment table (PASS/FAIL/NOT_APPLICABLE, one-line reasoning per rule)
- Policy coverage analysis with clause references
- Overall recommendation with primary and supporting reasons
- Assessor's summary (case note quality)
- Documentation checklist (type-specific)
- Current status and next action
- Payable amount breakdown
- Confidence level with reasoning

### Critical Technical Notes for Dify

- HTTP nodes use **params not path variables** — Dify has string handling issues with path params
- Classify Intent uses structured output with enum — IF/ELSE uses exact match `== "ASSESS"`
- Rule-by-Rule node receives `policy_summary` not full `policy_data` — token limit is 272K
- Policy Document Analysis receives full `policy_data` including policy_text
- D6 and D7 receive `structured_output` objects — Dify cannot select boolean/array fields directly
- All four sub-workflows published and available as tools
- DSL YAML files saved in `dify-data/`

### Agent 2 — Document Generation Agent

Input: `claim_id`, `document_type`
1. Fetch claim + policy via MCP
2. Branch: rejection letter / approval letter / claims summary
3. Generate professional formatted document with real data
4. Output formatted document

### Agent 3 — Claims Intelligence Agent

Four branches:
- **Operational:** workload queries, status summaries by officer
- **Anomaly Detection:** suspicious patterns, early claims, amount outliers
- **Cross-Policy:** all policies for customer_id, coverage analysis
- **Analytical:** management summaries, volume reports, recommendation rate trends

### Orchestrator Chatbot

Dify Agent node. Three specialist workflows registered as tools. Routes every query to the correct agent.

---

## 10. Component 2 — MCP Server (FastAPI)

All endpoints use **query parameters** (not path parameters — Dify string handling issue).

**Start command:**
```bash
cd ~/Documents/gitlocal/sit_capstone
source venv/bin/activate
cd mcp_server
uvicorn main:app --reload --port 8000
```

### Endpoints

| Endpoint | Method | Params | Returns |
|---|---|---|---|
| `/health` | GET | none | Server status |
| `/claims` | GET | claim_id, policy_id, customer_id, status, assigned_officer, claim_type, limit | Filtered claims |
| `/policies` | GET | policy_id, customer_id, policy_type, status, limit | Filtered policies (includes policy_text) |
| `/eligibility-rules` | GET | policy_type, is_mandatory | Rules filtered by type |
| `/assessment` | GET | claim_id | Claim + linked policy + rules combined |
| `/assessment-logs` | POST | JSON body | Writes to assessment_logs, returns log_id |
| `/assessment-logs` | GET | workflow_type, recommendation, limit | Query audit log |
| `/workflow-nodes` | GET | workflow_name | Returns stored nodes for a workflow |
| `/workflow-nodes` | POST | JSON body | Stores new/updated node after approval |
| `/change-approvals` | GET | status, workflow_name | Returns pending/approved changes |
| `/change-approvals` | POST | JSON body | Creates a change approval request |
| `/change-approvals/{id}/approve` | POST | approved_by, reason | Approves and triggers git commit |
| `/change-approvals/{id}/reject` | POST | rejected_by, reason | Rejects the change |

### Environment Variables
```
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_KEY=[service_role_secret_key]
MLFLOW_TRACKING_URI=[databricks tracking URI]
GITHUB_TOKEN=[personal access token for git commits]
GITHUB_REPO=jas12481/sit_capstone
```

---

## 11. Component 3 — Database Layer (Supabase)

- **Region:** Singapore (ap-southeast-1)
- **RLS:** Enabled on all tables
- **Access:** MCP server only (secret key). Frontend never connects directly.
- **Tables:** policies, claims, claim_documents, eligibility_rules, assessment_logs, workflow_nodes, change_approvals

See Section 7 for full schema of all tables.

---

## 12. Component 4 — MLflow + Databricks

### Three Functions

1. **Prompt Registry** — version control for all system prompts across all workflow nodes
2. **Experiment Tracking** — logs every evaluation run (parameters + metrics + artifacts)
3. **Production Audit Link** — every assessment_logs entry has an `mlflow_run_id` linking it to full parameter context

### Setup

Databricks Community Edition (free). The examiner specifically mentioned Databricks — use the real platform.

### Prompt Registry Naming Convention

```
life_classify_intent_v1.0
life_rule_check_v1.0
life_policy_analysis_v1.0
life_synthesise_verdict_v1.0
life_judge_v1.0
health_rule_check_v1.0
health_policy_analysis_v1.0
health_synthesise_verdict_v1.0
health_judge_v1.0
ci_rule_check_v1.0
ci_policy_analysis_v1.0
ci_synthesise_verdict_v1.0
ci_judge_v1.0
disability_rule_check_v1.0
disability_policy_analysis_v1.0
disability_synthesise_verdict_v1.0
disability_judge_v1.0
```

When prompts are updated (via DSL Change Management), increment version. Log `prompt_version` to `assessment_logs`.

### Evaluation Experiment Parameters

```
strategy          direct | chain_of_thought | structured_output | combined
policy_type       life | health | critical_illness | disability
claim_id          test claim identifier
model_name        gpt-5.2
prompt_version    from MLflow Prompt Registry
```

### Evaluation Experiment Metrics

```
recommendation_correct          1/0 vs ground truth
hallucinated_rule_count         rule IDs not in eligibility_rules table
hallucinated_clause_count       clause refs not found in policy_text
mandatory_rules_correctly_id    1/0 correct mandatory rules flagged
valid_clause_references         count of valid clause refs
confidence_level_numeric        HIGH=1.0 MEDIUM=0.5 LOW=0.0
judge_completeness              LLM-as-Judge score 0-1
judge_consistency               LLM-as-Judge score 0-1
judge_hallucination_risk        LLM-as-Judge score 0-1
judge_clarity                   LLM-as-Judge score 0-1
judge_overall                   average of four judge scores
```

### Artifacts per Run

- Full assessment report (text file)
- Raw structured output JSON
- LLM-as-Judge evaluation JSON

---

## 13. Component 5 — LLM-as-Judge Quality Evaluation Layer

### What It Is

After every assessment (both in production and in the evaluation study), an additional LLM node reads the full assessment report and scores it on four dimensions. Scores are logged to both `assessment_logs` and MLflow.

### The Four Dimensions

**Completeness (0-1):** Did the report check every rule applicable to this claim type? Is a documentation checklist present? Is a payable amount calculation included? Is there a clear next action for the officer?

**Consistency (0-1):** Does the final recommendation align with the rule verdicts? If mandatory rules failed, is the recommendation REJECT not APPROVE? Does the confidence level match the number of failures and the coverage conclusion?

**Hallucination Risk (0-1, where 1 = no hallucination detected):** Did the report reference rule IDs that don't exist in the standard set for this policy type? Did it cite clause numbers that are implausible for this policy? Are all figures (dates, amounts) traceable to the input data?

**Clarity (0-1):** Is the assessor's summary coherent and professional? Is the language clear enough for a claims officer to use directly as a case note? Is the recommendation stated unambiguously?

### Why This Matters

- Provides automated quality assurance on every assessment without manual review
- Produces quantitative quality metrics trackable over time in MLflow
- The Hallucination Risk dimension gives a scalable per-run hallucination signal
- Combined with the manual evaluation study, creates two layers of hallucination measurement: automated (LLM-as-Judge) and empirical (ground truth comparison)
- Directly implements MAS AIRG "capabilities and capacity" — the system can demonstrate its own quality

### Dify Implementation

A new LLM node added after Format Final Report in each sub-workflow:

**Name:** `llm_judge`
**Model:** GPT-5.2
**Structured Output:** ON

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
    "flagged_issues": {
      "type": "array",
      "items": {"type": "string"}
    }
  },
  "required": ["completeness_score", "consistency_score", "hallucination_risk_score", "clarity_score", "overall_score", "flagged_issues"]
}
```

**System Prompt:** You are a quality assurance evaluator for an AI insurance claims assessment system. You evaluate assessment reports on four dimensions: completeness, consistency, hallucination risk, and clarity. You are strict and objective. You do not give scores above 0.8 unless the report is genuinely excellent in that dimension.

**User Prompt:** Evaluate the following assessment report. The claim type is {{claim_type}}. The applicable eligibility rules for this type are: {{eligibility_rules}}. The policy type is {{policy_type}}.

ASSESSMENT REPORT TO EVALUATE:
{{format_final_report.text}}

Score each dimension from 0.0 to 1.0 and identify any specific issues flagged.

---

## 14. Component 6 — DSL Change Management System

### What It Is

A governed version control system for Dify workflow configurations. When a workflow DSL (YAML) is exported from Dify, the system parses it, extracts all executable nodes (LLM, code, agent), compares against what is stored, highlights any changes, and requires a named person to sign off before the change is committed to the database and GitHub.

### Why It Matters

This implements the MAS AIRG requirement for AI lifecycle controls in the most direct way possible. In a production insurance environment, a change to an eligibility assessment prompt is equivalent to a change to underwriting rules — it must be controlled, attributed, and auditable. The DSL Change Management System makes this concrete.

No other student capstone project is building this. It is the most original component of the entire system.

### The Full Flow

```
1. Developer exports DSL from Dify → saves YAML to dify-data/ folder
2. Run: python dsl_manager/parser.py --file dify-data/Life_Claims_Assessment.yml
3. Parser extracts all LLM nodes, code nodes, agent nodes
4. For each node: compute SHA256 hash of node content
5. Compare hash against stored hash in workflow_nodes table
6. If hash matches → no change, skip
7. If hash differs → show diff (before vs after prompt/code text)
8. Create entry in change_approvals table with status=pending
9. Frontend DSL Management view shows pending change with full diff
10. Approver reviews diff, enters their name and change reason, clicks Approve/Reject
11. If Approved:
    - Update workflow_nodes table with new content + hash
    - Increment prompt_version in MLflow Prompt Registry
    - Commit to GitHub via API with message: "APPROVED by [name]: [reason]"
    - Store git_commit_hash in change_approvals record
    - Update assessment_logs going forward to reference new prompt_version
12. If Rejected:
    - Log rejection with reason
    - No changes committed
    - Developer must revert DSL to previous state
```

### `dsl_manager/parser.py`

Reads a Dify YAML DSL and extracts:
- All `type: llm` nodes → extracts prompt_template system and user text
- All `type: code` nodes → extracts code content
- All `type: tool` nodes → extracts tool configuration

Output: list of `{workflow_name, node_type, node_name, node_content, content_hash}` objects

### `dsl_manager/diff.py`

Given a new node content and stored node content, produces a human-readable diff showing exactly what changed — which lines were added, removed, or modified in the prompt or code.

### `dsl_manager/approvals.py`

Handles the approval workflow:
- `create_approval(node_id, changed_by, diff_content)` → writes to change_approvals with status=pending
- `approve_change(approval_id, approved_by, reason)` → updates status, triggers git commit
- `reject_change(approval_id, rejected_by, reason)` → updates status, logs rejection

### `dsl_manager/git_commit.py`

Uses GitHub API to commit the approved DSL file:
- Commit message format: `[APPROVED] {workflow_name} — {node_name}: {change_reason} | Approved by: {approved_by}`
- Stores returned commit SHA in change_approvals record

### Frontend — DSL Management View

A dedicated view in the React frontend:
- Lists all workflows with their current version and last commit date
- Shows pending changes awaiting approval with full diff view
- Approval form: approver name + change reason (both mandatory)
- Approval history: all past changes with approver, reason, timestamp, Git commit link

### Audit Trail Chain

Every assessment_logs entry has a `prompt_version` field. Every prompt_version is tied to a change_approvals record. Every change_approvals record has a `git_commit_hash`. This creates a complete chain:

```
Assessment decision → prompt_version → approval record → git commit → exact prompt text used
```

An auditor can take any assessment decision and trace it all the way back to the exact prompt that produced it, who approved that prompt, when, and why.

---

## 15. Component 7 — Frontend (React + Vercel)

### Four Views

**1. Chat Interface**
- Natural language query input
- Message history
- Agent routing visibility panel (which specialist workflow ran)
- Loading state for long-running assessments (30-60 seconds typical)

**2. Audit Log View** *(serves compliance and audit stakeholders)*
- Table of assessment_logs records from MCP `/assessment-logs` GET
- Filters: date range, workflow type, recommendation, confidence level, judge score threshold
- Expandable rows: full assessment details + LLM-as-Judge scores per dimension
- Link to MLflow run for complete parameter context

**3. Management Dashboard** *(serves business stakeholders)*
- Claims volume by type (this month / last 30 days)
- Recommendation distribution chart (APPROVE/REJECT/REFER %)
- Average LLM-as-Judge overall score trend over time
- Average confidence level by workflow type
- Flagged anomalies from Claims Intelligence Agent
- Workload by assigned officer

**4. DSL Change Management View** *(serves IT governance)*
- All workflows with current version and last commit
- Pending changes awaiting approval (with diff)
- Approval form (name + reason, both mandatory)
- Full approval history with Git commit links

---

## 16. Evaluation Study Design

### Objective

Empirically compare four prompting strategies for LLM-based insurance claims assessment. Produce domain-specific findings on hallucination mitigation. The combined strategy (current system design) is expected to outperform all others — this validates the design choices.

### The Four Strategies

| Strategy | Description |
|---|---|
| **Direct** | "Assess this claim and give a recommendation" — no structure, no reasoning steps |
| **Chain-of-Thought** | "Check each rule in order, show your working with exact values from the data" |
| **Structured Output** | JSON schema with enum constraints, no explicit reasoning instructions |
| **Combined (current)** | Chain-of-thought + structured output + grounding ("only use provided context, cite specific clauses") |

### Test Set — 20 Claims (5 per type)

| # | Scenario | Expected Recommendation |
|---|---|---|
| 1 | Clear APPROVE — all rules pass, active policy | APPROVE |
| 2 | Clear REJECT — policy lapsed (mandatory rule fail) | REJECT |
| 3 | REFER — rules pass, documentation missing | REFER |
| 4 | Edge case — claim just after waiting period, amount at sum assured limit | Context-dependent |
| 5 | Validation test — wrong claim type for this workflow | REJECT or error |

(Repeated for each of the four policy types = 20 total)

### Ground Truth per Claim

- Expected recommendation
- Expected rules that should FAIL
- Expected clause references that should appear in the report
- Known hallucination traps (non-existent rule IDs, implausible clause numbers)

### Metrics

| Metric | Definition |
|---|---|
| `recommendation_correct` | 1 if matches ground truth |
| `hallucinated_rule_count` | Rule IDs in output not in eligibility_rules table |
| `hallucinated_clause_count` | Clause refs not found in policy_text |
| `mandatory_rules_correctly_identified` | 1 if correct mandatory rules flagged |
| `valid_clause_references` | Count of clause refs that exist in policy_text |
| `confidence_level_numeric` | HIGH=1.0, MEDIUM=0.5, LOW=0.0 |
| `judge_overall` | LLM-as-Judge overall score for this run |

### MLflow Experiment Structure

```
Experiment: "Claims Assessment Prompting Study"
├── Run: direct_life_CLM-XXXX
├── Run: cot_life_CLM-XXXX
├── Run: structured_life_CLM-XXXX
├── Run: combined_life_CLM-XXXX
└── ... (80 runs total: 4 strategies × 20 claims)
```

### Expected Findings

- Direct: highest hallucination, lowest accuracy, lowest judge scores
- CoT alone: improved accuracy, free-form hallucinations persist
- Structured output alone: low hallucination but misses nuance on edge cases
- Combined: lowest hallucination, highest accuracy, highest judge scores — validates design

---

## 17. Governance Framework (The Reusable Contribution)

### Title

"A Technical Governance Framework for Agentic AI in Regulated Financial Services"

### Five Governance Layers

```
Layer 1: Data Access Governance (MCP Server)
  → No direct DB access from agents; governed, auditable API layer
  → Maps to: MAS AIRG "key AI risk management systems"
  → IMDA: Internal Governance

Layer 2: Output Governance (Structured Schemas)
  → JSON schema + enum constraints on all inter-node outputs
  → Prevents hallucinated recommendations
  → Maps to: IMDA "Operations Management — Robustness"

Layer 3: Prompt Governance (MLflow Prompt Registry)
  → Every system prompt versioned; changes tracked with prompt_version in audit log
  → Maps to: MAS AIRG "AI lifecycle controls"

Layer 4: Decision Governance (Audit Log + LLM-as-Judge)
  → Every assessment logged with model version, prompt version, judge scores
  → Automated quality assurance on every output
  → Maps to: IMDA "Operations Management — Auditability"
            MAS AIRG "oversight of AI risk management"

Layer 5: Change Governance (DSL Change Management System)
  → Every modification to AI workflow logic requires sign-off
  → Diffs stored, approvals attributed, commits traceable
  → Maps to: MAS AIRG "AI lifecycle controls — change management"
            IMDA "Internal Governance — accountability"
```

### What Makes This Reusable

Any financial institution deploying agentic AI can apply these five layers regardless of their orchestration platform. The framework is technology-agnostic. Another organisation could implement it with LangChain, LlamaIndex, or any future platform. This is the academic contribution beyond the specific AIA implementation.

---

## 18. Stakeholder Map

| Stakeholder | How System Serves Them |
|---|---|
| **Claims Officer** | Chat interface; assessment reports with clause refs, documentation checklists, next action |
| **Claims Manager** | Management dashboard — volume, recommendation rates, quality trends, workload |
| **Compliance Officer** | Audit log — every decision traceable to rules, clauses, model version, prompt version |
| **Internal Auditor** | assessment_logs + change_approvals + MLflow links — complete decision and change history |
| **IT / AI Engineer** | MLflow tracking + DSL Change Management — prompt versions, model performance, change control |
| **Business Team (Kenix)** | Claims Intelligence Agent analytical summaries feed into business process redesign |

---

## 19. Build Status

| Component | Status | Notes |
|---|---|---|
| Supabase schema (4 core tables) | ✅ Done | RLS enabled |
| Synthetic data | ✅ Done | 1,000 policies, 1,522 claims, 24 rules |
| Policy PDFs | ✅ Done | 1,000 PDFs in Supabase Storage |
| MCP server (core 5 endpoints) | ✅ Done | /claims, /policies, /eligibility-rules, /assessment, /health |
| Life Claims Assessment | ✅ Done | Tested, published in Dify |
| Health Claims Assessment | ✅ Done | Tested, published in Dify |
| Critical Illness Assessment | ✅ Done | Tested, published in Dify |
| Disability Assessment | ✅ Done | Tested, published in Dify |
| assessment_logs table | 🔲 To build | Add 5 judge score columns |
| workflow_nodes table | 🔲 To build | |
| change_approvals table | 🔲 To build | |
| MCP /assessment-logs endpoints | 🔲 To build | POST + GET |
| MCP /workflow-nodes endpoints | 🔲 To build | GET + POST |
| MCP /change-approvals endpoints | 🔲 To build | GET + POST + approve/reject |
| MLflow on Databricks | 🔲 To build | Community Edition |
| MLflow Prompt Registry | 🔲 To build | Register all prompts as v1.0 |
| LLM-as-Judge node (all 4 workflows) | 🔲 To build | Add after Format Final Report |
| Evaluation script | 🔲 To build | 80 MLflow runs |
| dsl_manager/parser.py | 🔲 To build | Parse Dify YAML |
| dsl_manager/diff.py | 🔲 To build | Human-readable diffs |
| dsl_manager/approvals.py | 🔲 To build | Sign-off workflow |
| dsl_manager/git_commit.py | 🔲 To build | GitHub API commits |
| Claims Assessment routing workflow | 🔲 To build | Routes to 4 sub-workflows |
| Document Generation Agent | 🔲 To build | |
| Claims Intelligence Agent | 🔲 To build | 4 branches |
| Orchestrator Chatbot | 🔲 To build | Dify Agent node |
| Frontend — Chat view | 🔲 To build | |
| Frontend — Audit log view | 🔲 To build | |
| Frontend — Management dashboard | 🔲 To build | |
| Frontend — DSL Management view | 🔲 To build | |
| UAT + SUS | 🔲 June 2026 | AIA Technology team, target SUS > 68 |
| Final report | 🔲 July 2026 | |

---

## 20. Timeline

| Period | Target |
|---|---|
| **Week 1 (Now)** | assessment_logs + workflow_nodes + change_approvals tables; MCP endpoints for all three; MLflow on Databricks; register all current prompts as v1.0 |
| **Week 2** | LLM-as-Judge nodes added to all 4 sub-workflows; dsl_manager parser + diff + approvals + git_commit; evaluation test claims defined |
| **Week 3** | Run evaluation study (80 MLflow runs); Claims Assessment routing workflow; Document Generation Agent |
| **Week 4 (End May)** | Claims Intelligence Agent; Orchestrator; frontend scaffold + all 4 views |
| **June 1-15** | End-to-end testing; regression tests; frontend polish; DSL Management UI testing |
| **June 16-30** | UAT with AIA Technology team; SUS questionnaire; evaluation analysis |
| **July 1-19** | Final report — all chapters |

---

## 21. Final Report Structure

1. Introduction
2. Literature Review: AI in insurance; LLMs and agentic AI; LLM hallucination; platform selection; LLMOps + MLflow; LLM-as-Judge; AI governance (IMDA + MAS AIRG); Model Context Protocol; AI change management in regulated systems
3. System Architecture — five governance layers, design decisions
4. Regulatory Alignment — IMDA and MAS AIRG mapping tables
5. Implementation — all workflows, MCP server, MLflow, LLM-as-Judge, DSL system
6. Evaluation Study — methodology, 4 strategies × 20 claims, results, hallucination analysis
7. UAT and SUS Results
8. Governance Framework — five-layer reusable framework
9. Discussion — findings, limitations, future work
10. Conclusion

**Central argument:** The combined prompting strategy (chain-of-thought + structured output + grounding) produces the lowest hallucination rate and highest quality scores across all four insurance claim types. The five-layer governance framework provides a reusable reference implementation of the IMDA Model Framework and MAS AIRG Guidelines for agentic AI in regulated financial services.

**Citation format:** IEEE

---

*Last updated: May 2026. Any AI assistant or developer picking up this project must read this document in full before making any changes to the codebase, Dify configuration, MLflow experiments, or DSL files.*

Here's a summary of every component in the updated project:

Component 1 — Multi-Agent Assessment System (Dify)
Four complete sub-workflows (Life, Health, CI, Disability) + Claims Assessment routing workflow + Document Generation Agent + Claims Intelligence Agent + Orchestrator Chatbot. Each assessment sub-workflow now includes a LLM-as-Judge node at the end.
Component 2 — MCP Server (FastAPI)
Five existing endpoints plus six new ones: /assessment-logs (POST/GET), /workflow-nodes (GET/POST), /change-approvals (GET/POST/approve/reject).
Component 3 — Database Layer (Supabase)
Four existing tables plus three new ones: assessment_logs (now with five judge score columns), workflow_nodes, change_approvals.
Component 4 — MLflow + Databricks
Prompt Registry with 17 named prompts, experiment tracking for 80 evaluation runs, production audit linking via mlflow_run_id in assessment_logs.
Component 5 — LLM-as-Judge
A new LLM node in every sub-workflow scoring each assessment on completeness, consistency, hallucination risk, and clarity. Scores logged to both assessment_logs and MLflow.
Component 6 — DSL Change Management System
Four Python modules (parser, diff, approvals, git_commit) plus a dedicated frontend view. Parses Dify YAML, detects changes, requires named sign-off, commits to GitHub with attribution.
Component 7 — Frontend (React + Vercel)
Four views: Chat Interface, Audit Log, Management Dashboard, DSL Change Management.