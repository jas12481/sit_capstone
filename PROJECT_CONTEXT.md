# AIA Capstone Project — Full Context Document
> **For:** Claude Code and any AI assistant picking up this project  
> **Author:** Jasbir Kaur (2302990), Applied Computing (FinTech), Singapore Institute of Technology  
> **Last updated:** May 2026

---

## 1. Project Identity

| Field | Detail |
|---|---|
| **Project Title** | AI Workflow Automation and Agent Development for Insurance Claims Operations |
| **Module** | BAC3004 Capstone Project, Singapore Institute of Technology (SIT) |
| **Student** | Jasbir Kaur, Matriculation No. 2302990 |
| **Programme** | Applied Computing (FinTech) |
| **Organisation** | AIA Singapore Pte. Ltd. |
| **Project Period** | 5 January 2026 – 7 August 2026 |
| **Report Deadline** | 19 July 2026 |
| **Build Completion Target** | End of May 2026 |
| **Testing / UAT Target** | All of June 2026 |
| **Industry Supervisor** | Kartik-K Mahadevan, Associate Director AI & Machine Learning, Technology – Data Architecture Development |
| **Academic Supervisor** | Assoc. Prof. Harminder Singh, SIT |
| **GitHub Repo** | `https://github.com/jas12481/sit_capstone` (public) |

---

## 2. What This Project Is

A **multi-agent AI chatbot system** for AIA Singapore's claims operations department. Claims officers interact with a custom web UI, submit natural language queries about claims and policies, and the system orchestrates specialised AI agents to retrieve data, reason over it, and produce structured, explainable outputs.

The system is modelled directly on a real internal AIA initiative. Because live AIA data cannot be used for academic purposes, the capstone uses a **synthetic dataset** that mirrors real data structure without exposing proprietary information.

### Why This Matters

Insurance claims processing is documentation-heavy, requires cross-referencing multiple data sources, and demands consistency across high claim volumes. Generative AI in this context must be:
- **Governed** — outputs must be traceable and auditable
- **Explainable** — business teams need to understand what AI is doing
- **Consistent** — not produce wildly varying outputs on the same input

This is why the system is built on **Dify** (a managed enterprise LLM orchestration platform) rather than code-first frameworks like LangChain or LlamaIndex.

### Project Evolution

The original proposal described two parts: (1) an automated claim rejection workflow and (2) a policy lookup chatbot. The scope evolved into a single unified chatbot orchestrating multiple specialised Dify workflow agents. This better reflects the real AIA system architecture and is a stronger academic contribution.

---

## 3. Core Design Principles

These are non-negotiable architectural decisions that must be respected throughout the build:

1. **Agents must justify their existence through reasoning, not data retrieval.** A simple database query does not justify an agentic architecture. Every agent must do something a database cannot — reasoning, synthesis, or judgement.

2. **LLM reasoning over unstructured text is a deliberate choice.** The schema is intentionally lean. Rich unstructured content lives in the policy PDF and extracted `policy_text`. The LLM reads this to handle product-level differences rather than hardcoding logic into structured fields. This is a defensible architectural decision documented in the final report.

3. **Security and explainability drove platform selection.** Dify was chosen over LangChain and LlamaIndex because: (a) its security is managed at the platform level with no sprawling dependency chain to audit, and (b) its visual workflow builder is readable by non-technical business stakeholders. This is critical in a regulated insurance environment.

4. **Data never leaves the controlled environment.** Dify runs as a self-hosted Docker container, not on Dify's cloud. This means no claim or policy data passes through third-party servers — essential for a regulated financial services context.

5. **The MCP server is the only data access point.** Dify agents do not query Supabase directly. They call the MCP server's endpoints, which return structured JSON. This creates a clean, auditable, governable data access layer.

---

## 4. Tech Stack

