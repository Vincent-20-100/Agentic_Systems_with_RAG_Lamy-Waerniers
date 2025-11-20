# =================================
# ============ IMPORTS ============
# =================================

import json
from tools import execute_sql_query, web_search, omdb_api, semantic_search
from models import AgentState, PlannerOutput, SQLOutput
from config import llm
from utils import format_catalog_for_llm
from langchain_core.messages import AIMessage

# =================================
# ============= NODES =============
# =================================

def planner_node(state: AgentState) -> dict:
    """Analyze query and plan tool usage"""
    question = state.get("original_question", "")
    history = state.get("messages", [])
    catalog = state.get("db_catalog", {})
    
    catalog_info = format_catalog_for_llm(catalog)
    
    prompt = f"""You are a planning agent. Analyze the question and conversation history to decide which tools to use.

CURRENT QUESTION: "{question}"

CONVERSATION HISTORY (last 5 messages):
{json.dumps([{"role": m.type, "content": m.content} for m in history[-5:]], indent=2)}

{catalog_info}

AVAILABLE TOOLS (priority order):
1. SQL Database - Query movies/series data (titles, ratings, years, genres, cast)
    → Use for: filtering by year, rating, type, counting, aggregations
2. Semantic Search - Find movies by description/themes/plot similarity (vector search)
    → Use when: The query involves plot details, themes, or content-based recommendations
    → Use for: content-based search, "movies like X", plot descriptions, themes
    → IMPORTANT: Semantic query MUST be in English!
    → Two approaches: By KEYWORD like "romance" or by Full plot sentence like "A detective solving a mysterious murder"
3. OMDB API - Detailed info (posters, full plot, actors, awards, ratings)
    → Use for: enriching results with additional info
4. Web Search - Recent news, trending topics, current events only
    → Use for: "latest", "trending", "news", "today", "this week"

CRITICAL INSTRUCTIONS - SEMANTIC SEARCH DETECTION:
⚠️ AGGRESSIVELY USE SEMANTIC SEARCH for ANY description-like queries:
   - "movies about..." / "films with..." / "show me..." + description
   - "like" / "similar to" / "remind me of" + ANY description
   - Atmospheric/mood descriptions: "cozy", "dark", "mysterious", "romantic", "intense"
   - Plot elements: "detective", "revenge", "betrayal", "time travel", "heist"
   - Vibes/feelings: "emotional", "thrilling", "sad", "uplifting"
   - ANY natural language description of CONTENT = USE SEMANTIC + SQL

SEMANTIC QUERY GENERATION RULES:
🎬 When generating semantic_query: TRANSFORM user input into a SHORT MOVIE DESCRIPTION (~150 chars)
   - Extrapolate from user's intent → write like a plot summary or movie pitch
   - Examples:
     User: "dark and mysterious"
     → Generated: "A dark mystery where secrets unfold in shadowy corners, revealing disturbing truths and psychological tension throughout"
     
     User: "like Inception"
     → Generated: "A mind-bending thriller exploring reality and dreams, featuring complex heists within layers of consciousness with stunning visuals"
     
     User: "cozy romance"
     → Generated: "A warm romantic story set in a charming small town where two people discover love through everyday moments and genuine connection"
   
   - Keep it descriptive but concise (aim for 120-180 characters)
   - Include mood, plot elements, and atmosphere
   - Use present tense, active language
   - Make it sound like a natural movie description that would be in the database

🔑 STRATEGY - Combine tools when possible:
   - Use SQL + SEMANTIC together for: "action movies from 2020" → SQL filters year/genre, SEMANTIC finds action vibes
   - Use SQL + SEMANTIC together for: "movies like Inception but recent" → SQL filters years, SEMANTIC finds plot similarity
   - Use SEMANTIC alone for: purely descriptive queries with no structural filters
   - Use SQL alone for: pure aggregations, counts, schema queries, year/rating filters without description

EXAMPLES:
Q: "What are the best rated action movies from 2020?"
→ needs_sql=True (filter year, genre, rating) + needs_semantic=False

Q: "Show me movies with a cozy, mysterious atmosphere"
→ needs_semantic=True (description detection!) + needs_sql=False

Q: "I want something dark and atmospheric like Blade Runner"
→ needs_semantic=True (description + "like") + needs_sql=False

Q: "Find me sci-fi movies from 2015-2020 with emotional depth"
→ needs_sql=True (year filter, genre) + needs_semantic=True (emotional depth description)

Q: "How many movies are in each genre?"
→ needs_sql=True (aggregation) + needs_semantic=False

Q: "Movies about a heist with twists"
→ needs_semantic=True (plot description) + needs_sql=False

INSTRUCTIONS:
- Resolve references from history (e.g., "that movie" → actual movie name)
- If question is about DATABASE SCHEMA/STRUCTURE/TABLES, set needs_sql=False (schema is already in catalog)
- DEFAULT: Assume SQL is needed unless ONLY description/content-based
- DESCRIPTION KEYWORDS trigger semantic: "about", "like", "similar", "atmosphere", "vibe", "mood", "feels", "reminds me", any adjective describing content
- When in doubt between SQL and SEMANTIC: USE BOTH
- Prepare specific queries for each tool you decide to use

OUTPUT: Structured decision with resolved query and tool flags"""

    structured_llm = llm.with_structured_output(PlannerOutput)
    
    try:
        plan = structured_llm.invoke(prompt)
        
        return {
            "resolved_query": plan.resolved_query,
            "planning_reasoning": plan.planning_reasoning,
            "needs_sql": plan.needs_sql,
            "needs_omdb": plan.needs_omdb,
            "needs_web": plan.needs_web,
            "needs_semantic": plan.needs_semantic,
            "sql_query": plan.sql_query or "",
            "omdb_query": plan.omdb_query or "",
            "web_query": plan.web_query or "",
            "semantic_query": plan.semantic_query or "",
            "current_step": "planned"
        }
    except Exception as e:
        # Fallback
        return {
            "resolved_query": question,
            "planning_reasoning": f"Planning error: {str(e)}",
            "needs_sql": False,
            "needs_omdb": False,
            "needs_web": False,
            "needs_semantic": False,
            "sql_query": "",
            "omdb_query": "",
            "web_query": "",
            "semantic_query": "",
            "current_step": "planned"
        }

