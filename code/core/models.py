"""
Pydantic models for structured LLM outputs
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class ExecutionPlan(BaseModel):
    """Planner's structured decision output"""

    # Tools to execute
    use_sql: bool = False
    use_semantic: bool = False
    use_omdb: bool = False
    use_web: bool = False

    # Prepared queries for each tool
    sql_query: Optional[str] = None
    sql_database: Optional[str] = None

    semantic_query: Optional[str] = None
    semantic_n_results: int = 5

    omdb_title: Optional[str] = None

    web_query: Optional[str] = None
    web_n_results: int = 5

    # Planning metadata
    reasoning: str = Field(..., description="Why these tools were selected")
    resolved_query: str = Field(..., description="Clarified query with context from history")


class EvaluatorDecision(BaseModel):
    """Evaluator's assessment of tool results"""

    decision: Literal["continue", "replan"] = Field(
        ...,
        description="'continue' to synthesize answer, 'replan' to select more tools"
    )

    reasoning: str = Field(
        ...,
        description="Why is the data sufficient or insufficient?"
    )

    replan_instructions: Optional[str] = Field(
        None,
        description="If replanning, what additional information is needed?"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the available data (0-1)"
    )
