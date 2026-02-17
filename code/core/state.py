"""
AgentState definition for the agentic workflow
"""
from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """Workflow state that flows through all nodes"""

    # Conversation
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # User input
    original_question: str

    # Database metadata (loaded once at startup)
    db_catalog: dict

    # Iteration tracking
    iteration_count: int
    max_iterations: int

    # Planning (from Planner node)
    execution_plan: dict

    # Execution (from Executor node)
    tool_results: dict

    # Evaluation (from Evaluator node)
    evaluator_decision: str
    evaluator_reasoning: str
    replan_instructions: str
    evaluator_confidence: float

    # History (for loop context)
    previous_plans: list
    previous_results: dict

    # Output
    sources_used: list
    sources_detailed: list
