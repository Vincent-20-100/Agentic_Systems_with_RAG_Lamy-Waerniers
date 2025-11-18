# =================================
# ============ IMPORTS ============
# =================================

import os
import json
import sqlite3
import requests
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
import chromadb
from chromadb.utils import embedding_functions
from config import OPENAI_API_KEY, OMDB_API_KEY, OMDB_BASE_URL, CHROMA_PATH


# =================================
# ============= TOOLS =============
# =================================

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

@tool
def web_search(query: str, num_results: int = 5) -> str:
    """Web search via DuckDuckGo"""
    try:
        search = DuckDuckGoSearchResults(num_results=num_results)
        return search.run(query)
    except Exception as e:
        return json.dumps({"error": str(e)})

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
