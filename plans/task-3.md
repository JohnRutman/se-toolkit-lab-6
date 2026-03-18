# Task 3: The System Agent

## Overview

Extend the Task 2 agent with a `query_api` tool to query the deployed backend API. The agent can now answer:

1. **Static system facts** - framework, ports, status codes (from wiki or source code)
2. **Data-dependent queries** - item count, scores (from live API)
3. **Bug diagnosis** - query API, get error, read source code to explain

## Architecture

Same agentic loop as Task 2, with one new tool:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  CLI Input  │────▶│   agent.py   │────▶│  LLM API    │
│  (question) │     │  (agentic    │     │  (Qwen)     │
└─────────────┘     │   loop)      │     └─────────────┘
                    │      │               │
                    │      ▼               │
                    │ ┌─────────────┐      │
                    │ │   Tools     │◀─────┘
                    │ │ - read_file │
                    │ │ - list_files│
                    │ │ - query_api │ ← NEW
                    │ └─────────────┘
                    │      │
                    │      ▼
                    │ ┌──────────────┐
                    └▶│  JSON Output │
                      │ {answer,     │
                      │  source,     │
                      │  tool_calls} │
                      └──────────────┘
```

## New Tool: `query_api`

### Purpose

Call the deployed backend LMS API to fetch live data or test endpoints.

### Schema

```json
{
  "type": "function",
  "function": {
    "name": "query_api",
    "description": "Call the backend LMS API. Use this for data-dependent questions (e.g., item count, scores, analytics).",
    "parameters": {
      "type": "object",
      "properties": {
        "method": {
          "type": "string",
          "description": "HTTP method (GET, POST, etc.)",
          "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]
        },
        "path": {
          "type": "string",
          "description": "API path (e.g., '/items/', '/analytics/completion-rate')"
        },
        "body": {
          "type": "string",
          "description": "Optional JSON request body (for POST/PUT)"
        }
      },
      "required": ["method", "path"]
    }
  }
}
```

### Implementation

```python
def query_api(method: str, path: str, body: str = None) -> str:
    """Call the backend LMS API with authentication."""
    api_key = os.getenv("LMS_API_KEY")
    base_url = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002")

    url = f"{base_url}{path}"
    headers = {"Authorization": f"Bearer {api_key}"}

    response = httpx.request(method, url, headers=headers, json=body)

    return json.dumps({
        "status_code": response.status_code,
        "body": response.text
    })
```

### Authentication

- Uses `LMS_API_KEY` from `.env.docker.secret` (backend API key)
- **Not** the same as `LLM_API_KEY` (LLM provider key)
- Sent as `Authorization: Bearer <LMS_API_KEY>` header

## Environment Variables

| Variable             | Purpose                     | Source                                         | Required |
| -------------------- | --------------------------- | ---------------------------------------------- | -------- |
| `LLM_API_KEY`        | LLM provider authentication | `.env.agent.secret`                            | Yes      |
| `LLM_API_BASE`       | LLM API endpoint URL        | `.env.agent.secret`                            | Yes      |
| `LLM_MODEL`          | Model name                  | `.env.agent.secret`                            | Yes      |
| `LMS_API_KEY`        | Backend API authentication  | `.env.docker.secret`                           | Yes      |
| `AGENT_API_BASE_URL` | Backend API base URL        | Optional, defaults to `http://localhost:42002` | No       |

**Important:** The autochecker injects its own values. Never hardcode these!

## System Prompt Updates

The system prompt must guide the LLM to choose the right tool:

```
You have access to three tools:

1. list_files - List files in a directory. Use for discovering files.
2. read_file - Read a file's contents. Use for wiki documentation and source code.
3. query_api - Call the backend API. Use for live data (item counts, scores, analytics).

Tool selection guide:
- Wiki/documentation questions → list_files, then read_file
- Source code questions → read_file on backend/ files
- Live data questions (how many, what score) → query_api
- HTTP status codes → query_api without auth header
- Bug diagnosis → query_api first, then read_file on error location
```

## Benchmark Questions

The `run_eval.py` script tests 10 questions:

| #   | Question                 | Tool(s)              | Expected Answer                           |
| --- | ------------------------ | -------------------- | ----------------------------------------- |
| 0   | Wiki: protect branch     | read_file            | branch, protect                           |
| 1   | Wiki: SSH to VM          | read_file            | ssh, key, connect                         |
| 2   | Web framework            | read_file            | FastAPI                                   |
| 3   | API router modules       | list_files           | items, interactions, analytics, pipeline  |
| 4   | Item count               | query_api            | number > 0                                |
| 5   | Status code without auth | query_api            | 401 or 403                                |
| 6   | Division by zero bug     | query_api, read_file | ZeroDivisionError                         |
| 7   | TypeError bug            | query_api, read_file | TypeError, None, sorted                   |
| 8   | Request lifecycle        | read_file            | Caddy → FastAPI → auth → ORM → PostgreSQL |
| 9   | ETL idempotency          | read_file            | external_id check, duplicates skipped     |

## Implementation Steps

1. Create `plans/task-3.md` (this file)
2. Add `query_api` tool function with authentication
3. Add `query_api` schema to TOOLS list
4. Update system prompt for tool selection
5. Read `LMS_API_KEY` and `AGENT_API_BASE_URL` from env
6. Run `uv run run_eval.py` and iterate
7. Update `AGENT.md` with lessons learned
8. Add 2 regression tests
9. Pass all 10 eval questions

## Expected Challenges

| Challenge                     | Solution                                  |
| ----------------------------- | ----------------------------------------- |
| LLM calls wrong tool          | Improve tool descriptions in schema       |
| API returns 401               | Check LMS_API_KEY is loaded correctly     |
| Agent times out               | Reduce max iterations or use faster model |
| Answer doesn't match keywords | Adjust system prompt for precision        |
| LLM returns null content      | Use `(msg.get("content") or "")`          |

## Success Criteria

- `query_api` tool authenticates correctly
- Agent passes all 10 `run_eval.py` questions
- Agent uses correct tools for each question type
- No hardcoded values (all from environment variables)

## Benchmark Results

Initial run: **3/10 passed**

### Passing Questions

1. ✓ Wiki: protect branch - uses `list_files`, `read_file` on `wiki/github.md`
2. ✓ Wiki: SSH to VM - uses `list_files`, `read_file` on `wiki/ssh.md`
3. ✓ Web framework - uses `read_file` on `backend/app/main.py`, finds `FastAPI`

### Failing Questions

4. ✗ API router modules - LLM stops after reading one file, doesn't read all routers
5. ✗ Status code without auth - `query_api` always sends auth header
6. ✗ Division by zero bug - needs ETL pipeline to populate data
7. ✗ TypeError bug - needs ETL pipeline to populate data
8. ✗ Request lifecycle - LLM judge, needs comprehensive answer
9. ✗ ETL idempotency - LLM judge, needs to read pipeline code

### Iteration Strategy

1. Improve system prompt to encourage reading ALL files for "list all" questions
2. Consider splitting `query_api` into `query_api_auth` and `query_api_no_auth`
3. Run ETL pipeline to populate test data
4. Increase max_tokens and max_iterations for complex questions
