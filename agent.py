#!/usr/bin/env python3
"""
Agent CLI - Task 2: The Documentation Agent

An agent that uses tools (read_file, list_files) to answer questions about the project.
Implements an agentic loop: LLM → tool call → execute → repeat until answer.
"""

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from openai import OpenAI


# Project root directory (where agent.py is located)
PROJECT_ROOT = Path(__file__).parent

# Maximum tool calls per question
MAX_TOOL_CALLS = 15


def load_env():
    """Load environment variables from .env.agent.secret and .env.docker.secret"""
    # Load LLM config from .env.agent.secret
    agent_env_path = PROJECT_ROOT / ".env.agent.secret"
    if agent_env_path.exists():
        load_dotenv(agent_env_path)
    
    # Load LMS API config from .env.docker.secret
    docker_env_path = PROJECT_ROOT / ".env.docker.secret"
    if docker_env_path.exists():
        load_dotenv(docker_env_path, override=False)  # Don't override existing


def get_llm_config():
    """Get LLM configuration from environment variables"""
    api_key = os.getenv("LLM_API_KEY")
    api_base = os.getenv("LLM_API_BASE")
    model = os.getenv("LLM_MODEL", "qwen3-coder-plus")

    if not api_key:
        print("Error: LLM_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    if not api_base:
        print("Error: LLM_API_BASE not set", file=sys.stderr)
        sys.exit(1)

    return api_key, api_base, model


def create_client(api_key: str, api_base: str) -> OpenAI:
    """Create OpenAI-compatible client"""
    return OpenAI(api_key=api_key, base_url=api_base)


def query_api(method: str, path: str, body: str = None) -> str:
    """
    Call the backend LMS API with authentication.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: API path (e.g., '/items/', '/analytics/completion-rate')
        body: Optional JSON request body (for POST/PUT)
        
    Returns:
        JSON string with status_code and body, or error message
    """
    api_key = os.getenv("LMS_API_KEY")
    base_url = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002")
    
    if not api_key:
        return json.dumps({"error": "LMS_API_KEY not set"})
    
    url = f"{base_url}{path}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = httpx.request(method, url, headers=headers, json=body, timeout=30.0)
        return json.dumps({
            "status_code": response.status_code,
            "body": response.text
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def validate_path(path: str) -> tuple[bool, str]:
    """
    Validate that a path is safe (no directory traversal).
    Returns (is_valid, error_message).
    """
    # Check for empty path
    if not path or not path.strip():
        return False, "Path cannot be empty"
    
    # Check for absolute paths
    if path.startswith("/") or path.startswith("\\"):
        return False, "Absolute paths are not allowed"
    
    # Check for directory traversal
    if ".." in path:
        return False, "Directory traversal (..) is not allowed"
    
    # Resolve the full path and ensure it's within project root
    try:
        full_path = (PROJECT_ROOT / path).resolve()
        if not str(full_path).startswith(str(PROJECT_ROOT.resolve())):
            return False, "Path is outside project directory"
    except Exception as e:
        return False, f"Invalid path: {e}"
    
    return True, ""


def read_file(path: str) -> str:
    """
    Read a file from the project repository.
    
    Args:
        path: Relative path from project root
        
    Returns:
        File contents as string, or error message
    """
    is_valid, error = validate_path(path)
    if not is_valid:
        return f"Error: {error}"
    
    full_path = PROJECT_ROOT / path
    
    if not full_path.exists():
        return f"Error: File not found: {path}"
    
    if not full_path.is_file():
        return f"Error: Not a file: {path}"
    
    try:
        return full_path.read_text()
    except Exception as e:
        return f"Error reading file: {e}"


def list_files(path: str) -> str:
    """
    List files and directories at a given path.
    
    Args:
        path: Relative directory path from project root
        
    Returns:
        Newline-separated listing of entries, or error message
    """
    is_valid, error = validate_path(path)
    if not is_valid:
        return f"Error: {error}"
    
    full_path = PROJECT_ROOT / path
    
    if not full_path.exists():
        return f"Error: Directory not found: {path}"
    
    if not full_path.is_dir():
        return f"Error: Not a directory: {path}"
    
    try:
        entries = sorted([e.name for e in full_path.iterdir()])
        return "\n".join(entries)
    except Exception as e:
        return f"Error listing directory: {e}"


# Tool definitions for LLM function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project repository. Use this to read documentation files in the wiki/ directory or source code in backend/.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root (e.g., 'wiki/git-workflow.md' or 'backend/app/api/items.py')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories in a directory. Use this to discover what files are available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root (e.g., 'wiki' or 'backend/app/api')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Call the backend LMS API. Use this for data-dependent questions like item counts, scores, analytics, or checking HTTP status codes. Requires authentication.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, PUT, DELETE, PATCH)",
                        "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]
                    },
                    "path": {
                        "type": "string",
                        "description": "API path (e.g., '/items/', '/analytics/completion-rate', '/analytics/top-learners')"
                    },
                    "body": {
                        "type": "string",
                        "description": "Optional JSON request body for POST/PUT requests"
                    }
                },
                "required": ["method", "path"]
            }
        }
    }
]

