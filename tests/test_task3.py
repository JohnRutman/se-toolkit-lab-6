"""
Regression tests for Task 3: The System Agent

Tests that agent.py uses query_api tool and returns JSON with
answer, source, and tool_calls fields.
"""

import json
import subprocess
from pathlib import Path


def run_agent(question: str):
    """Run agent.py with a question argument."""
    cmd = ["uv", "run", "agent.py", question]
    
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=Path(__file__).parent.parent,
    )


def test_agent_uses_query_api_for_data():
    """Test that agent uses query_api when asked about live data."""
    # Ask a question that requires querying the API
    result = run_agent("How many items are currently stored in the database?")
    
    # Check exit code
    assert result.returncode == 0, f"Agent exited with code {result.returncode}: {result.stderr}"
    
    # Parse stdout as JSON
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Agent output is not valid JSON: {e}\nStdout: {result.stdout}")
    
    # Check required fields
    assert "answer" in output, "Missing 'answer' field in output"
    assert "source" in output, "Missing 'source' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"
    
    # Check that tool_calls is populated with query_api
    assert len(output["tool_calls"]) > 0, "tool_calls should be populated for data questions"
    
    tool_names = [tc.get("tool") for tc in output["tool_calls"]]
    assert "query_api" in tool_names, "Agent should use query_api for data questions"
    
    # Check answer is non-empty
    assert len(output["answer"].strip()) > 0, "'answer' field is empty"
    
    print(f"✓ Test passed: answer='{output['answer'][:50]}...'")
    print(f"  Tools used: {tool_names}")


def test_agent_uses_read_file_for_source_code():
    """Test that agent uses read_file when asked about source code."""
    # Ask a question that requires reading source code
    result = run_agent("What Python web framework does this project's backend use?")
    
    # Check exit code
    assert result.returncode == 0, f"Agent exited with code {result.returncode}: {result.stderr}"
    
    # Parse stdout as JSON
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Agent output is not valid JSON: {e}\nStdout: {result.stdout}")
    
    # Check required fields
    assert "answer" in output, "Missing 'answer' field in output"
    assert "source" in output, "Missing 'source' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"
    
    # Check that tool_calls is populated
    assert len(output["tool_calls"]) > 0, "tool_calls should be populated for source code questions"
    
    # Check that read_file was used
    tool_names = [tc.get("tool") for tc in output["tool_calls"]]
    assert "read_file" in tool_names, "Agent should use read_file for source code questions"
    
    # Check that source contains backend reference
    assert "backend" in output["source"].lower() or len(output["tool_calls"]) > 0, \
        "Source should reference backend files or tools should be used"
    
    # Check answer contains FastAPI
    assert "fastapi" in output["answer"].lower(), "Answer should mention FastAPI"
    
    print(f"✓ Test passed: answer='{output['answer'][:50]}...', source='{output['source']}'")
    print(f"  Tools used: {tool_names}")


if __name__ == "__main__":
    test_agent_uses_query_api_for_data()
    print()
    test_agent_uses_read_file_for_source_code()
    print("\n✓ All Task 3 tests passed!")