| Component | Technology | Notes |
|---|---|---|
| **LLM Orchestration** | Dify (self-hosted Docker container) | 6 CPU, 8GB RAM allocated. Running at `http://localhost`. GPT-5.2 (OpenAI) as default LLM |
| **Database** | Supabase (Singapore region, `ap-southeast-1`) | PostgreSQL with RLS enabled on all tables. Free tier |
| **Storage** | Supabase Storage (`policy-documents` bucket, public) | Stores 1000 policy PDFs |
| **Middleware / MCP Server** | Python FastAPI | Custom MCP server. Lives in `mcp_server/` folder. Uses Supabase secret key to bypass RLS |
| **Frontend** | Custom web UI | Lives in `frontend/` folder. Deployed on Vercel. Calls Dify agents via REST API |
| **PDF Generation** | ReportLab (Python) | Used to generate 1000 legal contract policy PDFs |
| **Version Control** | GitHub (`sit_capstone`, public repo) | Connected to Vercel for auto-deploy |
| **Editor** | Cursor | Primary development environment |
| **Terminal** | Warp | |
| **LLM Provider** | OpenAI (GPT-5.2) | $100 credit balance. GPT-5.2 used for orchestrator and eligibility agent. Simpler agents can use GPT-4o to save cost |

### Local Development URLs
- Dify: `http://localhost`
- MCP Server: `http://localhost:8000`
- Dify can reach MCP server at `http://host.docker.internal:8000` from inside Docker

### Folder Structure
```
sit_capstone/
├── mcp_server/          # FastAPI MCP server
│   ├── main.py          # Server entry point
│   └── .env             # SUPABASE_URL and SUPABASE_KEY
├── frontend/            # Web UI (React or Next.js)
├── dify-data/           # Dify config exports and workflow definitions
├── generate_data.py     # Synthetic data generation script
├── generate_pdfs.py     # PDF generation and upload script
├── .gitignore
└── README.md
```

---

## 5. Database Schema (Supabase)

All tables have **Row Level Security (RLS) enabled**. The MCP server uses the **secret key** to bypass RLS. The frontend never connects to Supabase directly.

### `policies`

| Column | Type | Notes |
|---|---|---|
| `policy_id` | TEXT (PK) | e.g. `POL-LI-0001`, `POL-HE-0042` |
| `customer_id` | TEXT | e.g. `CUST-0001`. Loose reference only — no customers table |
| `agent_id` | TEXT | e.g. `AGT-007`. Financial adviser who sold the policy |
| `policy_type` | TEXT | `life`, `health`, `critical_illness`, `disability` |
| `policy_name` | TEXT | One of 60 fictional product names |
| `policyholder_name` | TEXT | Real Singapore name e.g. "Tan Wei Ming" |
| `sum_assured` | NUMERIC | Coverage amount in SGD |
| `premium_amount` | NUMERIC | Monthly/quarterly/annual premium in SGD |
| `premium_frequency` | TEXT | `monthly`, `quarterly`, `annual` |
| `start_date` | DATE | Policy commencement date |
| `end_date` | DATE | Policy expiry date |
| `status` | TEXT | `active`, `lapsed`, `terminated` |
| `pdf_url` | TEXT | Supabase Storage public URL to policy PDF |
| `policy_text` | TEXT | Full extracted text from the PDF (~17,000 chars) |
| `policy_summary` | TEXT | 200-300 word structured summary for fast agent use |
| `created_at` | TIMESTAMP | |

### `claims`

| Column | Type | Notes |
|---|---|---|
| `claim_id` | TEXT (PK) | e.g. `CLM-0001` |
| `policy_id` | TEXT (FK → policies) | |
| `customer_id` | TEXT | Denormalised from policy for faster lookup |
| `claim_type` | TEXT | Matches policy_type: `life`, `health`, `critical_illness`, `disability` |
| `claim_category` | TEXT | More granular — see categories below |
| `claim_date` | DATE | Date claim was submitted |
| `incident_date` | DATE | Date of the event or diagnosis |
| `claim_amount` | NUMERIC | Amount claimed in SGD |
| `approved_amount` | NUMERIC | Amount approved (null if not yet approved) |
| `payment_date` | DATE | Date payment was made (null if not paid) |
| `status` | TEXT | `pending`, `approved`, `rejected`, `under_review` |
| `rejection_reason` | TEXT | Null unless rejected |
| `assigned_officer` | TEXT | Claims officer name |
| `notes` | TEXT | Free text notes |
| `created_at` | TIMESTAMP | |

