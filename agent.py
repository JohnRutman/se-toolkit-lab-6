#!/usr/bin/env python3
"""
Agent CLI - Task 1: Call an LLM from Code

A simple CLI that takes a question, sends it to an LLM, and returns a JSON response.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def load_env():
    """Load environment variables from .env.agent.secret"""
    env_path = Path(__file__).parent / ".env.agent.secret"
    if not env_path.exists():
        print(f"Error: {env_path} not found", file=sys.stderr)
        sys.exit(1)
    load_dotenv(env_path)


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


def get_answer(client: OpenAI, model: str, question: str) -> str:
    """Get answer from LLM"""
    system_prompt = (
        "You are a helpful assistant. Answer questions directly and concisely. "
        "Output only the answer without additional explanation unless asked."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    return response.choices[0].message.content


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

    # Create client and get answer
    client = create_client(api_key, api_base)
    answer = get_answer(client, model, question)

    print(f"Got answer from LLM", file=sys.stderr)

    # Output JSON response
    result = {
        "answer": answer,
        "tool_calls": [],
    }

    # Output valid JSON to stdout
    print(json.dumps(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
