# Task 1: Call an LLM from Code

## Overview

Build a Python CLI (`agent.py`) that takes a question as a command-line argument, sends it to an LLM, and returns a structured JSON response with `answer` and `tool_calls` fields.

## LLM Provider

**Provider:** Qwen Code API (deployed on VM)
- **Model:** `qwen3-coder-plus`
- **API Base:** `http://10.93.25.200:42001/v1` (VM backend)
- **Reason:** 1000 free requests/day, works from Russia, no credit card required

## Architecture

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

## Components

1. **Environment Variables** (`.env.agent.secret`):
   - `LLM_API_KEY` - API key for authentication
   - `LLM_API_BASE` - Base URL of the LLM API
   - `LLM_MODEL` - Model name to use

2. **agent.py**:
   - Parse command-line argument (question)
   - Load environment variables from `.env.agent.secret`
   - Create OpenAI client with custom base URL
   - Send chat completion request with system prompt
   - Parse response and format as JSON
   - Output to stdout, debug logs to stderr

3. **System Prompt**:
   - Simple instruction to answer questions directly
   - Will be expanded in later tasks with tool definitions

## Error Handling

- Missing question argument → print usage to stderr, exit 1
- API errors → catch exception, print to stderr, exit 1
- Invalid JSON → ensure valid JSON output always

## Testing

Single regression test:
- Run `agent.py "test question"` as subprocess
- Parse stdout JSON
- Verify `answer` field exists and is non-empty
- Verify `tool_calls` field exists and is array

## Files to Create

- `plans/task-1.md` - This plan
- `agent.py` - Main CLI script
- `.env.agent.secret` - Environment variables (gitignored)
- `AGENT.md` - Architecture documentation
- `tests/test_task1.py` - Regression test
