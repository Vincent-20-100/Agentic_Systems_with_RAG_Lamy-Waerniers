"""
Embedding Manager for Movie Database
Creates and queries ChromaDB embeddings with OpenAI
"""
import os
import sqlite3
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment")

# === HELPER FUNCTIONS ===

def generate_unique_id(table_name: str, index: int) -> str:
    """
    Generate unique ID from table name and index

    Examples:
        amazon_prime_titles, 0 -> ama0000
        netflix_titles, 42 -> net0042
        disney_plus_titles, 1234 -> dis1234
    """
    # Extract first 3 characters of table name
    prefix = table_name[:3].lower()
    # Format index with leading zeros (4 digits)
    id_str = f"{prefix}{index:04d}"
    return id_str

def extract_movies_from_databases(db_folder: str) -> List[Dict]:
    """
    Extract all movies/shows from all SQLite databases

    Returns:
        List of dicts with: database, table, title, description
    """
    all_data = []
    db_folder = Path(db_folder)

    if not db_folder.exists():
        raise FileNotFoundError(f"Database folder not found: {db_folder}")

    db_files = list(db_folder.glob("*.db")) + list(db_folder.glob("*.sqlite")) + list(db_folder.glob("*.sqlite3"))

    if not db_files:
        raise ValueError(f"No database files found in {db_folder}")

    print(f"📁 Scanning {len(db_files)} database(s)...")

    for db_path in db_files:
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            print(f"\n📁 Database: {db_path.name}")

            for (table_name,) in tables:
                # Get column names
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [col[1] for col in cursor.fetchall()]

                # Find title and description columns
                title_col = None
                desc_col = None

                for col in ['title', 'Title', 'name', 'Name']:
                    if col in columns:
                        title_col = col
                        break

                for col in ['description', 'Description', 'plot', 'Plot', 'summary']:
                    if col in columns:
                        desc_col = col
                        break

                if title_col and desc_col:
                    # Get distinct title + description
                    cursor.execute(f"SELECT DISTINCT {title_col}, {desc_col} FROM {table_name} WHERE {title_col} IS NOT NULL AND {desc_col} IS NOT NULL;")
                    results = cursor.fetchall()

                    print(f"  📋 Table: {table_name} - {len(results)} entries")

                    for title, description in results:
                        all_data.append({
                            "database": db_path.name,
                            "table": table_name,
                            "title": str(title),
                            "description": str(description)
                        })
                else:
                    if not title_col:
                        print(f"  ⚠️ Table: {table_name} - No title column found")
                    elif not desc_col:
                        print(f"  ⚠️ Table: {table_name} - No description column found")

            conn.close()

        except Exception as e:
            print(f"  ❌ Error reading {db_path.name}: {str(e)}")

    print(f"\n✅ Total: {len(all_data)} movies/shows extracted")
    return all_data

# === EMBEDDING FUNCTIONS ===

def get_or_create_collection(
    chroma_path: str,
    collection_name: str = "movie_descriptions",
    embedding_model: str = "text-embedding-3-small"
) -> chromadb.Collection:
    """
    Get or create ChromaDB collection with OpenAI embeddings

    Args:
        chroma_path: Path to ChromaDB persistent storage
        collection_name: Name of the collection
        embedding_model: OpenAI embedding model name

    Returns:
        ChromaDB collection
    """
    os.makedirs(chroma_path, exist_ok=True)

    # Create ChromaDB client
    client = chromadb.PersistentClient(path=chroma_path)

    # Create OpenAI embedding function
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=embedding_model
    )

    # Get or create collection
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=openai_ef
    )

    return collection

def embed_movies_if_not_exists(
    collection: chromadb.Collection,
    movies: List[Dict],
    batch_size: int = 100,
    force_rebuild: bool = False
) -> Dict:
    """
    Embed movies in ChromaDB - ONLY if they don't exist yet

    Args:
        collection: ChromaDB collection
        movies: List of movie dicts (database, table, title, description)
        batch_size: Number of movies to embed per batch
        force_rebuild: If True, delete existing collection and rebuild

    Returns:
        Dict with stats: total, added, skipped, errors
    """
    stats = {
        "total": len(movies),
        "added": 0,
        "skipped": 0,
        "errors": 0
    }

    # If force rebuild, delete all existing
    if force_rebuild:
        try:
            existing_count = collection.count()
            if existing_count > 0:
                print(f"🗑️ Force rebuild: deleting {existing_count} existing embeddings...")
                # Get all IDs and delete
                all_ids = collection.get()['ids']
                if all_ids:
                    collection.delete(ids=all_ids)
                print(f"✅ Deleted {len(all_ids)} embeddings")
        except Exception as e:
            print(f"⚠️ Error during force rebuild: {str(e)}")

    # Get existing IDs
    try:
        existing_ids = set(collection.get()['ids'])
        print(f"📊 Found {len(existing_ids)} existing embeddings")
    except:
        existing_ids = set()
        print(f"📊 Collection is empty")

    # Group movies by table for ID generation
    table_counters = {}
    movies_to_add = []

    for idx, movie in enumerate(movies):
        table_name = movie['table']

        # Initialize counter for this table
        if table_name not in table_counters:
            table_counters[table_name] = 0

        # Generate unique ID
        unique_id = generate_unique_id(table_name, table_counters[table_name])
        table_counters[table_name] += 1

        # Check if already exists
        if unique_id in existing_ids:
            stats['skipped'] += 1
            continue

        # Add to batch
        movies_to_add.append({
            "id": unique_id,
            "document": movie['description'],
            "metadata": {
                "title": movie['title'],
                "database": movie['database'],
                "table": movie['table']
            }
        })

    print(f"\n🔄 Processing {len(movies_to_add)} new movies in batches of {batch_size}...")

    # Process in batches
    for i in range(0, len(movies_to_add), batch_size):
        batch = movies_to_add[i:i + batch_size]

        try:
            collection.add(
                documents=[m['document'] for m in batch],
                metadatas=[m['metadata'] for m in batch],
                ids=[m['id'] for m in batch]
            )
            stats['added'] += len(batch)
            print(f"  ✅ Batch {i // batch_size + 1}: Added {len(batch)} movies (total: {stats['added']}/{len(movies_to_add)})")

        except Exception as e:
            stats['errors'] += len(batch)
            print(f"  ❌ Batch {i // batch_size + 1}: Error - {str(e)}")

    print(f"\n📊 Embedding completed:")
    print(f"  - Total movies: {stats['total']}")
    print(f"  - Added: {stats['added']}")
    print(f"  - Skipped (already exists): {stats['skipped']}")
    print(f"  - Errors: {stats['errors']}")

    return stats

