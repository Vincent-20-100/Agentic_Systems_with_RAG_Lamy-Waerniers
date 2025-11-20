import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
import time

from utils import build_db_catalog
from agent import app
from config import OPENAI_API_KEY, DB_FOLDER_PATH
from langfuse.langchain import CallbackHandler
 
langfuse_handler = CallbackHandler()

# =================================
# Configuration
# =================================
st.set_page_config(
    page_title="Albert Query",
    page_icon="🧙‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS 
st.markdown("""
    <style>
    [data-testid="stMainBlockContainer"] {
        padding-top: 1rem;
    }
    .main-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 2rem;
        padding: 1.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        color: white;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
    }
    .info-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin-bottom: 0.5rem;
    }
    .source-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-right: 0.5rem;
        margin-bottom: 0.3rem;
    }
    .db-badge {
        background: #e8f5e9;
        color: #2e7d32;
    }
    .semantic-badge {
        background: #e3f2fd;
        color: #1565c0;
    }
    .omdb-badge {
        background: #fff3e0;
        color: #e65100;
    }
    .web-badge {
        background: #f3e5f5;
        color: #6a1b9a;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        line-height: 1.6;
    }
    .assistant-message {
        background: #f0f2f6;
        border-left: 4px solid #667eea;
    }
    .user-message {
        background: #e8eaf6;
        border-left: 4px solid #764ba2;
    }

    /* Animations de chargement */
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.05); }
    }

    @keyframes dots {
        0%, 20% { content: '.'; }
        40% { content: '..'; }
        60%, 100% { content: '...'; }
    }

    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes glow {
        0%, 100% { box-shadow: 0 0 5px rgba(102, 126, 234, 0.5); }
        50% { box-shadow: 0 0 20px rgba(102, 126, 234, 0.8); }
    }

    /* Conteneur de statut animé */
    .albert-status {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1.5rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 12px;
        border-left: 5px solid #667eea;
        animation: slideInLeft 0.5s ease-out, glow 2s ease-in-out infinite;
        margin-bottom: 1rem;
    }

    .albert-status-icon {
        font-size: 2.5rem;
        animation: pulse 1.5s ease-in-out infinite;
    }

    .albert-status-text {
        flex: 1;
        font-size: 1.1rem;
        font-weight: 500;
        color: #2d3748;
    }

    .albert-spinner {
        width: 30px;
        height: 30px;
        border: 3px solid rgba(102, 126, 234, 0.3);
        border-top: 3px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    /* Dots animés */
    .loading-dots::after {
        content: '...';
        animation: dots 1.5s steps(3, end) infinite;
    }

    /* Style pour les différents types de statut */
    .status-thinking {
        border-left-color: #d946ef;
        background: linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%);
    }

    .status-sql {
        border-left-color: #7c3aed;
        background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
    }

    .status-semantic {
        border-left-color: #0ea5e9;
        background: linear-gradient(135deg, #e0f2fe 0%, #cffafe 100%);
    }

    .status-omdb {
        border-left-color: #a855f7;
        background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
    }

    .status-web {
        border-left-color: #6b7280;
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
    }        

    .status-complete {
        border-left-color: #2e7d32;
        background: linear-gradient(135deg, #e8f5e9 0%, #a5d6a7 100%);
        animation: slideInLeft 0.5s ease-out;
    }
    </style>
""", unsafe_allow_html=True)

# Vérifier la clé API
if not OPENAI_API_KEY:
    st.error("❌ OPENAI_API_KEY manquante")
    st.stop()

# =================================
# Initialisation Session State
# =================================
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "agent_messages" not in st.session_state:
    st.session_state.agent_messages = []

if "db_catalog" not in st.session_state:
    with st.spinner("⏳ Chargement des bases de données..."):
        catalog = build_db_catalog(DB_FOLDER_PATH)
        st.session_state.db_catalog = catalog

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "session_1"

# =================================
# Header
# =================================
st.markdown("""
    <div class="main-header">
        <div style="font-size: 80px; line-height: 1;">🧙‍♂️</div>
        <div>
            <h1>Albert Query</h1>
            <p style="margin: 0; opacity: 0.9;">Ton assistant intelligent pour explorer tes bases de données</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# =================================
# Sidebar - Infos et Paramètres
# =================================
with st.sidebar:

    catalog = st.session_state.db_catalog

    if catalog.get("error"):
        st.error(f"❌ {catalog['error']}")
    else:
        with st.expander("#### 🗄️ Bases de données disponibles", expanded=False):
            for db_name, db_info in catalog["databases"].items():
                if "error" not in db_info:
                    with st.expander(f"📊 {db_name}"):
                        # Afficher les tables avec leurs colonnes
                        tables = db_info.get("tables", {})
                        for table_name, table_info in tables.items():
                            with st.expander(f"{table_name}"):
                                row_count = table_info.get("row_count", "?")
                                st.caption(f"**Lignes:** {row_count}")

                                st.markdown("**Colonnes:**")
                                for col in table_info.get("columns", []):
                                    col_name = col["name"]
                                    col_type = col["type"]
                                    pk_icon = "🔑" if col.get("primary_key", False) else ""
                                    st.caption(f"{pk_icon} {col_name} ({col_type})")

        with st.expander("#### 🛠️ Outils disponibles", expanded=False):
                tools = [
                    ("🗄️", "Requête SQL", "Interroger directement les bases de données"),
                    ("🔍", "Recherche sémantique", "Recherche intelligente par similarité (RAG)"),
                    ("🎬", "API OMDB", "Informations sur les films"),
                    ("🌐", "Recherche Web", "Recherche sur internet")
                ]

                for icon, name, desc in tools:
                    st.markdown(f"**{icon} {name}**  \n*{desc}*")

        st.markdown("#### 💡 Exemples de questions")
        examples = [
            "Combien de genres de films y a-t-il dans nos bases de données ?",
            "Montre moi l'affiche de  Ex Machina.",
            "Propose des films d'enquêtes avec une ambiance sombre et une intrigue à suspense.",
        ]
        for idx, example in enumerate(examples, 1):
            st.caption(f"{idx}. {example}")

# =================================
# Chat Display
# =================================
st.markdown("### 💬 Conversation")

# Conteneur pour les messages avec scroll
chat_container = st.container()

with chat_container:
    # Premier message de bienvenue
    if len(st.session_state.chat_messages) == 0:
        with st.chat_message("assistant", avatar="🧙‍♂️"):
            st.markdown("""
            **Salut ! 👋 Moi c'est Albert Query**

            Je suis là pour t'aider à explorer tes bases de données de façon intelligente.

            Pose-moi une question pour commencer !
            """)
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": "Message de bienvenue",
            "is_welcome": True
        })

    # Afficher l'historique des messages
    for msg in st.session_state.chat_messages:
        if msg.get("is_welcome"):
            continue

        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🧙‍♂️"):
                st.markdown(msg["content"])

                # Afficher les sources si disponibles
                if "sources" in msg and msg["sources"]:
                    st.divider()
                    st.caption("📚 **Sources utilisées:**")

                    cols = st.columns(min(3, len(msg["sources"])))
                    for idx, source in enumerate(msg["sources"]):
                        with cols[idx % 3]:
                            source_type = source.get("type", "")

                            if source_type == "database":
                                st.markdown(f"""
                                    <div class="source-badge db-badge">
                                    🗄️ Base SQL: {source['name']}
                                    </div>
                                """, unsafe_allow_html=True)
                                if "details" in source:
                                    st.caption(source["details"])

                            elif source_type == "semantic":
                                st.markdown(f"""
                                    <div class="source-badge semantic-badge">
                                    🔍 Vectorielle: {source['name']}
                                    </div>
                                """, unsafe_allow_html=True)
                                if "details" in source:
                                    st.caption(source["details"])

                            elif source_type == "omdb":
                                url = source.get("url", "")
                                if url:
                                    st.markdown(f"""
                                        <div class="source-badge omdb-badge">
                                        🎬 <a href="{url}" target="_blank">{source['name']}</a>
                                        </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown(f"""
                                        <div class="source-badge omdb-badge">
                                        🎬 OMDB: {source['name']}
                                        </div>
                                    """, unsafe_allow_html=True)

                            elif source_type == "web":
                                url = source.get("url", "")
                                if url:
                                    st.markdown(f"""
                                        <div class="source-badge web-badge">
                                        🌐 <a href="{url}" target="_blank">Web</a>
                                        </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown(f"""
                                        <div class="source-badge web-badge">
                                        🌐 Recherche Web
                                        </div>
                                    """, unsafe_allow_html=True)

        else:  # User message
            with st.chat_message("user", avatar="🥸"):
                st.markdown(msg["content"])

# =================================
# User Input & Processing
# =================================
if prompt := st.chat_input("Pose-moi une question sur tes données... 💬"):

    # Ajouter le message utilisateur
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    st.session_state.agent_messages.append(HumanMessage(content=prompt))

    # Afficher le message utilisateur
    with st.chat_message("user", avatar="🧐"):
        st.markdown(prompt)

    # Traitement par l'agent avec animations
    with st.chat_message("assistant", avatar="🧙‍♂️"):
        status = st.empty()
        response_placeholder = st.empty()
        sources_placeholder = st.empty()

        inputs = {
            "messages": st.session_state.agent_messages,
            "db_catalog": st.session_state.db_catalog,
            "original_question": prompt,
            "resolved_query": "",
            "planning_reasoning": "",
            "sql_query": "",
            "semantic_query": "",
            "omdb_query": "",
            "web_query": "",
            "needs_sql": False,
            "needs_semantic": False,
            "needs_omdb": False,
            "needs_web": False,
            "sql_result": "[]",
            "semantic_result": "[]",
            "omdb_result": "{}",
            "web_result": "{}",
            "sources_used": [],
            "sources_detailed": [],
            "current_step": ""
        }

        config = {"thread_id": st.session_state.thread_id,
                  "callbacks": [langfuse_handler]}

        result = None
        for step in app.stream(inputs, config=config, stream_mode="values"):
            result = step
            current = step.get("current_step", "")

            if current == "planned":
                status.markdown("""
                    <div class="albert-status status-thinking">
                        <div class="albert-status-icon">🧠</div>
                        <div class="albert-status-text">Albert réfléchit à ta question<span class="loading-dots"></span></div>
                        <div class="albert-spinner"></div>
                    </div>
                """, unsafe_allow_html=True)
            elif current == "sql_executed":
                status.markdown("""
                    <div class="albert-status status-sql">
                        <div class="albert-status-icon">🗄️</div>
                        <div class="albert-status-text">Albert interroge la base de données SQL<span class="loading-dots"></span></div>
                        <div class="albert-spinner"></div>
                    </div>
                """, unsafe_allow_html=True)
            elif current == "semantic_executed":
                status.markdown("""
                    <div class="albert-status status-semantic">
                        <div class="albert-status-icon">🔍</div>
                        <div class="albert-status-text">Albert effectue une recherche sémantique (RAG)<span class="loading-dots"></span></div>
                        <div class="albert-spinner"></div>
                    </div>
                """, unsafe_allow_html=True)
            elif current == "omdb_executed":
                status.markdown("""
                    <div class="albert-status status-omdb">
                        <div class="albert-status-icon">🎬</div>
                        <div class="albert-status-text">Albert interroge OMDB<span class="loading-dots"></span></div>
                        <div class="albert-spinner"></div>
                    </div>
                """, unsafe_allow_html=True)
            elif current == "web_executed":
                status.markdown("""
                    <div class="albert-status status-web">
                        <div class="albert-status-icon">🌐</div>
                        <div class="albert-status-text">Albert recherche sur le web<span class="loading-dots"></span></div>
                        <div class="albert-spinner"></div>
                    </div>
                """, unsafe_allow_html=True)
            elif current == "complete":
                status.markdown("""
                    <div class="albert-status status-complete">
                        <div class="albert-status-icon">✅</div>
                        <div class="albert-status-text">Réponse prête !</div>
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(0.5)  # Petit délai pour voir le message "complete"

        if result:
            status.empty()

            # Extraire la réponse finale
            final_msgs = [m for m in result.get("messages", []) if isinstance(m, AIMessage)]
            if final_msgs:
                response = final_msgs[-1].content
                response_placeholder.markdown(response)

                # Afficher les sources
                sources_detailed = result.get("sources_detailed", [])
                if sources_detailed:
                    sources_placeholder.divider()
                    sources_placeholder.caption("📚 **Sources utilisées:**")

                    cols = sources_placeholder.columns(min(3, len(sources_detailed)))
                    for idx, source in enumerate(sources_detailed):
                        with cols[idx % 3]:
                            source_type = source.get("type", "")

                            if source_type == "database":
                                st.markdown(f"""
                                    <div class="source-badge db-badge">
                                    🗄️ Base SQL: {source['name']}
                                    </div>
                                """, unsafe_allow_html=True)
                                if "details" in source:
                                    st.caption(source["details"])

                            elif source_type == "semantic":
                                st.markdown(f"""
                                    <div class="source-badge semantic-badge">
                                    🔍 Vectorielle: {source['name']}
                                    </div>
                                """, unsafe_allow_html=True)
                                if "details" in source:
                                    st.caption(source["details"])

                            elif source_type == "omdb":
                                url = source.get("url", "")
                                if url:
                                    st.markdown(f"""
                                        <div class="source-badge omdb-badge">
                                        🎬 <a href="{url}" target="_blank">{source['name']}</a>
                                        </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown(f"""
                                        <div class="source-badge omdb-badge">
                                        🎬 OMDB: {source['name']}
                                        </div>
                                    """, unsafe_allow_html=True)

                            elif source_type == "web":
                                url = source.get("url", "")
                                if url:
                                    st.markdown(f"""
                                        <div class="source-badge web-badge">
                                        🌐 <a href="{url}" target="_blank">Web</a>
                                        </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown(f"""
                                        <div class="source-badge web-badge">
                                        🌐 Recherche Web
                                        </div>
                                    """, unsafe_allow_html=True)

                # Sauvegarder le message avec les sources
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": response,
                    "sources": sources_detailed
                })

                # Mettre à jour l'historique de l'agent
                user_msgs = [m for m in result["messages"] if isinstance(m, HumanMessage)]
                if user_msgs:
                    st.session_state.agent_messages = [user_msgs[-1], final_msgs[-1]]