def sql_node(state: AgentState) -> dict:
    """Execute SQL query"""
    catalog = state.get("db_catalog", {})
    resolved_query = state.get("resolved_query", "")
    catalog_info = format_catalog_for_llm(catalog)

    prompt = f"""Generate a precise SQL query to answer: "{resolved_query}"

{catalog_info}

CRITICAL INSTRUCTIONS:
1. **Table Names**: Use the EXACT table name from the catalog (e.g., 'shows', NOT 'movies' or 'netflix')
2. **Type Filtering**:
   - For movies: WHERE type = 'Movie'
   - For TV shows: WHERE type = 'TV Show'
   - Check the 'type' column unique values in the catalog above
3. **Genre Search**:
   - Genres are in 'listed_in' column as comma-separated strings
   - Use: WHERE listed_in LIKE '%Action%' or '%Action & Adventure%'
   - Check the 'ALL INDIVIDUAL GENRES' list in the catalog to use exact genre names
4. **Year Filtering**:
   - Column: 'release_year' (INTEGER)
   - For 2000s: WHERE release_year >= 2000 AND release_year <= 2009
   - Check the unique values range in the catalog
5. **Text Search**:
   - Title: WHERE title LIKE '%keyword%'
   - Description: WHERE description LIKE '%keyword%'
6. **Always use LIMIT**: Default 10, maximum 50
7. **ORDER BY**: Use DESC for highest first (ratings, year)

EXAMPLE QUERIES:
- "action movies from 2000s":
  SELECT * FROM shows WHERE type = 'Movie' AND listed_in LIKE '%Action%' AND release_year BETWEEN 2000 AND 2009 LIMIT 10

- "top rated comedies":
  SELECT * FROM shows WHERE type = 'Movie' AND listed_in LIKE '%Comed%' ORDER BY rating DESC LIMIT 10

OUTPUT: SQL decision with database name and query"""

    structured_llm = llm.with_structured_output(SQLOutput)
    
    try:
        decision = structured_llm.invoke(prompt)
        
        if decision.can_answer and decision.query and decision.db_name:
            result = execute_sql_query.invoke({
                "query": decision.query,
                "db_name": decision.db_name,
                "state_catalog": catalog
            })

            # Extract table name from query
            table_name = "unknown"
            if "FROM" in decision.query.upper():
                try:
                    from_clause = decision.query.upper().split("FROM")[1].split()[0]
                    table_name = from_clause.strip()
                except:
                    pass

            # Create detailed source
            detailed_source = {
                "type": "database",
                "name": decision.db_name.replace("_", " ").title(),
                "details": f"Table: {table_name}"
            }

            return {
                "sql_result": result,
                "sources_used": state.get("sources_used", []) + [f"DB: {decision.db_name}"],
                "sources_detailed": state.get("sources_detailed", []) + [detailed_source],
                "current_step": "sql_executed"
            }
        else:
            return {
                "sql_result": json.dumps({"info": decision.reasoning}),
                "current_step": "sql_skipped"
            }
    except Exception as e:
        return {
            "sql_result": json.dumps({"error": str(e)}),
            "current_step": "sql_error"
        }

