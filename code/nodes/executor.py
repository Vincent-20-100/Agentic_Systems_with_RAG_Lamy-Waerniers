"""
Executor node - parallel tool execution
"""
import asyncio
from code.core.state import AgentState
from code.core.models import ExecutionPlan
from code.tools.sql_tool import execute_sql_async
from code.tools.semantic_tool import execute_semantic_async
from code.tools.omdb_tool import execute_omdb_async
from code.tools.web_tool import execute_web_async


async def executor_node(state: AgentState) -> dict:
    """
    Execute all planned tools in parallel

    No LLM call - pure orchestration
    Returns results dict with error handling per tool
    """
    plan_dict = state.get("execution_plan", {})
    plan = ExecutionPlan(**plan_dict)
    catalog = state.get("db_catalog", {})
    previous_results = state.get("previous_results", {})

    # Gather async tasks
    tasks = []
    tool_names = []

    if plan.use_sql and plan.sql_query and plan.sql_database:
        tasks.append(execute_sql_async(plan.sql_query, plan.sql_database, catalog))
        tool_names.append("sql")

    if plan.use_semantic and plan.semantic_query:
        tasks.append(execute_semantic_async(plan.semantic_query, plan.semantic_n_results))
        tool_names.append("semantic")

    if plan.use_omdb and plan.omdb_title:
        tasks.append(execute_omdb_async(plan.omdb_title))
        tool_names.append("omdb")

    if plan.use_web and plan.web_query:
        tasks.append(execute_web_async(plan.web_query, plan.web_n_results))
        tool_names.append("web")

    # Execute in parallel
    if not tasks:
        # No tools selected
        return {
            "tool_results": {},
            "previous_results": previous_results,
            "sources_used": []
        }

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build results dict
    tool_results = {}
    sources = []

    for name, result in zip(tool_names, results):
        if isinstance(result, Exception):
            tool_results[name] = {"error": str(result)}
        else:
            tool_results[name] = result
            if not result.get("error"):
                sources.append(name)

    # Merge with previous results (for loop context)
    all_results = {**previous_results, **tool_results}

    return {
        "tool_results": tool_results,
        "previous_results": all_results,
        "sources_used": sources
    }
