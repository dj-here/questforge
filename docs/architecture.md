# QuestForge Architecture & Design Specification

QuestForge is an enterprise-grade autonomous system that generates competitive programming challenges, verifies their correctness through isolated containerized execution, evaluates their pedagogical quality using an LLM critic, deduplicates against existing problem sets, and publishes approved challenges directly to HackerRank for Work via REST v3 API.

---

## 1. High-Level System Architecture

```
                  +----------------------------------------------+
                  |         Next.js + Tailwind Frontend          |
                  |  (Dashboard, Review Queue, Publish, History) |
                  +----------------------+-----------------------+
                                         | REST / JSON
                                         v
                  +----------------------------------------------+
                  |             FastAPI Backend (8000)           |
                  |  - Auth & Role Guard (Admin, Reviewer)       |
                  |  - Jobs, Questions, Publish Endpoints        |
                  |  - Metrics & Health Checks                   |
                  +-----------+----------------------+-----------+
                              |                      |
             Task Dispatch    |                      | Direct Query
                              v                      v
                   +--------------------+   +-------------------+
                   |   Redis (Broker)   |   |   PostgreSQL 16   |
                   +----------+---------+   +-------------------+
                              |
                              v
                  +----------------------------------------------+
                  |            Celery Worker Pipeline            |
                  |                                              |
                  |   [Stage 1: Spec Generation]                 |
                  |   [Stage 2: LLM JSON Generation (3x retry)]  |
                  |   [Stage 3: Test Case Sandbox Execution]     |
                  |   [Stage 4: Reference & Brute Verification]  |
                  |   [Stage 5: LLM Critic Quality Scoring]      |
                  |   [Stage 6: Vector Cosine Dedup]             |
                  |   [Stage 7: Audit Persistence]               |
                  +--------------+------------------+------------+
                                 |                  |
                   Docker Exec   |                  | REST v3 API
                                 v                  v
                  +--------------------+     +-------------------+
                  |  Hardened Sandbox  |     | HackerRank Work   |
                  |  (Zero Network,    |     | API (v3 Questions)|
                  |   Read-Only FS,    |     +-------------------+
                  |   256MB Mem Limit) |
                  +--------------------+
```

---

## 2. The 7-Stage Generation Pipeline

The core question generation engine executes seven decoupled, independently testable stages:

### Stage 1: Specification Stage (`spec_stage.py`)
- Sanitizes user input against prompt injection attacks (strips markdown delimiters, system directives, XML tags).
- Retrieves the DB-configured difficulty rubric (concepts count, target time complexity, max solution lines, constraint guidelines).
- Renders the versioned Jinja2 specification template (`prompts/v1/question_spec.j2`).

### Stage 2: Generation Stage (`generate_stage.py`)
- Invokes Anthropic Claude 3.5 Sonnet requesting strict JSON output according to `GeneratedQuestionSchema`.
- Validates the response against Pydantic v2 schema.
- Implements self-healing retry logic: on schema or JSON failure, feeds validation error back to the LLM (up to 3 attempts).

### Stage 3: Test Case Synthesis Stage (`test_case_stage.py`)
- Executes `test_case_generator_code` inside the Docker sandbox.
- Produces between 15 and 30 rigorous test cases covering:
  - Sample visible cases (with explanations).
  - Corner/edge cases (empty, zeros, negative bounds, single elements).
  - Maximum constraint stress cases ($N = 10^5$, maximum numbers).
  - Deterministic random test cases.
- Assigns score weights (samples: 0 or 5 pts, visible edge cases: 10 pts, hidden stress cases: 15-20 pts).

### Stage 4: Verification Stage (`verification_stage.py`)
- **Reference Solution Execution**: Runs `reference_solution` on all 15-30 test cases in the sandbox. Must finish within time limits ($2.0s$) and memory limits ($256$ MB) with code `0`.
- **Differential Brute-Force Testing**: Runs `brute_force_solution` on small test cases ($N \le 1000$). Verifies that the brute-force outputs match reference outputs byte-for-byte.
- Automatically rejects and triggers regeneration if any test case crashes, times out, or produces mismatched output.

### Stage 5: Quality Critic Stage (`quality_stage.py`)
- A secondary, independent LLM call acts as an adversarial reviewer.
- Scores four orthogonal dimensions on a 1.0–10.0 scale:
  1. **Clarity**: Is the problem statement unambiguous with clear input/output rules?
  2. **Originality**: Is the story creative and non-derivative?
  3. **Difficulty Match**: Does the required complexity align with the rubric?
  4. **Unambiguity**: Are boundary constraints clearly specified?
- Questions scoring below an overall average threshold (default 7.0/10) are rejected.

### Stage 6: Deduplication Stage (`dedup_stage.py`)
- Generates a normalized semantic projection vector from title and problem narrative.
- Computes cosine similarity against all existing questions in the database.
- Questions exceeding a similarity threshold (default $0.85$) are flagged as near-duplicates and rejected.

### Stage 7: Persistence & Audit Stage (`persist_stage.py`)
- Persists the validated Question, Test Cases, and Verification Execution Logs into PostgreSQL within a single atomic database transaction.
- Records a complete audit trail entry (`audit_trails`) capturing the prompt snapshot, raw LLM JSON, and reviewer actions.

---

## 3. Human Review vs. Auto-Publish

QuestForge features a toggleable workflow:
- **Human Review Mode (Default)**: Questions are saved with status `review_ready`. Reviewers inspect test cases, execution runtimes, and critic evaluations on the Review Screen, edit statements or code, and approve/reject with one click.
- **Auto-Publish Mode**: When enabled on a job (`auto_publish=True`), questions that successfully pass all 7 stages are automatically approved and dispatched to HackerRank.