**Claim categories by type:**
- `life`: `death`, `accidental_death`, `total_permanent_disability`
- `health`: `hospitalisation`, `surgical`, `outpatient`, `emergency`
- `critical_illness`: `cancer`, `heart_attack`, `stroke`, `kidney_failure`, `major_organ_transplant`
- `disability`: `total_temporary_disability`, `total_permanent_disability`, `partial_permanent_disability`, `occupational_disability`

### `claim_documents`

| Column | Type | Notes |
|---|---|---|
| `document_id` | UUID (PK) | |
| `claim_id` | TEXT (FK → claims) | |
| `document_type` | TEXT | e.g. "Medical Report", "Death Certificate" |
| `document_name` | TEXT | Filename |
| `pdf_url` | TEXT | Supabase Storage URL |
| `uploaded_at` | TIMESTAMP | |

### `eligibility_rules`

| Column | Type | Notes |
|---|---|---|
| `rule_id` | TEXT (PK) | e.g. `RULE-LI-001`, `RULE-HE-006` |
| `policy_type` | TEXT | `life`, `health`, `critical_illness`, `disability` |
| `rule_name` | TEXT | e.g. "Waiting Period" |
| `rule_description` | TEXT | Human-readable explanation |
| `condition` | TEXT | Checkable condition e.g. "Claim date must be 90+ days after policy start date" |
| `is_mandatory` | BOOLEAN | If true, failure = hard rejection |

**24 rules total** — 5 life, 6 health, 6 critical illness, 7 disability.

### Why No Customers Table

In real enterprise insurance systems, customer data lives in a separate CRM system decoupled from the claims system. The `customer_id` field on policies is a loose reference to that external system. The personal details a claims officer needs are embedded in the policy PDF and `policy_text`. This is a deliberate architectural decision that reflects real enterprise data separation — not a shortcut.

---

## 6. Synthetic Data

### Scale
- **1,000 policies** across 60 fictional products (15 per type)
- **1,522 claims** with realistic type-specific frequency distributions
- **1,000 policy PDFs** in Supabase Storage (~23KB each, ~23MB total)
- **24 eligibility rules** across 4 policy types

### Claim Frequency Justification (from real Singapore sources)
Claim frequencies are based on MOH Singapore and LIA Singapore statistics:
- **Health**: avg 4.0 claims/policy (MOH IP holder data; policies span up to 35 years)
- **Disability**: avg 1.0 claim/policy (LIA 2023 claims data; temporary disability can recur)
- **Critical illness**: avg 0.5 claims/policy (1 in 4 Singaporeans develop CI; LIA data)
- **Life**: avg 0.3 claims/policy (death/TPD are rare lifetime events)

### The 60 Products

**Life (15):** AIA LifeGuard Essential, AIA LifeGuard Plus, AIA LifeGuard Premier, AIA SecureLife 300, AIA SecureLife 600, AIA SecureLife Platinum, AIA WholeCover Basic, AIA WholeCover Premier, AIA FamilyShield Income, AIA MortgageGuard, AIA SeniorGuard 65, AIA BusinessGuard Term, AIA EndowSave 20, AIA EndowSave 25, AIA ConvertTerm Plus

**Health (15):** AIA MediShield Basic, AIA MediShield Standard, AIA MediShield Gold, AIA MediShield Gold Max, AIA MediShield Platinum, AIA HealthPlus Essential, AIA HealthPlus Comprehensive, AIA HealthPlus Premier, AIA CareShield Basic, AIA CareShield Family, AIA CancerCare Protect, AIA MaternaCare, AIA SeniorCare Shield, AIA GlobalCare Elite, AIA WellnessPlus Rider

