"""
Evaluator node prompt templates and builders
"""
import json
from typing import Dict, Any

# Maximum character length for tool results in prompt
MAX_TOOL_RESULTS_LENGTH = 2000


def build_evaluator_prompt(
    question: str,
    execution_plan: Dict[str, Any],
    tool_results: Dict[str, Any]
) -> str:
    """Build evaluator prompt to assess result sufficiency

    Args:
        question: The original user question
        execution_plan: The execution plan dictionary
        tool_results: Dictionary of tool results

    Returns:
        Formatted prompt string for the evaluator

    Raises:
        ValueError: If required parameters are invalid
        RuntimeError: If JSON serialization fails
    """
    # Input validation
    if not question or not isinstance(question, str):
        raise ValueError("question must be a non-empty string")
    if not isinstance(execution_plan, dict):
        raise ValueError("execution_plan must be a dictionary")
    if not isinstance(tool_results, dict):
        raise ValueError("tool_results must be a dictionary")

    # Serialize execution plan with error handling
    try:
        execution_plan_str = json.dumps(execution_plan, indent=2)
    except (TypeError, ValueError) as e:
        raise RuntimeError(f"Failed to serialize execution_plan: {e}")

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

    prompt = f"""You are an evaluation agent that decides if we have sufficient data to answer the user's question.

ORIGINAL QUESTION: "{question}"

EXECUTION PLAN:
{execution_plan_str}

TOOL RESULTS:
{tool_results_display}

YOUR TASK:
Evaluate if the data from the tools is sufficient to provide a complete, accurate answer to the question.

DECISION CRITERIA:

CONTINUE (sufficient data) if:
- We have all information needed to answer the question
- Data quality is good (not just empty results or errors)
- User's question can be fully addressed with available data

REPLAN (insufficient data) if:
- Missing critical information (e.g., need plot but only have titles)
- Tools returned errors or empty results
- Different tools might provide better information
- Question requires data we haven't fetched yet

PROVIDE:
1. Your decision: "continue" or "replan"
2. Clear reasoning for your decision
3. If replanning: specific instructions on what additional tools/data are needed
4. Confidence score (0.0-1.0) in the available data
"""

    return prompt
