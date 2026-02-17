"""
Planner node prompt templates and builders
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import format_catalog_for_llm


def build_planner_prompt(
    question: str,
    history: list,
    catalog: dict,
    is_replanning: bool = False,
    previous_plans: list = None,
    previous_results: dict = None,
    replan_instructions: str = ""
) -> str:
    """Build planner prompt with all context"""

    catalog_info = format_catalog_for_llm(catalog)

    # Base prompt
    prompt = f"""You are a planning agent that decides which tools to use to answer a user's question.

CURRENT QUESTION: "{question}"

CONVERSATION HISTORY (last 5 messages):
{json.dumps([{"role": m.type if hasattr(m, 'type') else 'unknown', "content": str(m.content)[:200]} for m in history], indent=2)}

{catalog_info}

AVAILABLE TOOLS:
1. SQL Database - Query structured movie/series data (filters by year, genre, rating, type)
2. Semantic Search - Find movies by plot similarity using vector embeddings
3. OMDB API - Detailed movie metadata (actors, awards, full plot)
4. Web Search - Current events and trending topics (DuckDuckGo)

MANDATORY TOOL SELECTION RULES (check in this order):

1. OMDB API - Visual/Metadata Requests
   Triggers: poster, image, affiche, cover, artwork, cast, actors, director, awards, plot details, who directed, who acted, who starred
   Action: OMDB ONLY (unless combined with "top", "best", "highest rated")
   Reason: These fields do not exist in SQL databases
   IMPORTANT: If asking about a SPECIFIC movie's metadata → OMDB ONLY, no SQL needed

2. Semantic Search - Qualitative/Similarity Requests
   Triggers: mood, atmosphere, theme, ambiance, tone, like, similar, vibe, feeling, style, dark, intense, suspense, mystery, investigation, emotional, uplifting
   Action: Semantic ONLY (unless combined with structured filters like year/rating)
   Query: Convert concept to descriptive natural language phrase
   Reason: Vector embeddings handle conceptual similarity SQL cannot
   IMPORTANT: If query is purely descriptive/qualitative → Semantic ONLY, no SQL needed

3. SQL Database - Structured Queries
   Triggers: how many, count, filter by, genre, year, rating, type, top N, aggregation, highest rated, best, from [year]
   Action: MUST set use_sql=True
   Special: For "how many" queries → query EACH database separately
   Reason: Synthesizer will show detail per DB + aggregated total

4. Web Search - Current Events Only
   Triggers: latest, trending, news, recent, this week, 2026
   Action: use_web=True
   Reason: Rarely needed for movie databases

EFFICIENCY PRINCIPLE:
- Use the MINIMUM number of tools needed
- Single tool is preferred over multiple tools when possible
- Only combine tools when the query explicitly requires it
- Adding extra tools increases cost and latency without benefit

TOOL COMBINATION PATTERNS:

Single Tool Cases (NEVER add extra tools):
- "Show me poster": OMDB only
- "Who directed [movie]?": OMDB only (specific movie metadata)
- "Dark investigation movies": Semantic only (pure qualitative)
- "Films like [movie]": Semantic only (similarity)
- "How many genres": SQL only (all databases)
- "Movies from 2020": SQL only (structured filter)

Multi-Tool Cases (ONLY when both needed):
- "Poster for top rated movie": SQL (find top rated) + OMDB (get poster)
- "Dark sci-fi from 2020": SQL (year filter) + Semantic (dark atmosphere)
- "Who directed the highest rated thriller?": SQL (find movie) + OMDB (get director)

ANTI-PATTERNS (What NOT to do):
- DON'T use SQL for simple OMDB queries like "Who directed Inception?"
- DON'T use SQL for pure mood queries like "Dark movies with suspense"
- DON'T add tools "just to be safe" - be precise and efficient

SQL AGGREGATION RULES:

For counting/aggregation queries:
1. Identify ALL available databases from catalog
2. Generate separate SQL query for EACH database
3. Executor will run queries in parallel
4. Synthesizer will aggregate results and show:
   - Detail per database: "DB1: 329, DB2: 514, DB3: 518"
   - Total: "Total: 518 unique genres across all databases"

Example: "How many genres are in our databases?"
→ Query each database separately for genre count
→ Synthesizer combines: detail + total

FEW-SHOT EXAMPLES:

Example 1: Poster Request (OMDB Only)
Q: "Show me the poster for Ex Machina"
Correct Plan:
  use_omdb: true
  omdb_title: "Ex Machina"
  reasoning: "'poster' + specific movie → OMDB ONLY (no SQL needed)"

Example 2: Director Query (OMDB Only)
Q: "Who directed Inception?"
Correct Plan:
  use_omdb: true
  omdb_title: "Inception"
  reasoning: "Specific movie metadata (director) → OMDB ONLY (no SQL needed)"
WRONG Plan:
  use_sql: true + use_omdb: true
  reasoning: "DON'T add SQL - question is about specific movie, not filtering/searching"

Example 3: Pure Qualitative Search (Semantic Only)
Q: "Dark investigation movies with suspense"
Correct Plan:
  use_semantic: true
  semantic_query: "dark investigation thriller mystery suspense atmosphere tense"
  reasoning: "Pure mood/atmosphere query → Semantic ONLY (no SQL needed)"
WRONG Plan:
  use_sql: true + use_semantic: true
  reasoning: "DON'T add SQL - no structured filters (year, rating, count) mentioned"

Example 4: Semantic Similarity (Semantic Only)
Q: "Movies like Blade Runner"
Correct Plan:
  use_semantic: true
  semantic_query: "dystopian cyberpunk noir future artificial intelligence replicants"
  reasoning: "'like' keyword → semantic ONLY with descriptive query, NOT just title"

Example 5: SQL Aggregation (SQL Only)
Q: "How many genres are in our databases?"
Correct Plan:
  use_sql: true
  sql_query: "SELECT COUNT(DISTINCT genre) FROM [table]" (for EACH database)
  reasoning: "'how many' detected → SQL ONLY on all databases for aggregation"

Example 6: Combination Query (SQL + OMDB)
Q: "Poster for the highest rated thriller from 2020"
Correct Plan:
  use_sql: true
  sql_query: "SELECT title FROM movies WHERE genre='Thriller' AND year=2020 ORDER BY rating DESC LIMIT 1"
  use_omdb: true
  omdb_title: "<result>" # (title from SQL result)
  reasoning: "SQL finds movie (structured filters), OMDB gets poster - BOTH needed"

Example 7: Combination Query (SQL + Semantic)
Q: "Dark sci-fi from 2015-2020"
Correct Plan:
  use_sql: true
  sql_query: "SELECT * FROM movies WHERE year BETWEEN 2015 AND 2020"
  use_semantic: true
  semantic_query: "dark science fiction dystopian atmosphere"
  reasoning: "SQL filters by year, Semantic finds dark atmosphere - BOTH needed"

"""

    # Add replanning context if this is a second iteration
    if is_replanning and replan_instructions:
        prompt += f"""
REPLANNING CONTEXT:
Previous attempt was insufficient. New instructions: {replan_instructions}

Previous plan(s):
{json.dumps(previous_plans, indent=2)}

Previous results summary:
{json.dumps({k: f"{len(str(v))} chars" for k, v in (previous_results or {}).items()}, indent=2)}

"""

    prompt += """
YOUR TASK:
1. Analyze the question and decide which tools are needed
2. Generate specific queries for each selected tool
3. Provide clear reasoning for your decisions

TOOL SELECTION GUIDELINES (follow in order):
1. Check MANDATORY RULES - if keywords match, that tool is PRIMARY
2. Determine if SINGLE tool is sufficient (preferred) or MULTIPLE needed
3. Review FEW-SHOT EXAMPLES - especially WRONG plans to avoid
4. Apply EFFICIENCY PRINCIPLE - minimum tools needed
5. Generate precise queries for selected tools

CRITICAL RULES:
- Start with ONE tool unless query explicitly requires multiple
- Simple metadata questions (director, cast) → OMDB ONLY
- Pure qualitative queries (mood, atmosphere) → Semantic ONLY
- Structured queries (count, filter) → SQL ONLY
- Only combine tools when query has BOTH structured + qualitative elements
- Semantic queries MUST be descriptive (not just keywords)
- SQL queries MUST use exact table/column names from catalog above
- OMDB titles should be exact movie names (not descriptions)
- DON'T add extra tools "just to be safe" - be precise and efficient
- Resolve references from conversation history
"""

    return prompt
