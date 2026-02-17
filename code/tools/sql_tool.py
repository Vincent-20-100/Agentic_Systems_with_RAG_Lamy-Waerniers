"""
SQL tool - async wrapper for database queries
"""
import asyncio
import json
import sqlite3
from langchain_core.tools import tool


@tool
def execute_sql_query(query: str, db_name: str, state_catalog: dict) -> str:
    """Execute SQL query"""
    catalog = state_catalog

    if db_name not in catalog["databases"]:
        return json.dumps({"error": f"Database '{db_name}' not found"})

    db_info = catalog["databases"][db_name]

    if "error" in db_info:
        return json.dumps({"error": db_info["error"]})

    db_path = db_info["full_path"]

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result = [dict(zip(columns, row)) for row in rows]
        conn.close()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": f"SQL Error: {str(e)}"})


async def execute_sql_async(query: str, db_name: str, catalog: dict) -> dict:
    """
    Execute SQL query asynchronously

    Uses asyncio.to_thread() to run sync tool in thread pool
    (True async with aiopg/asyncpg can be future optimization)

    Returns dict with results or error
    """
    try:
        # Run sync tool in thread pool
        result_json = await asyncio.to_thread(
            execute_sql_query.invoke,
            {
                "query": query,
                "db_name": db_name,
                "state_catalog": catalog
            }
        )

        # Parse JSON result
        result = json.loads(result_json)

        return {
            "results": result if not isinstance(result, dict) or "error" not in result else [],
            "error": result.get("error") if isinstance(result, dict) else None,
            "row_count": len(result) if isinstance(result, list) else 0
        }
    except Exception as e:
        return {
            "results": [],
            "error": f"SQL execution failed: {str(e)}",
            "row_count": 0
        }