**Critical Illness (15):** AIA CI Essential 5, AIA CI Protect 10, AIA CI Protect 36, AIA CI Protect 53, AIA CI MultiClaim, AIA EarlyCI Basic, AIA EarlyCI Premier, AIA CancerGuard Plus, AIA HeartGuard Plus, AIA CI Monthly Income, AIA CI Protect 360, AIA SeniorCI Cover, AIA CI FamilyCare, AIA CI BusinessGuard, AIA DreadDisease Premier

**Disability (15):** AIA DisabilityGuard Basic, AIA DisabilityGuard Plus, AIA DisabilityGuard Premier, AIA IncomeShield Basic, AIA IncomeShield Plus, AIA IncomeShield Premier, AIA TotalCover Disability, AIA OccupationProtect, AIA ExecutiveDisability, AIA FreelanceShield, AIA AccidentDisability, AIA RehabPlus Disability, AIA PartialDisability Cover, AIA SeniorDisability Shield, AIA GroupDisability SME

### Policy PDFs
Each PDF is a full legal contract style document (~11 pages, black and white professional layout) containing:
- Page 1: Policy schedule with real data from the database row
- Page 2: Definitions (14-16 terms, meaningfully different per policy type)
- Page 3: Benefit provisions (6-7 clauses, type-specific)
- Page 4: Exclusions (8-12, type-specific)
- Page 5: Premium provisions
- Page 6: Claims provisions (type-specific documentation requirements)
- Page 7: General provisions
- Page 8: Assignment, nomination, policy servicing
- Page 9: Regulatory notices (MAS, SDIC, PDPA)
- Page 10: Schedule of benefits table + execution/signature page

Company branding uses fictional details: "AIA Singapore Pte. Ltd.", Reg. No. 202600001Z, MAS Licence No. LI-SIM-2026-001, www.aia-s.com.sg — to avoid trademark issues while keeping AIA as the company name (supervisors are aware).

---

## 7. Agent Architecture

### Overview

```
User (Web UI)
    ↓ natural language query
Orchestrator Chatbot (Dify Agent)
    ↓ routes to specialist agent
    ├── Claims Assessment Agent (Dify Workflow — main)
    │       ├── Life Claims Assessment (Dify Workflow — sub)
    │       ├── Health Claims Assessment (Dify Workflow — sub)
    │       ├── Critical Illness Assessment (Dify Workflow — sub)
    │       └── Disability Assessment (Dify Workflow — sub)
    ├── Document Generation Agent (Dify Workflow)
    └── Claims Intelligence Agent (Dify Workflow)
        ↓ each agent calls
MCP Server (FastAPI)
        ↓ queries
Supabase (PostgreSQL + Storage)
```

**Total Dify workflows to build: 8**
1. Life Claims Assessment (sub-workflow)
2. Health Claims Assessment (sub-workflow)
3. Critical Illness Assessment (sub-workflow)
4. Disability Assessment (sub-workflow)
5. Claims Assessment Agent (main routing workflow)
6. Document Generation Agent
7. Claims Intelligence Agent
8. Orchestrator Chatbot (Agent node, not a workflow)

### Agent 1 — Claims Assessment Agent (Flagship)

**Purpose:** Given a claim ID, perform a full multi-step eligibility assessment with rule-by-rule reasoning and a structured verdict. This is the most complex agent and the core demonstration of AI value in the system.

**Why this requires an agent:** A database query can return claim data. It cannot check whether the claim date is more than 90 days after the policy start date, read the policy_text to verify the specific condition is covered, cross-reference that against each eligibility rule, and produce an explainable decision with reasoning for each rule. That requires LLM reasoning.

**Architecture — Separate sub-workflows per type, composed into a main routing workflow:**

The Claims Assessment layer is built as **5 separate Dify workflows**:

```
Claims Assessment Agent (main workflow)
    ├── calls → Life Claims Assessment (sub-workflow)
    ├── calls → Health Claims Assessment (sub-workflow)
    ├── calls → Critical Illness Assessment (sub-workflow)
    └── calls → Disability Assessment (sub-workflow)
```

