"""
Regression tests for Task 2: The Documentation Agent

Tests that agent.py uses tools (read_file, list_files) and returns
JSON with answer, source, and tool_calls fields.
"""

import json
import subprocess
import sys
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


def test_agent_uses_read_file_for_documentation():
    """Test that agent uses read_file when asked about documentation."""
    # Ask a question that requires reading wiki files
    result = run_agent("How do you resolve a merge conflict?")
    
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
    
    # Check that tool_calls is populated (agent should use tools for documentation questions)
    assert len(output["tool_calls"]) > 0, "tool_calls should be populated for documentation questions"
    
    # Check that read_file was used
    tool_names = [tc.get("tool") for tc in output["tool_calls"]]
    assert "read_file" in tool_names, "Agent should use read_file for documentation questions"
    
    # Check that source contains wiki reference
    assert "wiki/" in output["source"] or len(output["tool_calls"]) > 0, \
        "Source should reference wiki files or tools should be used"
    
    # Check answer is non-empty
    assert len(output["answer"].strip()) > 0, "'answer' field is empty"
    
    print(f"✓ Test passed: answer='{output['answer'][:50]}...', source='{output['source']}'")
    print(f"  Tools used: {tool_names}")


def test_agent_uses_list_files_for_discovery():
    """Test that agent uses list_files when asked about available files."""
    # Ask a question that requires listing directory contents
    result = run_agent("What files are in the wiki directory?")
    
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
    assert len(output["tool_calls"]) > 0, "tool_calls should be populated for file discovery questions"
    
    # Check that list_files was used
    tool_names = [tc.get("tool") for tc in output["tool_calls"]]
    assert "list_files" in tool_names, "Agent should use list_files for file discovery"
    
    # Check answer is non-empty
    assert len(output["answer"].strip()) > 0, "'answer' field is empty"
    
    print(f"✓ Test passed: answer='{output['answer'][:50]}...'")
    print(f"  Tools used: {tool_names}")


if __name__ == "__main__":
    test_agent_uses_read_file_for_documentation()
    print()
    test_agent_uses_list_files_for_discovery()
    print("\n✓ All Task 2 tests passed!")