# Map function names to actual functions
TOOL_FUNCTIONS = {
    "read_file": read_file,
    "list_files": list_files,
    "query_api": query_api,
}


def get_system_prompt() -> str:
    """Get the system prompt for the agent"""
    return """You are a helpful assistant that answers questions about this software project by reading documentation, source code, and querying the live API.

You have access to three tools:
- list_files: List files and directories in a directory. Use this to discover what files are available.
- read_file: Read the contents of a file. Use this to read documentation (wiki/), source code (backend/), or configuration files.
- query_api: Call the backend LMS API. Use this for data-dependent questions (item counts, scores, analytics) or checking HTTP status codes.

Tool selection guide:
- Wiki/documentation questions → use list_files to discover, then read_file to find answers
- Source code questions → use read_file on backend/ files
- Live data questions (how many items, what scores, how many learners) → use query_api
- HTTP status codes → use query_api (may return 401/403 without auth)
- Bug diagnosis → use query_api first to see the error, then read_file on the error location. When asked about bugs, look for: division operations (ZeroDivisionError), sorting with None values (TypeError), missing null checks.
- "List all" questions → use list_files first, then read ALL relevant files before answering
- Request lifecycle questions → read docker-compose.yml, Caddyfile, Dockerfile, and main.py to trace the full path
- Docker questions → search wiki/ for docker-related files and read them thoroughly

When answering:
1. Choose the right tool(s) for the question
2. For "list all" questions, read ALL relevant files before providing the final answer
3. For wiki/source questions, include a source reference (e.g., wiki/file.md#section or backend/file.py)
4. For bug questions, explain BOTH what error occurs AND which line/code causes it
5. For lifecycle questions, trace ALL hops: Caddy (reverse proxy) → FastAPI (app) → authentication → router → ORM/SQLAlchemy → PostgreSQL
6. Stop calling tools once you have enough information

Maximum 15 tool calls per question. Be thorough - read multiple files when needed."""


def execute_tool_call(tool_call) -> dict:
    """
    Execute a single tool call and return the result.
    
    Args:
        tool_call: OpenAI tool call object
        
    Returns:
        dict with tool name, args, and result
    """
    function_name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        args = {}
    
    print(f"Executing tool: {function_name}({args})", file=sys.stderr)
    
    # Execute the tool
    if function_name in TOOL_FUNCTIONS:
        func = TOOL_FUNCTIONS[function_name]
        result = func(**args)
    else:
        result = f"Error: Unknown tool: {function_name}"
    
    return {
        "tool": function_name,
        "args": args,
        "result": result,
    }