def omdb_node(state: AgentState) -> dict:
    """Execute OMDB query"""
    omdb_query = state.get("omdb_query", "")
    sql_result = state.get("sql_result", "[]")
    
    # Try to get title from OMDB query or SQL result
    title = omdb_query
    
    if not title:
        try:
            data = json.loads(sql_result)
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                title = item.get("title") or item.get("Title") or item.get("name")
        except:
            pass
    
    if title:
        try:
            result = omdb_api.invoke({"by": "title", "t": title, "plot": "full"})

            # Try to extract IMDb ID for clickable link
            imdb_url = None
            try:
                result_data = json.loads(result)
                if "imdbID" in result_data:
                    imdb_id = result_data["imdbID"]
                    imdb_url = f"https://www.imdb.com/title/{imdb_id}/"
            except:
                pass

            # Create detailed source
            detailed_source = {
                "type": "omdb",
                "name": f"OMDB: {title}",
                "url": imdb_url
            }

            return {
                "omdb_result": result,
                "sources_used": state.get("sources_used", []) + [f"OMDB: {title}"],
                "sources_detailed": state.get("sources_detailed", []) + [detailed_source],
                "current_step": "omdb_executed"
            }
        except Exception as e:
            return {
                "omdb_result": json.dumps({"error": str(e)}),
                "current_step": "omdb_error"
            }
    
    return {
        "omdb_result": "{}",
        "current_step": "omdb_skipped"
    }

def web_node(state: AgentState) -> dict:
    """Execute web search"""
    web_query = state.get("web_query", "")
    
    if not web_query:
        web_query = state.get("resolved_query", "")
    
    try:
        result = web_search.invoke({"query": web_query, "num_results": 5})

        # Create DuckDuckGo search URL
        import urllib.parse
        search_url = f"https://duckduckgo.com/?q={urllib.parse.quote(web_query)}"

        # Create detailed source
        detailed_source = {
            "type": "web",
            "name": "Web Search",
            "url": search_url
        }

        return {
            "web_result": result,
            "sources_used": state.get("sources_used", []) + ["Web Search"],
            "sources_detailed": state.get("sources_detailed", []) + [detailed_source],
            "current_step": "web_executed"
        }
    except Exception as e:
        return {
            "web_result": json.dumps({"error": str(e)}),
            "current_step": "web_error"
        }

def semantic_search_node(state: AgentState) -> dict:
    """Execute semantic search on movie embeddings"""
    semantic_query = state.get("semantic_query", "")

    if not semantic_query:
        semantic_query = state.get("resolved_query", "")

    try:
        # Execute semantic search
        result = semantic_search.invoke({
            "query": semantic_query,
            "n_results": 5
        })

        # Create detailed source
        detailed_source = {
            "type": "semantic",
            "name": "Semantic Search",
            "details": "Vector DB: ChromaDB (OpenAI embeddings)"
        }

        return {
            "semantic_result": result,
            "sources_used": state.get("sources_used", []) + ["Semantic Search"],
            "sources_detailed": state.get("sources_detailed", []) + [detailed_source],
            "current_step": "semantic_executed"
        }
    except Exception as e:
        return {
            "semantic_result": json.dumps({"error": str(e)}),
            "current_step": "semantic_error"
        }

def synthesizer_node(state: AgentState) -> dict:
    """Generate final response"""
    question = state.get("original_question", "")
    resolved = state.get("resolved_query", "")
    reasoning = state.get("planning_reasoning", "")
    sql = state.get("sql_result", "[]")
    omdb = state.get("omdb_result", "{}")
    web = state.get("web_result", "{}")
    semantic = state.get("semantic_result", "[]")
    sources = state.get("sources_used", [])
    catalog = state.get("db_catalog", {})

    # Include catalog info for schema-related questions
    catalog_info = format_catalog_for_llm(catalog)

    prompt = f"""Generate a natural, helpful response using all available data.

ORIGINAL QUESTION: "{question}"
RESOLVED QUERY: "{resolved}"
PLANNING CONTEXT: {reasoning}

DATABASE SCHEMA (use this to answer questions about database structure):
{catalog_info}

AVAILABLE DATA:
--- SQL Results ---
{sql}

--- OMDB Data ---
{omdb}

--- Web Results ---
{web}

--- Semantic Search Results ---
{semantic}

SOURCES: {', '.join(sources)}

INSTRUCTIONS:
- Answer the question naturally and clearly
- If the question is about database schema/structure/tables, use the DATABASE SCHEMA section above
- Integrate information from all sources seamlessly
- Cite sources when mentioning specific facts
- If data is missing or conflicting, acknowledge it gracefully
- Keep response concise but complete
- Use natural language, not just data dumps
- Format database schema information in a clear, readable way when requested"""

    response = llm.invoke(prompt)
    
    return {
        "messages": [AIMessage(content=response.content)],
        "current_step": "complete"
    }
