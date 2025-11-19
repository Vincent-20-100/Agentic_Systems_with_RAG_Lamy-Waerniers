import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
# =================================
from utils import build_db_catalog
from agent import app
from config import OPENAI_API_KEY, DB_FOLDER_PATH


# Configuration
st.set_page_config(page_title="Albert query", page_icon="🧙‍♂️", layout="wide")


if not OPENAI_API_KEY:
    st.error("❌ OPENAI_API_KEY missing")
    st.stop()


# === STREAMLIT INTERFACE ===

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "agent_messages" not in st.session_state:
    st.session_state.agent_messages = []

if "db_catalog" not in st.session_state:
    catalog = build_db_catalog(DB_FOLDER_PATH)
    st.session_state.db_catalog = catalog
    
    # Welcome message
    if catalog.get("error"):
        welcome = f"❌ Error: {catalog['error']}"
    else:
        # Welcome message
        welcome = "##### 👋 **Salut, moi c'est Albert Query** 🧙‍♂️\n\n"
        welcome += "##### Je suis là pour t'aider à explorer tes bases de données !\n\n"
        welcome += "\n\n"
        welcome += "**Bases de données disponibles:**\n\n"
        for db_name, db_info in catalog["databases"].items():
                if "error" not in db_info:
                        welcome += f" {db_name} -\n"
        welcome += "**Outils disponibles**: Requête SQL / Recherche sémantique / API OMDB / Recherche Web\n\n"
        welcome += "**Demande-moi quelque chose pour commencer !**\n\n"
        welcome += "Par exemple :\n"
        welcome += "- Quelles tables et colonnes sont disponibles dans les bases de données ?\n"
        welcome += "- Combien de genres différents sont disponibles ?\n"
        welcome += "- Montre moi l'affiche de Gladiator de Ridley Scott.\n"
        welcome += "- Propose-moi des films d'anquêtes aux ambiances sombre beacoup de suspens. (semantic search).\n"
        
    st.session_state.chat_messages.append({"role": "assistant", "content": welcome})

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "session_1"

# Display chat
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Display sources if available
        if "sources" in msg and msg["sources"]:
            st.markdown("---")
            st.caption("📚 Sources utilisées:")
            cols = st.columns(len(msg["sources"]))
            for idx, source in enumerate(msg["sources"]):
                with cols[idx]:
                    if source.get("type") == "database":
                        st.markdown(f"🗄️ Base de donnée SQL :{source['name']}")
                        if "details" in source:
                            st.caption(source["details"])
                    elif source.get("type") == "semantic":
                        st.markdown(f"🔍 Base de donnée vectorielle :{source['name']}")
                        if "details" in source:
                            st.caption(source["details"])
                    elif source.get("type") == "omdb":
                        if source.get("url"):
                            st.markdown(f"🎬 IMDB [{source['name']}]({source['url']})")
                        else:
                            st.markdown(f"🎬 API OMDB {source['name']}")
                    elif source.get("type") == "web":
                        if source.get("url"):
                            st.markdown(f"🌐 [Recherche Web]({source['url']})")
                        else:
                            st.markdown(f"🌐 Recherche Web")

# User input
if prompt := st.chat_input("Your question..."):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    st.session_state.agent_messages.append(HumanMessage(content=prompt))
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        status = st.empty()
        response_placeholder = st.empty()
        
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
        
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        
        result = None
        for step in app.stream(inputs, config=config, stream_mode="values"):
            result = step
            current = step.get("current_step", "")
            
            if current == "planned":
                status.info("🧠 Albert réfléchit...")
            elif current == "sql_executed":
                status.info("💾 Albert interroge la base de données SQL...")
            elif current == "semantic_executed":
                status.info("🔍 Albert effectue une recherche sémantique... (RAG)")
            elif current == "omdb_executed":
                status.info("🎬 Albert interroge l'API OMDB...")
            elif current == "web_executed":
                status.info("🌐 Albert recherche sur le web...")
            elif current == "complete":
                status.success("✅ Terminé !")
        
        if result:
            status.empty()

            final_msgs = [m for m in result.get("messages", []) if isinstance(m, AIMessage)]
            if final_msgs:
                response = final_msgs[-1].content
                response_placeholder.markdown(response)

                # Get detailed sources
                sources_detailed = result.get("sources_detailed", [])

                # Display sources below response
                if sources_detailed:
                    st.markdown("---")
                    st.caption("📚 Sources utilisées:")
                    cols = st.columns(len(sources_detailed))
                    for idx, source in enumerate(sources_detailed):
                        with cols[idx]:
                            if source.get("type") == "database":
                                st.markdown(f"🗄️ Base de donnée SQL :{source['name']}")
                                if "details" in source:
                                    st.caption(source["details"])
                            elif source.get("type") == "semantic":
                                st.markdown(f"🔍 Base de donnée vectorielle :{source['name']}")
                                if "details" in source:
                                    st.caption(source["details"])
                            elif source.get("type") == "omdb":
                                if source.get("url"):
                                    st.markdown(f"🎬 IMDB [{source['name']}]({source['url']})")
                                else:
                                    st.markdown(f"🎬 API OMDB {source['name']}")
                            elif source.get("type") == "web":
                                if source.get("url"):
                                    st.markdown(f"🌐 [Recherche Web]({source['url']})")
                                else:
                                    st.markdown(f"🌐 Recherche Web")

                # Save message with sources
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": response,
                    "sources": sources_detailed
                })

                # Keep last user + assistant in agent messages
                user_msgs = [m for m in result["messages"] if isinstance(m, HumanMessage)]
                if user_msgs:
                    st.session_state.agent_messages = [user_msgs[-1], final_msgs[-1]]