def run_agentic_loop(client: OpenAI, model: str, question: str) -> tuple[str, str, list]:
    """
    Run the agentic loop: LLM → tool call → execute → repeat.
    
    Args:
        client: OpenAI client
        model: Model name
        question: User's question
        
    Returns:
        Tuple of (answer, source, tool_calls_list)
    """
    # Initialize conversation
    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": question},
    ]
    
    tool_calls_log = []
    iteration = 0
    
    while iteration < MAX_TOOL_CALLS:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---", file=sys.stderr)
        
        # Call LLM
        print(f"Calling LLM...", file=sys.stderr)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=3000,
            tools=TOOLS,
        )
        
        assistant_message = response.choices[0].message
        
        # Check if LLM returned tool calls
        if assistant_message.tool_calls:
            print(f"LLM returned {len(assistant_message.tool_calls)} tool call(s)", file=sys.stderr)
            
            # Add assistant message to conversation
            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": assistant_message.tool_calls,
            })
            
            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                result_dict = execute_tool_call(tool_call)
                tool_calls_log.append(result_dict)
                
                # Add tool result to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_dict["result"],
                })
            
            # Continue loop - LLM will process tool results
            continue
        else:
            # No tool calls - LLM provided final answer
            print(f"LLM provided final answer", file=sys.stderr)
            answer = assistant_message.content
            
            # Try to extract source from the answer or tool calls
            source = extract_source(answer, tool_calls_log)
            
            return answer, source, tool_calls_log
    
    # Max iterations reached
    print(f"Max tool calls ({MAX_TOOL_CALLS}) reached", file=sys.stderr)
    
    # Return whatever answer we have
    if tool_calls_log:
        # Use the last tool result as a fallback
        last_result = tool_calls_log[-1]["result"]
        answer = f"Reached maximum tool calls. Last result: {last_result[:200]}"
        source = ""
    else:
        answer = "Unable to answer after maximum tool calls."
        source = ""
    
    return answer, source, tool_calls_log


def extract_source(answer: str, tool_calls: list = None) -> str:
    """
    Try to extract a source reference from the answer or tool calls.
    Looks for patterns like wiki/filename.md, backend/filename.py, or file paths.
    """
    import re

    # First try to find source from the answer text
    patterns = [
        r"(wiki/[\w\-/]+\.md(?:#[\w\-]+)?)",  # wiki files
        r"(backend/[\w\-/]+\.py)",  # backend Python files
        r"([\w\-/]+\.md(?:#[\w\-]+)?)",  # any .md file
        r"([\w\-/]+\.py)",  # any .py file
        r"(docker-compose\.yml)",  # docker-compose.yml
        r"(Dockerfile)",  # Dockerfile
    ]

    for pattern in patterns:
        match = re.search(pattern, answer)
        if match:
            return match.group(1)

    # If not found in answer, try to get from tool calls
    if tool_calls:
        for tc in tool_calls:
            tool_name = tc.get("tool", "")
            args = tc.get("args", {})
            path = args.get("path", "")

            if tool_name == "read_file" and path:
                # Return the last file read
                return path

    return ""


def main():
    """Main entry point"""
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: uv run agent.py \"<question>\"", file=sys.stderr)
        sys.exit(1)
    
    question = sys.argv[1]
    
    # Load configuration
    load_env()
    api_key, api_base, model = get_llm_config()
    
    print(f"Calling LLM: {model}", file=sys.stderr)
    print(f"Question: {question}", file=sys.stderr)
    
    # Create client
    client = create_client(api_key, api_base)
    
    # Run agentic loop
    answer, source, tool_calls_log = run_agentic_loop(client, model, question)
    
    print(f"\nGot answer from LLM", file=sys.stderr)
    
    # Output JSON response
    result = {
        "answer": answer,
        "source": source,
        "tool_calls": tool_calls_log,
    }
    
    # Output valid JSON to stdout
    print(json.dumps(result))
    
    sys.exit(0)


if __name__ == "__main__":
    main()
