"""
OMDB API tool - async wrapper for movie metadata
"""
import asyncio
import json
import requests
from langchain_core.tools import tool
from config import OMDB_API_KEY, OMDB_BASE_URL


@tool
def omdb_api(by: str = "title", t: str = None, plot: str = "full") -> str:
    """Query OMDb API"""
    if not OMDB_API_KEY:
        return json.dumps({"error": "OMDB_API_KEY missing"})

    params = {"apikey": OMDB_API_KEY, "plot": plot}

    if by == "title" and t:
        params["t"] = t
    else:
        return json.dumps({"error": "Title required"})

    try:
        response = requests.get(OMDB_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return json.dumps({"error": str(e)})


async def execute_omdb_async(title: str) -> dict:
    """Execute OMDB API call asynchronously"""
    try:
        result_json = await asyncio.to_thread(
            omdb_api.invoke,
            {
                "by": "title",
                "t": title,
                "plot": "full"
            }
        )

        result = json.loads(result_json)

        if isinstance(result, dict) and result.get("Response") == "False":
            return {
                "data": None,
                "error": result.get("Error", "Movie not found")
            }

        return {
            "data": result,
            "error": None
        }
    except Exception as e:
        return {
            "data": None,
            "error": f"OMDB API failed: {str(e)}"
        }
