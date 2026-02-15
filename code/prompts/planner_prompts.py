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
   Triggers: poster, image, affiche, cover, artwork, cast, actors, director, awards, plot details
   Action: MUST set use_omdb=True
   Reason: These fields do not exist in SQL databases

2. Semantic Search - Qualitative/Similarity Requests
   Triggers: mood, atmosphere, theme, ambiance, tone, like, similar, vibe, feeling, style
   Action: MUST set use_semantic=True
   Query: Convert concept to descriptive natural language phrase
   Reason: Vector embeddings handle conceptual similarity SQL cannot

3. SQL Database - Structured Queries
   Triggers: how many, count, filter by, genre, year, rating, type, top N, aggregation
   Action: MUST set use_sql=True
   Special: For "how many" queries → query EACH database separately
   Reason: Synthesizer will show detail per DB + aggregated total

4. Web Search - Current Events Only
   Triggers: latest, trending, news, recent, this week, 2026
   Action: use_web=True
   Reason: Rarely needed for movie databases

TOOL COMBINATION PATTERNS:

Single Tool Cases:
- Poster request: OMDB only
- "How many" queries: SQL only (all databases)
- Qualitative search: Semantic only

Multi-Tool Cases:
- "Poster for top rated movie": SQL (find top rated) + OMDB (get poster)
- "Dark sci-fi from 2020": SQL (year filter) + Semantic (dark sci-fi atmosphere)

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

TOOL SELECTION GUIDELINES:
- SQL: Use for filtering by year, genre, rating, counting, aggregations
- Semantic: Use for plot-based search, "movies like X", theme matching
- OMDB: Use when you need detailed metadata beyond database fields
- Web: Use ONLY for "latest", "trending", "news", current events

CRITICAL:
- Semantic queries MUST be descriptive (not just keywords)
- SQL queries MUST use exact table/column names from catalog above
- Don't use multiple tools if one is sufficient
- Resolve references from conversation history
"""

    return prompt
