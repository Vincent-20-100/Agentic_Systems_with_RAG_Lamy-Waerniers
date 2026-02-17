"""
Semantic search tool - async wrapper for vector search
"""
import asyncio
import json
import os
import chromadb
from chromadb.utils import embedding_functions
from langchain_core.tools import tool
from config import OPENAI_API_KEY, CHROMA_PATH


@tool
def semantic_search(query: str, n_results: int = 5, table_filter: str = None) -> str:
    """Execute semantic search on movie embeddings.

      This tool searches movie descriptions using AI embeddings for semantic similarity.
      ALL MOVIE DESCRIPTIONS ARE IN ENGLISH - query must be in English!

      Two query strategies:
      1. KEYWORD approach: Single word or short phrase (e.g., "romance", "space adventure", "heist")
         → Good for finding movies by genre/theme

      2. DESCRIPTIVE approach: Full sentence describing plot/content
         (e.g., "A detective investigating a murder in a small town",
               "Two friends on a road trip across America")
         → Good for finding movies with similar plots/stories

      Args:
          query: English query - either keyword or descriptive sentence
          n_results: Number of similar movies to return (default 5, max 10)
          table_filter: Optional table name filter (e.g., "netflix_titles")

      Returns:
          JSON with similar movies: id, title, description, database, table, similarity_score"""
    try:
        # Get or create ChromaDB collection
        os.makedirs(CHROMA_PATH, exist_ok=True)
        client = chromadb.PersistentClient(path=CHROMA_PATH)

        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=OPENAI_API_KEY,
            model_name="text-embedding-3-small"
        )

        collection = client.get_or_create_collection(
            name="movie_descriptions",
            embedding_function=openai_ef
        )

        # Build filter if specified
        where_filter = None
        if table_filter:
            where_filter = {"table": table_filter}

        # Query collection
        results = collection.query(
              query_texts=[query],
              n_results=n_results,
              where=where_filter
          )

          # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "title": results['metadatas'][0][i].get('title', 'Unknown'),
                    "description": results['documents'][0][i],
                    "database": results['metadatas'][0][i].get('database', 'unknown'),
                    "table": results['metadatas'][0][i].get('table', 'unknown'),
                    "similarity_score": 1 - results['distances'][0][i] if 'distances' in results else None
                })

        return json.dumps(formatted_results, indent=2, default=str)

    except Exception as e:
        return json.dumps({"error": f"Semantic search error: {str(e)}"})


async def execute_semantic_async(query: str, n_results: int = 5) -> dict:
    """
    Execute semantic search asynchronously

    Returns dict with results or error
    """
    try:
        # Run sync tool in thread pool
        result_json = await asyncio.to_thread(
            semantic_search.invoke,
            {
                "query": query,
                "n_results": n_results
            }
        )

        # Parse JSON result
        result = json.loads(result_json)

        if isinstance(result, dict) and "error" in result:
            return {
                "results": [],
                "error": result["error"]
            }

        return {
            "results": result if isinstance(result, list) else [],
            "error": None
        }
    except Exception as e:
        return {
            "results": [],
            "error": f"Semantic search failed: {str(e)}"
        }
