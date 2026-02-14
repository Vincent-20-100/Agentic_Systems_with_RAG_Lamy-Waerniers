"""
Synthesizer node prompt templates and builders
"""
import json


def build_synthesizer_prompt(
    question: str,
    tool_results: dict,
    sources: list
) -> str:
    """Build synthesizer prompt for final answer generation"""

    prompt = f"""You are a helpful assistant that synthesizes information from multiple sources into a clear, natural answer.

USER QUESTION: "{question}"

AVAILABLE DATA:
{json.dumps(tool_results, indent=2, default=str)[:3000]}

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
