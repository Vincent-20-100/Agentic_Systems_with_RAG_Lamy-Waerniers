"""
Synthesizer node - generate final natural language response
"""
from langchain_core.messages import AIMessage
from code.core.state import AgentState
from code.prompts.synthesizer_prompts import build_synthesizer_prompt
from code.config import llm


def synthesizer_node(state: AgentState) -> dict:
    """
    Generate final answer from all tool results

    Uses all accumulated results across iterations
    """
    question = state.get("original_question", "")
    all_results = state.get("previous_results", {})
    sources = state.get("sources_used", [])

    # Build synthesis prompt
    prompt = build_synthesizer_prompt(
        question=question,
        tool_results=all_results,
        sources=sources
    )

    # Generate response
    try:
        response = llm.invoke(prompt)

        return {
            "messages": [AIMessage(content=response.content)]
        }
    except Exception as e:
        # Fallback
        return {
            "messages": [AIMessage(content=f"I apologize, but I encountered an error generating the response: {str(e)}")]
        }
