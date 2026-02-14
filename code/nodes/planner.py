"""
Planner node - LLM-powered tool selection and query preparation
"""
from code.core.state import AgentState
from code.core.models import ExecutionPlan
from code.prompts.planner_prompts import build_planner_prompt
from code.config import llm


def planner_node(state: AgentState) -> dict:
    """
    Analyze query and create execution plan

    Uses LLM with structured output to decide which tools to use
    and prepare specific queries for each tool.
    """
    question = state.get("original_question", "")
    history = state.get("messages", [])
    catalog = state.get("db_catalog", {})
    iteration = state.get("iteration_count", 0)

    # Context from previous iteration (if looping)
    previous_plans = state.get("previous_plans", [])
    previous_results = state.get("previous_results", {})
    replan_instructions = state.get("replan_instructions", "")

    # Build prompt
    prompt = build_planner_prompt(
        question=question,
        history=history[-5:] if history else [],
        catalog=catalog,
        is_replanning=(iteration > 0),
        previous_plans=previous_plans,
        previous_results=previous_results,
        replan_instructions=replan_instructions
    )

    # Get structured output from LLM
    structured_llm = llm.with_structured_output(ExecutionPlan)

    try:
        plan = structured_llm.invoke(prompt)

        return {
            "execution_plan": plan.model_dump(),
            "iteration_count": iteration + 1,
            "previous_plans": previous_plans + [plan.model_dump()]
        }
    except Exception as e:
        # Fallback: no tools selected
        fallback_plan = ExecutionPlan(
            reasoning=f"Planning error: {str(e)}",
            resolved_query=question
        )
        return {
            "execution_plan": fallback_plan.model_dump(),
            "iteration_count": iteration + 1,
            "previous_plans": previous_plans + [fallback_plan.model_dump()]
        }