# === QUERY FUNCTIONS ===

def query_movies(
    collection: chromadb.Collection,
    query_text: str,
    n_results: int = 5,
    where_filter: Optional[Dict] = None
) -> List[Dict]:
    """
    Query movies by semantic similarity

    Args:
        collection: ChromaDB collection
        query_text: Search query (will be embedded)
        n_results: Number of results to return
        where_filter: Optional metadata filter (e.g., {"table": "netflix_titles"})

    Returns:
        List of dicts with: id, title, description, database, table, distance
    """
    try:
        # Query collection
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter
        )

        # Format results
        formatted_results = []

        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "id": results['ids'][0][i],
                "title": results['metadatas'][0][i]['title'],
                "description": results['documents'][0][i],
                "database": results['metadatas'][0][i]['database'],
                "table": results['metadatas'][0][i]['table'],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })

        return formatted_results

    except Exception as e:
        print(f"❌ Query error: {str(e)}")
        return []

def get_movie_by_id(collection: chromadb.Collection, movie_id: str) -> Optional[Dict]:
    """
    Get a specific movie by its unique ID

    Args:
        collection: ChromaDB collection
        movie_id: Unique movie ID (e.g., "net0042")

    Returns:
        Dict with movie info or None if not found
    """
    try:
        results = collection.get(ids=[movie_id])

        if results['ids']:
            return {
                "id": results['ids'][0],
                "title": results['metadatas'][0]['title'],
                "description": results['documents'][0],
                "database": results['metadatas'][0]['database'],
                "table": results['metadatas'][0]['table']
            }
        else:
            return None

    except Exception as e:
        print(f"❌ Error getting movie {movie_id}: {str(e)}")
        return None

# === MAIN WORKFLOW ===

def build_movie_embeddings(
    db_folder: str,
    chroma_path: str,
    force_rebuild: bool = False,
    batch_size: int = 100
) -> Dict:
    """
    Complete workflow: Extract movies from SQL databases and embed them

    Args:
        db_folder: Path to folder with SQLite databases
        chroma_path: Path to ChromaDB storage
        force_rebuild: If True, rebuild all embeddings
        batch_size: Batch size for embedding

    Returns:
        Dict with stats
    """
    print("=" * 60)
    print("🎬 MOVIE EMBEDDING BUILDER")
    print("=" * 60)

    # Step 1: Extract movies
    print("\n📥 Step 1: Extracting movies from databases...")
    movies = extract_movies_from_databases(db_folder)

    # Step 2: Get or create collection
    print(f"\n🗄️ Step 2: Initializing ChromaDB...")
    collection = get_or_create_collection(chroma_path)
    print(f"✅ Collection: {collection.name}")
    print(f"   Count: {collection.count()} embeddings")

    # Step 3: Embed movies
    print(f"\n🔮 Step 3: Creating embeddings...")
    stats = embed_movies_if_not_exists(
        collection=collection,
        movies=movies,
        batch_size=batch_size,
        force_rebuild=force_rebuild
    )

    print("\n" + "=" * 60)
    print("✅ EMBEDDING BUILD COMPLETE")
    print("=" * 60)

    return stats

# === EXAMPLE USAGE ===

if __name__ == "__main__":
    # Configuration
    DB_FOLDER = r"C:\Users\Vincent\GitHub\Vincent-20-100\Agentic_Systems_Project_Vlamy\data\databases"
    CHROMA_PATH = r"C:\Users\Vincent\GitHub\Vincent-20-100\Agentic_Systems_Project_Vlamy\data\vector_database"

    # Build embeddings
    stats = build_movie_embeddings(
        db_folder=DB_FOLDER,
        chroma_path=CHROMA_PATH,
        force_rebuild=False,  # Set to True to rebuild everything
        batch_size=100
    )

    # Test query
    print("\n" + "=" * 60)
    print("🔍 TESTING QUERY")
    print("=" * 60)

    collection = get_or_create_collection(CHROMA_PATH)

    # Example query
    results = query_movies(
        collection=collection,
        query_text="action movie with explosions and car chases",
        n_results=5
    )

    print(f"\n🎬 Top 5 results for: 'action movie with explosions'")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   📁 {result['database']} / {result['table']}")
        print(f"   🆔 {result['id']}")
        print(f"   📝 {result['description'][:100]}...")
        if result['distance']:
            print(f"   📊 Distance: {result['distance']:.4f}")
