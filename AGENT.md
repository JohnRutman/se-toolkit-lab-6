# Agent Architecture

## Overview

This project implements an AI-powered agent that answers questions about the Learning Management System (LMS) by reading project documentation. The agent uses Large Language Models (LLMs) with function calling to execute tools and gather information.

## Task 2: The Documentation Agent

### Architecture

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

### Agentic Loop

The agent implements a reasoning loop:

1. **Send question** - User's question + tool definitions sent to LLM
2. **LLM decides** - LLM either:
   - Returns `tool_calls` → execute tools, append results, go to step 1
   - Returns text answer → output JSON and exit
3. **Maximum 10 iterations** - Prevents infinite loops

```python
while iteration < MAX_TOOL_CALLS:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
    )

    if response.tool_calls:
        # Execute tools and continue
    else:
        # Return final answer
```

### Tools

#### `read_file`

Read a file from the project repository.

**Parameters:**

- `path` (string): Relative path from project root (e.g., `wiki/git-workflow.md`)

**Returns:** File contents as string, or error message

**Security:**

- Rejects paths containing `..` (directory traversal)
- Rejects absolute paths
- Only allows files within project root

#### `list_files`

List files and directories at a given path.

**Parameters:**

- `path` (string): Relative directory path from project root (e.g., `wiki`)

**Returns:** Newline-separated listing of entries, or error message

**Security:**

- Same path validation as `read_file`
- Only allows directories within project root

### Tool Schemas

Tools are defined as OpenAI-compatible function schemas:

```json
{
  "type": "function",
  "function": {
    "name": "read_file",
    "description": "Read a file from the project repository...",
    "parameters": {
      "type": "object",
      "properties": {
        "path": { "type": "string", "description": "..." }
      },
      "required": ["path"]
    }
  }
}
```

### System Prompt

The system prompt instructs the LLM how to use tools:

```
You are a helpful assistant that answers questions about this software project
by reading the project documentation.

You have access to two tools:
- list_files: List files and directories in a directory.
- read_file: Read the contents of a file.

When answering questions about the project:
1. First use list_files to discover relevant files (e.g., in the wiki/ directory)
2. Then use read_file to read specific files and find the answer
3. Always include a source reference in your answer
4. Stop calling tools once you have enough information

Maximum 10 tool calls per question.
```

### Output Format

```json
{
  "answer": "Edit the conflicting file, choose which changes to keep, then stage and commit.",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {
      "tool": "list_files",
      "args": { "path": "wiki" },
      "result": "git-workflow.md\n..."
    },
    {
      "tool": "read_file",
      "args": { "path": "wiki/git-workflow.md" },
      "result": "...content..."
    }
  ]
}
```

- `answer` (string): The LLM's final answer
- `source` (string): Reference to the wiki section (e.g., `wiki/file.md#anchor`)
- `tool_calls` (array): All tool calls made during the agentic loop

### Usage

```bash
# Run the agent with a question
uv run agent.py "How do you resolve a merge conflict?"

# Output (JSON to stdout)
{
  "answer": "...",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [...]
}
```

### Path Security

The agent validates all file paths to prevent directory traversal attacks:

```python
def validate_path(path: str) -> tuple[bool, str]:
    # Reject empty paths
    # Reject absolute paths
    # Reject paths containing ".."
    # Ensure resolved path is within project root
```

### LLM Provider

**Qwen Code API** (self-hosted on VM)

- **Model:** `qwen3-coder-plus`
- **API Base:** `http://10.93.25.200:42005/v1`
- **Benefits:** 1000 free requests/day, OpenAI-compatible function calling

### Environment Variables

Stored in `.env.agent.secret` (gitignored):

| Variable       | Description                | Example                        |
| -------------- | -------------------------- | ------------------------------ |
| `LLM_API_KEY`  | API key for authentication | `my-secret-qwen-key`           |
| `LLM_API_BASE` | Base URL of the LLM API    | `http://10.93.25.200:42005/v1` |
| `LLM_MODEL`    | Model name to use          | `qwen3-coder-plus`             |

### Testing

Run the regression tests:

```bash
uv run pytest tests/test_task2.py -v
```

Tests verify:

- `read_file` is called when asked about documentation
- `list_files` is called when asked about available files
- `source` field contains wiki file reference
- `tool_calls` array is populated

### Future Tasks

#### Task 3: Agentic Loop with More Tools

Add more tools:

- `query_api` - Query the backend LMS API for data-dependent questions
- Enhanced system prompt for multi-step reasoning

The agent will handle complex questions requiring multiple tool chains.