Each type-specific sub-workflow is published as a tool and called by the main workflow after identifying the policy type. This means:
- Each sub-workflow can be independently tested and iterated
- If one type's logic changes, only that workflow is touched
- Each workflow has a single clear responsibility (easier to explain in the report)
- Mirrors how real enterprise claims systems separate processes by insurance type

**Main Claims Assessment Agent workflow:**
1. **Input** — receives `claim_id` from orchestrator
2. **Fetch Claim** — MCP call → returns claim record including `claim_type`
3. **Route by claim_type** — IF/ELSE branch node routes to the correct sub-workflow tool
4. **Call type-specific sub-workflow** — passes `claim_id` to the appropriate sub-workflow
5. **Output** — returns structured assessment from sub-workflow to orchestrator

**Each type-specific sub-workflow (Life / Health / Critical Illness / Disability):**
1. **Input** — receives `claim_id`
2. **Fetch Claim** — MCP call → full claim record
3. **Fetch Policy** — MCP call using `policy_id` → full policy including `policy_text` and `policy_summary`
4. **Fetch Eligibility Rules** — MCP call using `claim_type` → all rules for this policy type
5. **Rule-by-rule assessment (LLM)** — checks each mandatory rule against actual claim+policy data. PASS/FAIL per rule with reasoning
6. **Policy document analysis (LLM)** — reads `policy_text` for product-specific coverage terms and exclusions relevant to this `claim_category`
7. **Synthesise verdict (LLM)** — combines rule verdicts + policy analysis into structured output
8. **Output** — returns to main workflow:
   ```
   - Per rule: PASS / FAIL / WARNING + reasoning
   - Policy coverage: COVERED / NOT COVERED / UNCLEAR + reasoning
   - Overall: APPROVE / REJECT / REFER
   - Plain English summary for claims officer
   ```

**Key design decision:** Product-level differences (e.g. AIA CI MultiClaim allows multiple claims; AIA MortgageGuard has a decreasing sum assured) are handled by the LLM reading `policy_text` — not by 60 separate hardcoded workflows. This is why rich policy documents were generated.

**Build order for this agent:** Life → Health → Critical Illness → Disability → Main routing workflow.

### Agent 2 — Document Generation Agent

**Purpose:** Given a claim ID and a document type, generate a professional formatted document using real claim and policy data. Mirrors the original proposal objective of "generating outputs based on predefined formats."

**Document types:**
- Rejection letter (formal letter to policyholder explaining rejection with policy clause references)
- Approval letter (formal notification of claim approval with payment details)
- Claims summary report (management-style summary for internal use)

**Workflow:**
1. **Input** — receives `claim_id` + `document_type`
2. **Fetch claim + policy** — MCP call → returns everything needed
3. **Determine template** — based on `document_type` and claim `status`
4. **Generate document (LLM)** — fills template with real data, produces professional output
5. **Output** — formatted document text returned to orchestrator

**Why this is straightforward:** The LLM is doing template filling with real data, not complex multi-step reasoning. The complexity is in prompt engineering to ensure professional tone and correct clause references.

### Agent 3 — Claims Intelligence Agent

**Purpose:** Answer complex analytical questions that require synthesis across multiple records — things a single database query cannot answer.

**Multi-branch structure:**
- **Branch A — Operational queries:** "Show all pending claims for officer Sarah Tan", "How many claims are under review this week?" → fetch + aggregate + summarise
- **Branch B — Anomaly detection:** "Flag any unusual claims" → fetch batch of claims, compare dates/amounts against policy terms, surface suspicious patterns (claim submitted day after policy inception, claim amount suspiciously close to sum assured, etc.)
- **Branch C — Cross-policy analysis:** "Does this customer have any other policies that could cover this claim?" → fetch all policies for `customer_id`, read each `policy_summary`, reason about coverage
- **Branch D — Analytical summaries:** "Give me a summary of this month's claims activity" → fetch recent claims, aggregate by status/type/officer, produce management summary

