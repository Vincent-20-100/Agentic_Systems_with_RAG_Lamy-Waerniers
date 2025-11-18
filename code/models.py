# =================================
# ============ IMPORTS ============
# =================================
from typing import Optional, Sequence, TypedDict, Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


# =================================
# ========== AGENT STATE ==========
# =================================
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    db_catalog: dict

    # Planning
    original_question: str
    resolved_query: str
    planning_reasoning: str

    # Tool queries
    sql_query: str
    omdb_query: str
    web_query: str
    semantic_query: str

    # Tool flags
    needs_sql: bool
    needs_omdb: bool
    needs_web: bool
    needs_semantic: bool

    # Tool results
    sql_result: str
    omdb_result: str
    web_result: str
    semantic_result: str

    # Metadata
    sources_used: list
    sources_detailed: list  # Structured sources with type, name, url, etc.
    current_step: str


# =================================
# ======= STRUCTURED OUTPUTS ======
# =================================

class PlannerOutput(BaseModel):
    """Planner decision output"""
    resolved_query: str = Field(..., description="Query reformulated with context from history")
    planning_reasoning: str = Field(..., description="Why these tools are needed")
    needs_sql: bool = Field(default=False, description="Whether SQL query is needed")
    needs_omdb: bool = Field(default=False, description="Whether OMDB enrichment is needed")
    needs_web: bool = Field(default=False, description="Whether web search is needed")
    needs_semantic: bool = Field(default=False, description="Whether semantic search is needed")
    sql_query: Optional[str] = Field(None, description="Prepared SQL query if needed")
    omdb_query: Optional[str] = Field(None, description="Title to search in OMDB if needed")
    web_query: Optional[str] = Field(None, description="Web search query if needed")
    semantic_query: Optional[str] = Field(None, description="Semantic search query if needed")

class SQLOutput(BaseModel):
    """SQL execution decision"""
    can_answer: bool = Field(..., description="Whether SQL can answer the query")
    db_name: Optional[str] = Field(None, description="Database to query")
    query: Optional[str] = Field(None, description="SQL query to execute")
    reasoning: str = Field(..., description="Why this query or why SQL cannot answer")
