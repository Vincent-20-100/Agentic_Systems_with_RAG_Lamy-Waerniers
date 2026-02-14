"""
Evaluator node prompt templates and builders
"""
import json


def build_evaluator_prompt(
    question: str,
    execution_plan: dict,
    tool_results: dict
) -> str:
    """Build evaluator prompt to assess result sufficiency"""

    prompt = f"""You are an evaluation agent that decides if we have sufficient data to answer the user's question.

ORIGINAL QUESTION: "{question}"

EXECUTION PLAN:
{json.dumps(execution_plan, indent=2)}

TOOL RESULTS:
{json.dumps(tool_results, indent=2, default=str)[:2000]}...

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
