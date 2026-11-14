# HackerRank for Work REST v3 API Integration

QuestForge integrates with the official **HackerRank for Work REST v3 API** to publish automated coding challenges directly to your organization's question library and assessments.

---

## 1. Authentication & API Environments

Authentication uses an API Bearer token configured via environment variable `HACKERRANK_ACCESS_TOKEN`.

| Environment | Base URL |
| :--- | :--- |
| **Production** | `https://www.hackerrank.com/work/api/v3` |
| **Sandbox / Staging** | `https://sandbox.hackerrank.com/work/api/v3` |

Requests include the following headers:
```http
Authorization: Bearer <HACKERRANK_ACCESS_TOKEN>
Content-Type: application/json
Accept: application/json
```

---

## 2. Payload Schema Mapping

QuestForge translates internal `Question` records to HackerRank's v3 payload format:

| QuestForge Field | HackerRank Payload Field | Format / Transformation |
| :--- | :--- | :--- |
| `title` | `name` | String (up to 255 chars) |
| `story` | `problem_statement` | Markdown narrative |
| `input_format` | `input_format` | Markdown text |
| `output_format` | `output_format` | Markdown text |
| `constraints` | `constraints` | Markdown text |
| `difficulty` | `difficulty` | Lowercase: `"easy"`, `"medium"`, `"hard"` |
| `tags` | `tags` | Array of strings |
| `time_limit` | `time_limit` | Integer seconds ($1$ to $5$) |
| `memory_limit` | `memory_limit` | Integer megabytes ($256$ to $1024$) |
| `test_cases` | `testcases` | Array of test case objects |
| `reference_solution` | `solutions` | Map of `{ "python3": "...", "java17": "..." }` |

### Test Case Object Mapping
```json
{
  "stdin": "5\n1 2 3 4 5\n",
  "expected_output": "15\n",
  "is_sample": true,
  "hidden": false,
  "score": 10,
  "weight": 10
}
```

---

## 3. Resilience, Idempotency & Rate Limiting

1. **Idempotency**: When a question is published, HackerRank returns a unique question ID (e.g. `hr_q_123456`). QuestForge records this ID in `questions.hackerrank_question_id`. Subsequent publish calls automatically issue a `PUT /tests/questions/{id}` update instead of creating duplicate questions.
2. **Exponential Backoff**:
   - HTTP 429 (Too Many Requests) or 5xx server errors trigger exponential backoff.
   - Retry delays: $t = 2^{\text{attempt}} + \text{jitter}$, up to 5 attempts.
3. **Dry-Run Mode**: Passing `dry_run=True` validates payload schemas, serializes test cases, and asserts compatibility without making mutating network requests.

---

## 4. Offline Challenge ZIP Export Mode

When direct API access or credentials are not configured, QuestForge generates an industry-standard HackerRank challenge package ZIP archive downloadable directly from the UI or API:

```
challenge_package.zip
├── problem.md         # Full statement, formats, constraints, and explanation
├── editorial.md       # Optimal algorithmic editorial and complexity analysis
├── solution.py        # Verified reference solution
├── metadata.json      # Tags, difficulty, limits, and scoring schema
├── input/
│   ├── input00.txt
│   ├── input01.txt
│   └── ...
└── output/
    ├── output00.txt
    ├── output01.txt
    └── ...
```
This package can be directly uploaded to HackerRank's challenge importer.
