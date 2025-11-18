# =================================
# ========== CONFIGURATION =========
# =================================
import os
import pathlib
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
OMDB_BASE_URL = "http://www.omdbapi.com/"

# Paths - Using absolute paths based on the location of this file
CURRENT_FILE = pathlib.Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
DB_FOLDER_PATH = str(PROJECT_ROOT / "data" / "databases")
CHROMA_PATH = str(PROJECT_ROOT / "data" / "vector_database")

# LLM instance
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)
