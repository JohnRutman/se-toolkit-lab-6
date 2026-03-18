"""
Regression tests for Task 1: Call an LLM from Code

Tests that agent.py outputs valid JSON with required fields.
"""

import json
import subprocess
import sys
from pathlib import Path


def run_agent(question: str = None):
    """Run agent.py with optional question argument."""
    cmd = ["uv", "run", "agent.py"]
    if question:
        cmd.append(question)
    
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=Path(__file__).parent.parent,
    )


def test_agent_outputs_valid_json():
    """Test that agent.py outputs valid JSON with answer and tool_calls fields."""
    # Run agent.py with a test question
    result = run_agent("What is 2+2?")

    # Check exit code
    assert result.returncode == 0, f"Agent exited with code {result.returncode}: {result.stderr}"

    # Parse stdout as JSON
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Agent output is not valid JSON: {e}\nStdout: {result.stdout}")

    # Check required fields
    assert "answer" in output, "Missing 'answer' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"

    # Check field types
    assert isinstance(output["answer"], str), "'answer' must be a string"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"

    # Check answer is non-empty
    assert len(output["answer"].strip()) > 0, "'answer' field is empty"

    print(f"✓ Test passed: answer='{output['answer'][:50]}...'")


def test_agent_handles_missing_argument():
    """Test that agent.py exits with error when no question provided."""
    result = run_agent()

    # Should exit with non-zero code
    assert result.returncode != 0, "Agent should exit with error when no argument provided"

    # Should print usage to stderr
    assert "Usage" in result.stderr or "usage" in result.stderr, "Should print usage to stderr"

    print("✓ Test passed: handles missing argument correctly")


if __name__ == "__main__":
    test_agent_outputs_valid_json()
    test_agent_handles_missing_argument()
    print("\n✓ All tests passed!")
