"""
OMDB API tool - async wrapper for movie metadata
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
sync_omdb_tool = _tools_module.omdb_api


async def execute_omdb_async(title: str) -> dict:
    """Execute OMDB API call asynchronously"""
    try:
        result_json = await asyncio.to_thread(
            sync_omdb_tool.invoke,
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
