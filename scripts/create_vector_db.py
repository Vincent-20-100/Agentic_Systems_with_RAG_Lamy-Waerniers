"""
Build ChromaDB vector embeddings from SQL databases.

Usage:
    python scripts/create_vector_db.py

Run from the project root directory.
Input:  data/databases/*.db
Output: data/vector_database/

Requires OPENAI_API_KEY in .env
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from dotenv import load_dotenv
load_dotenv()

from embedding import build_movie_embeddings

DB_FOLDER = str(PROJECT_ROOT / "data" / "databases")
VECTOR_DB_FOLDER = str(PROJECT_ROOT / "data" / "vector_database")

if __name__ == "__main__":
    print("Building vector embeddings...\n")
    stats = build_movie_embeddings(
        db_folder=DB_FOLDER,
        chroma_path=VECTOR_DB_FOLDER,
        force_rebuild=True,
        batch_size=100,
    )
    print(f"\nDone: {stats}")
