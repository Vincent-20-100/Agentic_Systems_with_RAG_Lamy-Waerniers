"""
Evaluator node - assess result sufficiency and decide to continue or replan
"""
from core.state import AgentState
from core.models import EvaluatorDecision
from prompts.evaluator_prompts import build_evaluator_prompt
from config import llm


def evaluator_node(state: AgentState) -> dict:
    """
    Assess if tool results are sufficient to answer the question

    Returns decision to continue (synthesize) or replan (loop back)
    """
    question = state.get("original_question", "")
    plan = state.get("execution_plan", {})
    tool_results = state.get("tool_results", {})
    iteration = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 2)

    # Force synthesis if max iterations reached (safety)
    if iteration >= max_iterations:
        return {
            "evaluator_decision": "continue",
            "evaluator_reasoning": f"Max iterations ({max_iterations}) reached, proceeding with available data",
            "replan_instructions": "",
            "evaluator_confidence": 0.5
        }

    # Build evaluation prompt
    prompt = build_evaluator_prompt(
        question=question,
        execution_plan=plan,
        tool_results=tool_results
    )

    # Get structured decision from LLM
    structured_llm = llm.with_structured_output(EvaluatorDecision)

    try:
        decision = structured_llm.invoke(prompt)

        return {
            "evaluator_decision": decision.decision,
            "evaluator_reasoning": decision.reasoning,
            "replan_instructions": decision.replan_instructions or "",
            "evaluator_confidence": decision.confidence
        }
    except Exception as e:
        # Fallback: continue with what we have
        return {
            "evaluator_decision": "continue",
            "evaluator_reasoning": f"Evaluation error: {str(e)}, proceeding with available data",
            "replan_instructions": "",
            "evaluator_confidence": 0.0
        }
