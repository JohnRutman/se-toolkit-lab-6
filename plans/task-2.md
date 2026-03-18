# Task 2: The Documentation Agent

## Overview

Extend the Task 1 agent with tools (`read_file`, `list_files`) and an agentic loop. The agent can now read project documentation to answer questions with source references.

## Architecture

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

## Agentic Loop

1. Send user question + tool definitions to LLM
2. If LLM returns `tool_calls`:
   - Execute each tool
   - Append results as `tool` role messages
   - Send back to LLM (max 10 iterations)
3. If LLM returns text answer:
   - Extract answer and source
   - Output JSON and exit

## Tool Definitions

### `read_file`

**Purpose:** Read file contents from the project repository.

**Schema:**
```json
{
  "name": "read_file",
  "description": "Read a file from the project repository",
  "parameters": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "Relative path from project root (e.g., 'wiki/git-workflow.md')"
      }
    },
    "required": ["path"]
  }
}
```

**Security:**
- Reject paths containing `..` (directory traversal)
- Reject absolute paths
- Only allow files within project root

### `list_files`

**Purpose:** List files and directories at a given path.

**Schema:**
```json
{
  "name": "list_files",
  "description": "List files and directories in a directory",
  "parameters": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "Relative directory path from project root (e.g., 'wiki')"
      }
    },
    "required": ["path"]
  }
}
```

**Security:**
- Same path validation as `read_file`
- Only allow directories within project root

## System Prompt Strategy

The system prompt will instruct the LLM to:

1. Use `list_files` to discover wiki files when asked about project documentation
2. Use `read_file` to read specific files and find answers
3. Include source references in the format `wiki/filename.md#section-anchor`
4. Stop after finding the answer (max 10 tool calls)

Example system prompt:
```
You are a helpful assistant that answers questions about this software project.
You have access to two tools:
- list_files: List files in a directory
- read_file: Read contents of a file

When answering questions about the project:
1. First use list_files to discover relevant files in the wiki/ directory
2. Then use read_file to read specific files and find the answer
3. Always include a source reference in your answer (e.g., "wiki/git-workflow.md#resolving-merge-conflicts")
4. Stop calling tools once you have enough information to answer

Maximum 10 tool calls per question.
```

## Output Format

```json
{
  "answer": "The answer from the LLM",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {
      "tool": "list_files",
      "args": {"path": "wiki"},
      "result": "git-workflow.md\n..."
    },
    {
      "tool": "read_file",
      "args": {"path": "wiki/git-workflow.md"},
      "result": "...content..."
    }
  ]
}
```

## Implementation Steps

1. Create `plans/task-2.md` (this file)
2. Add tool function definitions (`read_file`, `list_files`)
3. Add tool schemas for LLM function calling
4. Implement agentic loop (max 10 iterations)
5. Update output JSON to include `source` and populated `tool_calls`
6. Update `AGENT.md` with tool documentation
7. Add 2 regression tests
8. Test manually with wiki questions

## Files to Modify

- `agent.py` - Add tools and agentic loop
- `AGENT.md` - Document tools and loop
- `tests/test_task1.py` → `tests/test_task2.py` - Add 2 new tests
