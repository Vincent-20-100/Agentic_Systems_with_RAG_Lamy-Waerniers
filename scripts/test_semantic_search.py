"""
Diagnostic tool for the ChromaDB semantic search collection.

Usage:
    python scripts/test_semantic_search.py

Run from the project root directory.
Requires OPENAI_API_KEY in .env
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from dotenv import load_dotenv
load_dotenv()

import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = str(PROJECT_ROOT / "data" / "vector_database")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-small",
    )
    return client.get_or_create_collection(
        name="movie_descriptions",
        embedding_function=openai_ef,
    )


def test_query(collection, query: str, n_results: int = 5, where: dict = None):
    print(f"\n{'='*70}")
    print(f"Query: '{query}'")
    if where:
        print(f"Filter: {where}")
    print("=" * 70)

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where,
    )

    if not results["ids"] or not results["ids"][0]:
        print("No results found.")
        return

    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]
        similarity = (1 - distance) * 100
        meta = results["metadatas"][0][i]
        print(f"\n  #{i+1} {meta.get('title', 'N/A')}  ({similarity:.1f}% similarity)")
        print(f"      {meta.get('table', '')} — {results['documents'][0][i][:120]}...")


def print_stats(collection):
    count = collection.count()
    print(f"\n{'='*70}")
    print(f"Collection stats")
    print("=" * 70)
    print(f"  Documents: {count:,}")

    if count > 0:
        sample = collection.peek(limit=3)
        tables = {m.get("table") for m in sample["metadatas"]}
        print(f"  Sample tables: {sorted(tables)}")
        print(f"\n  First document:")
        print(f"    Title: {sample['metadatas'][0].get('title')}")
        print(f"    Text:  {sample['documents'][0][:100]}...")


if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("OPENAI_API_KEY not found. Check your .env file.")
        sys.exit(1)

    print(f"ChromaDB path: {CHROMA_PATH}")

    collection = get_collection()
    print_stats(collection)

    if collection.count() == 0:
        print("\nCollection is empty. Run scripts/create_vector_db.py first.")
        sys.exit(1)

    # Sample queries
    test_query(collection, "detective investigating a murder mystery")
    test_query(collection, "dark sci-fi with emotional depth")
    test_query(collection, "romantic comedy")
