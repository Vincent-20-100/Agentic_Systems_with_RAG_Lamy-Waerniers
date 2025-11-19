# =================================
# ========== CONFIGURATION =========
# =================================
import os
import pathlib
from langchain_openai import ChatOpenAI

# =============================================================================
# API KEYS LOADING — 2025-PROOF (local + Streamlit Cloud)
# =============================================================================

def load_api_keys():
    """
    Loads API keys safely:
    - On Streamlit Community Cloud → reads st.secrets
    - Locally → reads .env file
    Never imports streamlit at import time → no more startup crashes
    """
    # Detect Streamlit Cloud environment
    is_streamlit_cloud = (
        os.getenv("STREAMLIT_SHARING_MODE") or
        "streamlit.io" in os.getenv("SERVER_NAME", "") or
        os.getenv("STREAMLIT_CLOUD") == "true"
    )

    if is_streamlit_cloud:
        import streamlit as st
        openai_key = st.secrets.get("OPENAI_API_KEY")
        omdb_key   = st.secrets.get("OMDB_API_KEY")
    else:
        # Local development
        from dotenv import load_dotenv
        load_dotenv()
        openai_key = os.getenv("OPENAI_API_KEY")
        omdb_key   = os.getenv("OMDB_API_KEY")

    return openai_key, omdb_key


# Load keys at import time
OPENAI_API_KEY, OMDB_API_KEY = load_api_keys()

# =============================================================================
# IMMEDIATE & CLEAR VALIDATION — fails fast with helpful message
# =============================================================================

missing = []

if not OPENAI_API_KEY:
    missing.append("OPENAI_API_KEY")

if not OMDB_API_KEY:
    missing.append("OMDB_API_KEY")

if missing:
    raise ValueError(
        "Missing required API key(s)!\n\n"
        "Go to your Streamlit app → Settings → Secrets and add:\n\n"
        + "\n".join([f'{key} = "your_key_here"' for key in missing]) +
        "\n\n"
        "Example:\n"
        '[secrets]\n'
        'OPENAI_API_KEY = "sk-proj-..."\n'
        'OMDB_API_KEY = "12345678"'
    )

# =============================================================================
# CONSTANTS & PATHS
# =============================================================================

OMDB_BASE_URL = "http://www.omdbapi.com/"

CURRENT_FILE = pathlib.Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
DB_FOLDER_PATH = str(PROJECT_ROOT / "data" / "databases")
CHROMA_PATH    = str(PROJECT_ROOT / "data" / "vector_database")

# =============================================================================
# LLM INSTANCE
# =============================================================================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=OPENAI_API_KEY,
    max_tokens=4000,
)