"""
Synthesizer node prompt templates and builders
"""
import json
from typing import Dict, Any, List

# Maximum character length for tool results in prompt
MAX_TOOL_RESULTS_LENGTH = 3000


def build_synthesizer_prompt(
    question: str,
    tool_results: Dict[str, Any],
    sources: List[str]
) -> str:
    """Build synthesizer prompt for final answer generation

    Args:
        question: The original user question
        tool_results: Dictionary of tool results
        sources: List of source names used

    Returns:
        Formatted prompt string for the synthesizer

    Raises:
        ValueError: If required parameters are invalid
        RuntimeError: If JSON serialization fails
    """
    # Input validation
    if not question or not isinstance(question, str):
        raise ValueError("question must be a non-empty string")
    if not isinstance(tool_results, dict):
        raise ValueError("tool_results must be a dictionary")
    if not isinstance(sources, list):
        raise ValueError("sources must be a list")

    # Serialize and conditionally truncate tool results
    try:
        tool_results_str = json.dumps(tool_results, indent=2, default=str)
    except (TypeError, ValueError) as e:
        raise RuntimeError(f"Failed to serialize tool_results: {e}")

    # Only add "..." if we actually truncated
    if len(tool_results_str) > MAX_TOOL_RESULTS_LENGTH:
        tool_results_display = tool_results_str[:MAX_TOOL_RESULTS_LENGTH] + "..."
    else:
        tool_results_display = tool_results_str

    prompt = f"""You are a helpful assistant that synthesizes information from multiple sources into a clear, natural answer.

USER QUESTION: "{question}"

AVAILABLE DATA:
{tool_results_display}

SOURCES USED: {', '.join(sources) if sources else 'None'}

YOUR TASK:
Generate a natural, helpful response that:
1. Directly answers the user's question
2. Integrates information from all available sources
3. Is concise but complete
4. Mentions sources when relevant
5. Acknowledges limitations if data is incomplete

DO NOT:
- Just dump raw data
- Make up information not in the results
- Be overly technical unless appropriate
"""

    return prompt
