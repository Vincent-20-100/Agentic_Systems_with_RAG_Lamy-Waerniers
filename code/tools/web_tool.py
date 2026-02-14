"""
Web search tool - async wrapper for DuckDuckGo
"""
import asyncio
import json
import os
import importlib.util

# Import from code/tools.py module file (not code/tools/ package)
# Due to naming conflict, we use importlib to load the specific file
_tools_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools.py")
_spec = importlib.util.spec_from_file_location("_code_tools_module", _tools_file_path)
_tools_module = importlib.util.module_from_spec(_spec)

# We need to setup the module's environment before loading
# so it can find its imports (config, etc.)
import sys
_parent_dir = os.path.dirname(os.path.dirname(__file__))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

_spec.loader.exec_module(_tools_module)
sync_web_tool = _tools_module.web_search


async def execute_web_async(query: str, n_results: int = 5) -> dict:
    """Execute web search asynchronously"""
    try:
        result_json = await asyncio.to_thread(
            sync_web_tool.invoke,
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
