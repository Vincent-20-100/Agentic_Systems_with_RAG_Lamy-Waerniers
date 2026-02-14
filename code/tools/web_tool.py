"""
Web search tool - async wrapper for DuckDuckGo
"""
import asyncio
import json
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults


@tool
def web_search(query: str, num_results: int = 5) -> str:
    """Web search via DuckDuckGo"""
    try:
        search = DuckDuckGoSearchResults(num_results=num_results)
        return search.run(query)
    except Exception as e:
        return json.dumps({"error": str(e)})


async def execute_web_async(query: str, n_results: int = 5) -> dict:
    """Execute web search asynchronously"""
    try:
        result_json = await asyncio.to_thread(
            web_search.invoke,
            {
                "query": query,
                "num_results": n_results
            }
        )

        # web_search returns string, might be JSON or plain text
        try:
            result = json.loads(result_json)
        except:
            result = result_json  # Keep as string

        return {
            "results": result,
            "error": None
        }
    except Exception as e:
        return {
            "results": [],
            "error": f"Web search failed: {str(e)}"
        }