**Routing:** The agent must first decide which branch the query falls into — that routing decision is itself a reasoning step.

### Orchestrator — Central Chatbot

**Purpose:** The only agent the web UI talks to. Receives every natural language query, classifies it, routes to the right specialist agent, and returns a conversational response.

**Routing logic:**
- Contains an eligibility/assessment question → Claims Assessment Agent
- Asks to generate a letter or document → Document Generation Agent
- Asks about patterns, summaries, workloads, anomalies → Claims Intelligence Agent
- Complex query spanning multiple types → calls multiple agents sequentially

**Built as:** A Dify Agent node (not a workflow) with the three specialist agents registered as tools.

---

## 8. MCP Server

### What It Is

A Python FastAPI server that acts as the data access layer between Dify agents and Supabase. Dify agents call HTTP endpoints; the MCP server queries Supabase and returns structured JSON.

### Why Separate From Supabase

Direct database access from Dify would be ungoverned and hard to audit. The MCP server exposes only specific, well-defined endpoints — the agent gets exactly the data it needs, nothing more. This is the MCP pattern as defined by Anthropic's Model Context Protocol standard.

### Connection in Docker

Dify runs as a Docker container. The MCP server runs as a separate process on the host machine. Dify reaches the MCP server at `http://host.docker.internal:8000`. In future, the MCP server can be added to the `docker-compose.yml` to run as a container alongside Dify.

### Planned Endpoints (to be built)

| Endpoint | Used By | Returns |
|---|---|---|
| `GET /health` | All | Server status |
| `GET /claims/{claim_id}` | Assessment, Document Gen | Single claim record |
| `GET /claims` | Intelligence | Filtered claims (by status, officer, policy_id, customer_id, date range) |
| `GET /policies/{policy_id}` | Assessment, Document Gen | Full policy record including policy_text |
| `GET /policies` | Intelligence | Filtered policies (by customer_id, policy_type) |
| `GET /eligibility-rules/{policy_type}` | Assessment | All rules for a policy type |
| `GET /assessment/{claim_id}` | Assessment | Claim + linked policy + rules in one call |

### Environment Variables (in `mcp_server/.env`)
```
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_KEY=[service_role_secret_key]
```

---

## 9. Frontend (Web UI)

### What It Is

A custom web interface separate from Dify's built-in chat UI. Users submit queries here; the frontend calls Dify's orchestrator agent via REST API and displays responses.

### Key Features to Build
- Chat window with message history
- Dify API integration (`/v1/chat-messages` endpoint)
- Agent routing visibility panel — shows which specialist agent handled each response (important for demonstrating multi-agent architecture during UAT and to the examiner)

### Deployment
Deployed on Vercel, connected to the `sit_capstone` GitHub repo for auto-deploy. Environment variables (Dify API URL and key) set in Vercel dashboard.

---

## 10. Build Order

This is the correct sequence. Do not deviate:

1. ✅ **Database + Schema** — Done (Supabase tables, RLS enabled)
2. ✅ **Synthetic Data** — Done (1000 policies, 1522 claims, 24 eligibility rules)
3. ✅ **Policy PDFs** — Done (1000 PDFs generated and uploaded to Supabase Storage)
4. 🔲 **Dify Agents** — Build next. Start with Claims Assessment Agent (most complex, flagship)
5. 🔲 **MCP Server** — Build after agents are designed, so endpoints match exactly what agents need
6. 🔲 **Frontend** — Build last, it just calls Dify via REST API
7. 🔲 **Testing + UAT** — All of June 2026
8. 🔲 **Final Report** — July 1-19 2026

---

## 11. Build Status

