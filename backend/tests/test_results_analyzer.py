"""Unit tests for the Results Analyzer agent."""
from app.agents.orchestrator import classify_intent, detect_slash_command, dispatch_to_agent
from app.models.schemas import AgentType

def test_results_analyzer_routing():
    """Verify that results analyzer keywords route to the correct agent."""
    assert classify_intent("analyze results") == AgentType.AUTORESEARCH_ANALYZER
    assert classify_intent("explain the training progress") == AgentType.AUTORESEARCH_ANALYZER
    
def test_results_analyzer_slash_command():
    """Verify slash command routing."""
    agent, msg = detect_slash_command("/analyze the results")
    assert agent == AgentType.AUTORESEARCH_ANALYZER
    assert msg == "the results"

def test_results_analyzer_dispatch():
    """Verify the agent can be dispatched to and handles quick topics."""
    result = dispatch_to_agent(AgentType.AUTORESEARCH_ANALYZER, "analyze results")
    assert "Autoresearch Results Summary" in result["response"]
    assert "Training Trend Analysis" in result["response"]
