# Agent Architecture

## Overview

This project implements an AI-powered agent that answers questions about the Learning Management System (LMS). The agent uses Large Language Models (LLMs) to understand questions and generate accurate responses.

## Task 1: Call an LLM from Code

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  CLI Input  │────▶│   agent.py   │────▶│  LLM API    │
│  (question) │     │  (OpenAI SDK)│     │  (Qwen)     │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  JSON Output │
                    │  {answer,    │
                    │   tool_calls}│
                    └──────────────┘
```

### Components

**agent.py** - Main CLI script that:
- Parses command-line arguments (question)
- Loads environment variables from `.env.agent.secret`
- Creates an OpenAI-compatible client
- Sends chat completion requests to the LLM
- Returns structured JSON output

### LLM Provider

**Qwen Code API** (self-hosted on VM)
- **Model:** `qwen3-coder-plus`
- **API Base:** `http://10.93.25.200:42005/v1`
- **Benefits:** 1000 free requests/day, works from Russia, no credit card required

### Environment Variables

Stored in `.env.agent.secret` (gitignored):

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_API_KEY` | API key for authentication | `my-secret-qwen-key` |
| `LLM_API_BASE` | Base URL of the LLM API | `http://10.93.25.200:42005/v1` |
| `LLM_MODEL` | Model name to use | `qwen3-coder-plus` |

### Usage

```bash
# Run the agent with a question
uv run agent.py "What does REST stand for?"

# Output (JSON to stdout)
{"answer": "Representational State Transfer.", "tool_calls": []}
```

### Output Format

The agent outputs a single JSON line to stdout:

```json
{
  "answer": "The answer from the LLM",
  "tool_calls": []
}
```

- `answer` (string): The LLM's response to the question
- `tool_calls` (array): Empty for Task 1 (will be populated in Task 2+)

### Error Handling

- Missing question argument → prints usage to stderr, exits with code 1
- API errors → prints error to stderr, exits with code 1
- All debug output goes to stderr, only valid JSON goes to stdout

### Dependencies

- `openai` - OpenAI Python SDK (compatible with OpenAI-compatible APIs)
- `python-dotenv` - Load environment variables from `.env` file

### Testing

Run the regression test:

```bash
uv run pytest tests/test_task1.py -v
```

## Future Tasks

### Task 2: Add Tools

The agent will gain access to tools:
- `read_file` - Read project documentation
- `query_api` - Query the backend LMS API

### Task 3: Agentic Loop

The agent will implement a reasoning loop:
1. Receive question
2. Decide which tools to use
3. Execute tools and gather information
4. Generate final answer

## Qwen Code API Setup

The Qwen Code API is deployed on the VM at `10.93.25.200:42005`.

### Deployment Steps

1. Install Node.js and pnpm on VM
2. Install Qwen Code CLI: `npm install -g @qwen-code/qwen-code`
3. Authenticate: `qwen` → `/auth`
4. Clone qwen-code-oai-proxy: `git clone https://github.com/inno-se-toolkit/qwen-code-oai-proxy`
5. Configure `.env` with API key
6. Run: `docker compose up --build -d`

### Testing the API

```bash
curl -s http://10.93.25.200:42005/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my-secret-qwen-key" \
  -d '{"model":"qwen3-coder-plus","messages":[{"role":"user","content":"What is 2+2?"}]}'
```