| Component | Status | Notes |
|---|---|---|
| Docker Desktop | ✅ Done | 6 CPU, 8GB RAM |
| Dify container | ✅ Done | Running at `http://localhost`, GPT-5.2 connected |
| Supabase project | ✅ Done | Singapore region, RLS enabled |
| GitHub repo | ✅ Done | `sit_capstone`, public |
| Cursor setup | ✅ Done | Project open |
| Eligibility rules | ✅ Done | 24 rules across 4 types |
| Policies table | ✅ Done | 1000 rows |
| Claims table | ✅ Done | 1522 rows |
| Policy PDFs | ✅ Done | 1000 PDFs in Supabase Storage |
| Vercel account | ✅ Done | Connected to GitHub |
| MCP server | 🔲 Not started | Build after Dify agents |
| Dify agents | 🔲 Not started | **Start here** |
| Frontend | 🔲 Not started | Build last |

---

## 12. Key Decisions Log

These decisions have been made and are final. Do not revisit without good reason:

| Decision | What Was Decided | Why |
|---|---|---|
| LLM platform | Dify (self-hosted Docker) | Security (no dependency chain), explainability (visual builder), governance features |
| No customers table | customer_id is a loose text reference only | Mirrors real enterprise data separation; personal details in policy_text |
| Lean schema | Unstructured content in policy_text, not normalised fields | LLM reasons over text; deliberate architectural choice documented in report |
| Per-type workflows (not per-product) | 4 separate sub-workflows (Life, Health, CI, Disability) called by a main routing workflow — not 60 per-product workflows | Feasible in timeline; product differences handled by LLM reading policy_text; each sub-workflow independently testable |
| Fictional product names | AIA LifeGuard, AIA MediShield etc. (not real AIA products) | Avoids trademark issues; supervisor-approved |
| Fictional company details in PDFs | Reg. No. 202600001Z, www.aia-s.com.sg etc. | Same reason; AIA company name retained |
| policy_text + policy_summary both stored | Full text for deep analysis, summary for fast agent calls | Balances token cost vs depth of reasoning |
| Service role key in MCP server | Bypasses RLS for trusted backend | MCP server is a controlled backend; frontend never touches Supabase |
| GPT-5.2 as default | Reasoning model for complex multi-step eligibility assessment | Eligible for complex workflows; $100 credit is sufficient |
| Build Dify agents before MCP server | Agents first, then shape MCP endpoints around what agents need | Avoids building endpoints that don't match agent requirements |

---

## 13. Final Report Requirements

The final capstone report must cover:
- Project background and industry context
- Background research (LLM platforms, agentic AI, MCP, prompt engineering)
- System architecture and design decisions — especially: lean schema rationale, why Dify over LangChain/LlamaIndex, why self-hosted container, the MCP pattern
- Implementation details for all three agents and orchestrator
- Prompt engineering approach and iteration
- Test results and UAT findings (SUS score recommended)
- Evaluation against original project objectives
- Lessons learned

**Key argument to make in report:** The lean schema (storing unstructured policy content as text rather than normalising everything into structured fields) is a deliberate architectural choice that enables LLM reasoning over product-specific terms — not a shortcut. The tradeoff (LLM interpretation vs structured query reliability) must be acknowledged and defended.

**Citation format:** IEEE

---

## 14. Academic Context

- **Interim report:** Submitted and graded. Covered project background, research, system design, and early implementation.
- **Biweekly logs:** Submitted for Weeks 1-12. Document week-by-week progress.
- **UAT:** Planned for June with AIA Technology team members (and potentially AIA China team for additional feedback)
- **Academic supervisor's note:** Focus on a few particular workflows (e.g. claims rejection) — keep efforts concentrated rather than spread thin

---

## 15. People and Contacts

| Person | Role | Contact |
|---|---|---|
| Jasbir Kaur | Student / Developer | 2302990@sit.singaporetech.edu.sg |
| Kartik-K Mahadevan | Industry Supervisor | Kartik-K.Mahadevan@aia.com |
| Harminder Singh | Academic Supervisor | harminder.singh@singaporetech.edu.sg |

---

*This document should be kept updated as the project progresses. Any AI assistant or developer picking up this project should read this document in full before making any changes to the codebase or Dify configuration.*