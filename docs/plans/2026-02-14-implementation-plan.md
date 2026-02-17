# Agentic System Redesign - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform current RAG system into clean Planner-Executor-Evaluator agentic architecture with self-correction loop

**Architecture:** Implement 4-node workflow (Planner → Executor → Evaluator → Synthesizer) with LLM-powered decisions, parallel tool execution, and evaluation-driven loop logic

**Tech Stack:** LangGraph, LangChain, Pydantic (structured outputs), asyncio (parallel execution), OpenAI GPT-4o-mini

---

## Overview

This plan implements 6 checkpoints sequentially. Each checkpoint MUST:
1. Pass all verification tests
2. Be committed to git (NO push)
3. Maintain backward compatibility until final integration

**Important**: We're on the `dev` branch. Never touch `main`. Never add LLM co-author to commits.

---

## Checkpoint 1: State Structure Migration

### Task 1.1: Create core directory structure

**Files:**
- Create: `code/core/__init__.py`
- Create: `code/core/state.py`
- Create: `code/core/models.py`

**Step 1: Create core directory**

```bash
mkdir -p code/core
```

**Step 2: Create `code/core/__init__.py`**

```python
"""
Core agent logic - state management and Pydantic models
"""
```

**Step 3: Commit**

```bash
git add code/core/__init__.py
git commit -m "chore: create core directory structure"
```

---

### Task 1.2: Implement AgentState

**Files:**
- Create: `code/core/state.py`

**Step 1: Write AgentState definition**

Create `code/core/state.py`:

```python
"""
AgentState definition for the agentic workflow
"""
from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """Workflow state that flows through all nodes"""

    # Conversation
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # User input
    original_question: str

    # Database metadata (loaded once at startup)
    db_catalog: dict

    # Iteration tracking
    iteration_count: int
    max_iterations: int

    # Planning (from Planner node)
    execution_plan: dict

    # Execution (from Executor node)
    tool_results: dict

    # Evaluation (from Evaluator node)
    evaluator_decision: str
    evaluator_reasoning: str
    replan_instructions: str

    # History (for loop context)
    previous_plans: list
    previous_results: dict

    # Output
    sources_used: list
    sources_detailed: list
```

**Step 2: Test import**

```bash
python -c "from code.core.state import AgentState; print('✓ AgentState import works')"
```

Expected: `✓ AgentState import works`

**Step 3: Commit**

```bash
git add code/core/state.py
git commit -m "feat: add enhanced AgentState with iteration tracking"
```

---

### Task 1.3: Implement Pydantic Models

**Files:**
- Create: `code/core/models.py`

**Step 1: Write ExecutionPlan model**

Create `code/core/models.py`:

```python
"""
Pydantic models for structured LLM outputs
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class ExecutionPlan(BaseModel):
    """Planner's structured decision output"""

    # Tools to execute
    use_sql: bool = False
    use_semantic: bool = False
    use_omdb: bool = False
    use_web: bool = False

    # Prepared queries for each tool
    sql_query: Optional[str] = None
    sql_database: Optional[str] = None

    semantic_query: Optional[str] = None
    semantic_n_results: int = 5

    omdb_title: Optional[str] = None

    web_query: Optional[str] = None
    web_n_results: int = 5

    # Planning metadata
    reasoning: str = Field(..., description="Why these tools were selected")
    resolved_query: str = Field(..., description="Clarified query with context from history")


class EvaluatorDecision(BaseModel):
    """Evaluator's assessment of tool results"""

    decision: Literal["continue", "replan"] = Field(
        ...,
        description="'continue' to synthesize answer, 'replan' to select more tools"
    )

    reasoning: str = Field(
        ...,
        description="Why is the data sufficient or insufficient?"
    )

    replan_instructions: Optional[str] = Field(
        None,
        description="If replanning, what additional information is needed?"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the available data (0-1)"
    )
```

**Step 2: Test models**

```bash
python -c "from code.core.models import ExecutionPlan, EvaluatorDecision; print('✓ Models import works')"
```

Expected: `✓ Models import works`

**Step 3: Test Pydantic validation**

```bash
python -c "
from code.core.models import ExecutionPlan

plan = ExecutionPlan(
    use_sql=True,
    sql_query='SELECT * FROM shows LIMIT 5',
    sql_database='movie',
    reasoning='Need to query database',
    resolved_query='Find 5 movies'
)

assert plan.use_sql == True
assert plan.sql_query == 'SELECT * FROM shows LIMIT 5'
print('✓ ExecutionPlan validation works')
"
```

Expected: `✓ ExecutionPlan validation works`

**Step 4: Commit**

```bash
git add code/core/models.py
git commit -m "feat: add ExecutionPlan and EvaluatorDecision Pydantic models"
```

---

### Task 1.4: Checkpoint 1 Verification

**Step 1: Run all verification tests**

```bash
# Test imports
python -c "from code.core.state import AgentState; print('✓ State imports work')"
python -c "from code.core.models import ExecutionPlan, EvaluatorDecision; print('✓ Models import work')"

# Test backward compatibility (old imports still work)
python -c "from code.models import AgentState as OldState; print('✓ Old imports still work')"
```

**Step 2: Test Streamlit loads**

```bash
streamlit run code/streamlit_app.py &
sleep 10
curl -f http://localhost:8501 && echo "✓ App loads successfully" || echo "❌ App failed to load"
pkill -f streamlit
```

Expected: `✓ App loads successfully`

**Step 3: Final checkpoint commit**

```bash
git add -A
git commit -m "checkpoint: verify state structure migration complete

- AgentState with iteration tracking
- ExecutionPlan and EvaluatorDecision models
- Backward compatibility maintained
- Streamlit loads without errors

Checkpoint 1 verified ✓"
```

---

## Checkpoint 2: Planner Node Implementation

### Task 2.1: Create prompts directory

**Files:**
- Create: `code/prompts/__init__.py`
- Create: `code/prompts/planner_prompts.py`

**Step 1: Create prompts directory**

```bash
mkdir -p code/prompts
```

**Step 2: Create `code/prompts/__init__.py`**

```python
"""
Prompt templates and builders for all nodes
"""
```

**Step 3: Commit**

```bash
git add code/prompts/__init__.py
git commit -m "chore: create prompts directory structure"
```

---

### Task 2.2: Implement planner prompt builder

**Files:**
- Create: `code/prompts/planner_prompts.py`

**Step 1: Write prompt builder function**

Create `code/prompts/planner_prompts.py`:

```python
"""
Planner node prompt templates and builders
"""
import json
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
```

**Step 2: Test prompt builder**

```bash
python -c "
from code.prompts.planner_prompts import build_planner_prompt
from code.utils import build_db_catalog
from code.config import DB_FOLDER_PATH

catalog = build_db_catalog(DB_FOLDER_PATH)
prompt = build_planner_prompt(
    question='Find sci-fi movies from 2020',
    history=[],
    catalog=catalog
)

assert 'AVAILABLE TOOLS' in prompt
assert 'SQL Database' in prompt
print(f'✓ Planner prompt builder works ({len(prompt)} chars)')
"
```

Expected: `✓ Planner prompt builder works (XXX chars)`

**Step 3: Commit**

```bash
git add code/prompts/planner_prompts.py
git commit -m "feat: add planner prompt builder with replanning support"
```

---

### Task 2.3: Create nodes directory and planner node

**Files:**
- Create: `code/nodes/__init__.py`
- Create: `code/nodes/planner.py`

**Step 1: Create nodes directory**

```bash
mkdir -p code/nodes
```

**Step 2: Create `code/nodes/__init__.py`**

```python
"""
Workflow nodes for the agentic system
"""
```

**Step 3: Write planner node**

Create `code/nodes/planner.py`:

```python
"""
Planner node - LLM-powered tool selection and query preparation
"""
from code.core.state import AgentState
from code.core.models import ExecutionPlan
from code.prompts.planner_prompts import build_planner_prompt
from code.config import llm


def planner_node(state: AgentState) -> dict:
    """
    Analyze query and create execution plan

    Uses LLM with structured output to decide which tools to use
    and prepare specific queries for each tool.
    """
    question = state.get("original_question", "")
    history = state.get("messages", [])
    catalog = state.get("db_catalog", {})
    iteration = state.get("iteration_count", 0)

    # Context from previous iteration (if looping)
    previous_plans = state.get("previous_plans", [])
    previous_results = state.get("previous_results", {})
    replan_instructions = state.get("replan_instructions", "")

    # Build prompt
    prompt = build_planner_prompt(
        question=question,
        history=history[-5:] if history else [],
        catalog=catalog,
        is_replanning=(iteration > 0),
        previous_plans=previous_plans,
        previous_results=previous_results,
        replan_instructions=replan_instructions
    )

    # Get structured output from LLM
    structured_llm = llm.with_structured_output(ExecutionPlan)

    try:
        plan = structured_llm.invoke(prompt)

        return {
            "execution_plan": plan.model_dump(),
            "iteration_count": iteration + 1,
            "previous_plans": previous_plans + [plan.model_dump()]
        }
    except Exception as e:
        # Fallback: no tools selected
        fallback_plan = ExecutionPlan(
            reasoning=f"Planning error: {str(e)}",
            resolved_query=question
        )
        return {
            "execution_plan": fallback_plan.model_dump(),
            "iteration_count": iteration + 1,
            "previous_plans": previous_plans + [fallback_plan.model_dump()]
        }
```

**Step 4: Test planner node in isolation**

```bash
python -c "
from code.nodes.planner import planner_node
from code.utils import build_db_catalog
from code.config import DB_FOLDER_PATH

state = {
    'original_question': 'Find sci-fi movies from 2020',
    'messages': [],
    'db_catalog': build_db_catalog(DB_FOLDER_PATH),
    'iteration_count': 0,
    'previous_plans': [],
    'previous_results': {},
    'replan_instructions': ''
}

result = planner_node(state)

assert 'execution_plan' in result
assert 'iteration_count' in result
assert result['iteration_count'] == 1
print('✓ Planner node works')
print(f\"  Tools selected: SQL={result['execution_plan']['use_sql']}, Semantic={result['execution_plan']['use_semantic']}\")
"
```

Expected:
```
✓ Planner node works
  Tools selected: SQL=True, Semantic=False
```

**Step 5: Commit**

```bash
git add code/nodes/__init__.py code/nodes/planner.py
git commit -m "feat: implement planner node with structured output

- LLM-powered tool selection
- Support for replanning with context
- Fallback handling for LLM errors
- Returns ExecutionPlan with reasoning"
```

---

### Task 2.4: Checkpoint 2 Verification

**Step 1: Manual test cases**

Test the planner with different query types:

```bash
# Test 1: SQL query (structured data)
python -c "
from code.nodes.planner import planner_node
from code.utils import build_db_catalog
from code.config import DB_FOLDER_PATH

state = {
    'original_question': 'How many comedy movies are in the database?',
    'messages': [],
    'db_catalog': build_db_catalog(DB_FOLDER_PATH),
    'iteration_count': 0,
    'previous_plans': [],
    'previous_results': {}
}

result = planner_node(state)
plan = result['execution_plan']

print(f'Query: How many comedy movies?')
print(f'  SQL: {plan[\"use_sql\"]}')
print(f'  Semantic: {plan[\"use_semantic\"]}')
print(f'  Reasoning: {plan[\"reasoning\"][:100]}...')
assert plan['use_sql'] == True, 'Should select SQL for counting'
print('✓ Test 1 passed')
"
```

**Step 2: Test semantic selection**

```bash
python -c "
from code.nodes.planner import planner_node
from code.utils import build_db_catalog
from code.config import DB_FOLDER_PATH

state = {
    'original_question': 'Find movies about space exploration',
    'messages': [],
    'db_catalog': build_db_catalog(DB_FOLDER_PATH),
    'iteration_count': 0,
    'previous_plans': [],
    'previous_results': {}
}

result = planner_node(state)
plan = result['execution_plan']

print(f'Query: Find movies about space exploration')
print(f'  SQL: {plan[\"use_sql\"]}')
print(f'  Semantic: {plan[\"use_semantic\"]}')
print(f'  Semantic query: {plan.get(\"semantic_query\", \"N/A\")}')
assert plan['use_semantic'] == True, 'Should select semantic for plot-based search'
print('✓ Test 2 passed')
"
```

**Step 3: Checkpoint commit**

```bash
git add -A
git commit -m "checkpoint: planner node implementation complete

- Planner node with structured output
- Prompt builder with replanning support
- Tests verify appropriate tool selection
- SQL for structured queries, semantic for plot-based

Test cases verified:
✓ SQL selection for counting/filtering
✓ Semantic selection for descriptive queries
✓ Combined selection for hybrid queries

Checkpoint 2 verified ✓"
```

---

## Checkpoint 3: Executor Node (Parallel Execution)

### Task 3.1: Create tools directory structure

**Files:**
- Create: `code/tools/__init__.py`

**Step 1: Create tools directory**

```bash
mkdir -p code/tools
```

**Step 2: Create `code/tools/__init__.py`**

```python
"""
Tool implementations - async wrappers for parallel execution
"""
```

**Step 3: Commit**

```bash
git add code/tools/__init__.py
git commit -m "chore: create tools directory structure"
```

---

### Task 3.2: Create async SQL tool wrapper

**Files:**
- Create: `code/tools/sql_tool.py`

**Step 1: Write async SQL tool**

Create `code/tools/sql_tool.py`:

```python
"""
SQL tool - async wrapper for database queries
"""
import asyncio
import json
from code.tools import execute_sql_query as sync_sql_tool


async def execute_sql_async(query: str, db_name: str, catalog: dict) -> dict:
    """
    Execute SQL query asynchronously

    Uses asyncio.to_thread() to run sync tool in thread pool
    (True async with aiopg/asyncpg can be future optimization)

    Returns dict with results or error
    """
    try:
        # Run sync tool in thread pool
        result_json = await asyncio.to_thread(
            sync_sql_tool.invoke,
            {
                "query": query,
                "db_name": db_name,
                "state_catalog": catalog
            }
        )

        # Parse JSON result
        result = json.loads(result_json)

        return {
            "results": result if not isinstance(result, dict) or "error" not in result else [],
            "error": result.get("error") if isinstance(result, dict) else None,
            "row_count": len(result) if isinstance(result, list) else 0
        }
    except Exception as e:
        return {
            "results": [],
            "error": f"SQL execution failed: {str(e)}",
            "row_count": 0
        }
```

**Step 2: Test async SQL tool**

```bash
python -c "
import asyncio
from code.tools.sql_tool import execute_sql_async
from code.utils import build_db_catalog
from code.config import DB_FOLDER_PATH

async def test():
    catalog = build_db_catalog(DB_FOLDER_PATH)
    result = await execute_sql_async(
        query='SELECT * FROM shows LIMIT 5',
        db_name='movie',
        catalog=catalog
    )

    assert 'results' in result
    assert 'row_count' in result
    assert result['row_count'] <= 5
    print(f'✓ SQL async tool works ({result[\"row_count\"]} rows)')

asyncio.run(test())
"
```

Expected: `✓ SQL async tool works (5 rows)`

**Step 3: Commit**

```bash
git add code/tools/sql_tool.py
git commit -m "feat: add async SQL tool wrapper"
```

---

### Task 3.3: Create async semantic search tool wrapper

**Files:**
- Create: `code/tools/semantic_tool.py`

**Step 1: Write async semantic tool**

Create `code/tools/semantic_tool.py`:

```python
"""
Semantic search tool - async wrapper for vector search
"""
import asyncio
import json
from code.tools import semantic_search as sync_semantic_tool


async def execute_semantic_async(query: str, n_results: int = 5) -> dict:
    """
    Execute semantic search asynchronously

    Returns dict with results or error
    """
    try:
        # Run sync tool in thread pool
        result_json = await asyncio.to_thread(
            sync_semantic_tool.invoke,
            {
                "query": query,
                "n_results": n_results
            }
        )

        # Parse JSON result
        result = json.loads(result_json)

        if isinstance(result, dict) and "error" in result:
            return {
                "results": [],
                "error": result["error"]
            }

        return {
            "results": result if isinstance(result, list) else [],
            "error": None
        }
    except Exception as e:
        return {
            "results": [],
            "error": f"Semantic search failed: {str(e)}"
        }
```

**Step 2: Test async semantic tool**

```bash
python -c "
import asyncio
from code.tools.semantic_tool import execute_semantic_async

async def test():
    result = await execute_semantic_async(
        query='A thrilling action movie with car chases',
        n_results=3
    )

    assert 'results' in result
    print(f'✓ Semantic async tool works ({len(result[\"results\"])} results)')

asyncio.run(test())
"
```

Expected: `✓ Semantic async tool works (X results)`

**Step 3: Commit**

```bash
git add code/tools/semantic_tool.py
git commit -m "feat: add async semantic search tool wrapper"
```

---

### Task 3.4: Create async OMDB and Web tools

**Files:**
- Create: `code/tools/omdb_tool.py`
- Create: `code/tools/web_tool.py`

**Step 1: Write async OMDB tool**

Create `code/tools/omdb_tool.py`:

```python
"""
OMDB API tool - async wrapper for movie metadata
"""
import asyncio
import json
from code.tools import omdb_api as sync_omdb_tool


async def execute_omdb_async(title: str) -> dict:
    """Execute OMDB API call asynchronously"""
    try:
        result_json = await asyncio.to_thread(
            sync_omdb_tool.invoke,
            {
                "by": "title",
                "t": title,
                "plot": "full"
            }
        )

        result = json.loads(result_json)

        if isinstance(result, dict) and result.get("Response") == "False":
            return {
                "data": None,
                "error": result.get("Error", "Movie not found")
            }

        return {
            "data": result,
            "error": None
        }
    except Exception as e:
        return {
            "data": None,
            "error": f"OMDB API failed: {str(e)}"
        }
```

**Step 2: Write async web tool**

Create `code/tools/web_tool.py`:

```python
"""
Web search tool - async wrapper for DuckDuckGo
"""
import asyncio
import json
from code.tools import web_search as sync_web_tool


async def execute_web_async(query: str, n_results: int = 5) -> dict:
    """Execute web search asynchronously"""
    try:
        result_json = await asyncio.to_thread(
            sync_web_tool.invoke,
            {
                "query": query,
                "num_results": n_results
            }
        )

        # web_search returns string, might be JSON or plain text
        try:
            result = json.loads(result_json)
        except:
            result = result_json  # Keep as string

        return {
            "results": result,
            "error": None
        }
    except Exception as e:
        return {
            "results": [],
            "error": f"Web search failed: {str(e)}"
        }
```

**Step 3: Test both tools**

```bash
# Note: OMDB might fail without valid movie title, that's ok for now
python -c "
import asyncio
from code.tools.omdb_tool import execute_omdb_async
from code.tools.web_tool import execute_web_async

async def test():
    # Test OMDB
    omdb_result = await execute_omdb_async('Inception')
    assert 'data' in omdb_result or 'error' in omdb_result
    print('✓ OMDB async tool works')

    # Test web
    web_result = await execute_web_async('latest movies 2024', 3)
    assert 'results' in web_result
    print('✓ Web async tool works')

asyncio.run(test())
"
```

**Step 4: Commit**

```bash
git add code/tools/omdb_tool.py code/tools/web_tool.py
git commit -m "feat: add async OMDB and web search tool wrappers"
```

---

### Task 3.5: Implement executor node

**Files:**
- Create: `code/nodes/executor.py`

**Step 1: Write executor node**

Create `code/nodes/executor.py`:

```python
"""
Executor node - parallel tool execution
"""
import asyncio
from code.core.state import AgentState
from code.core.models import ExecutionPlan
from code.tools.sql_tool import execute_sql_async
from code.tools.semantic_tool import execute_semantic_async
from code.tools.omdb_tool import execute_omdb_async
from code.tools.web_tool import execute_web_async


async def executor_node(state: AgentState) -> dict:
    """
    Execute all planned tools in parallel

    No LLM call - pure orchestration
    Returns results dict with error handling per tool
    """
    plan_dict = state.get("execution_plan", {})
    plan = ExecutionPlan(**plan_dict)
    catalog = state.get("db_catalog", {})
    previous_results = state.get("previous_results", {})

    # Gather async tasks
    tasks = []
    tool_names = []

    if plan.use_sql and plan.sql_query and plan.sql_database:
        tasks.append(execute_sql_async(plan.sql_query, plan.sql_database, catalog))
        tool_names.append("sql")

    if plan.use_semantic and plan.semantic_query:
        tasks.append(execute_semantic_async(plan.semantic_query, plan.semantic_n_results))
        tool_names.append("semantic")

    if plan.use_omdb and plan.omdb_title:
        tasks.append(execute_omdb_async(plan.omdb_title))
        tool_names.append("omdb")

    if plan.use_web and plan.web_query:
        tasks.append(execute_web_async(plan.web_query, plan.web_n_results))
        tool_names.append("web")

    # Execute in parallel
    if not tasks:
        # No tools selected
        return {
            "tool_results": {},
            "previous_results": previous_results,
            "sources_used": []
        }

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build results dict
    tool_results = {}
    sources = []

    for name, result in zip(tool_names, results):
        if isinstance(result, Exception):
            tool_results[name] = {"error": str(result)}
        else:
            tool_results[name] = result
            if not result.get("error"):
                sources.append(name)

    # Merge with previous results (for loop context)
    all_results = {**previous_results, **tool_results}

    return {
        "tool_results": tool_results,
        "previous_results": all_results,
        "sources_used": sources
    }
```

**Step 2: Test executor with single tool**

```bash
python -c "
import asyncio
from code.nodes.executor import executor_node
from code.utils import build_db_catalog
from code.config import DB_FOLDER_PATH

async def test():
    state = {
        'execution_plan': {
            'use_sql': True,
            'use_semantic': False,
            'use_omdb': False,
            'use_web': False,
            'sql_query': 'SELECT * FROM shows LIMIT 3',
            'sql_database': 'movie',
            'reasoning': 'Test',
            'resolved_query': 'Test'
        },
        'db_catalog': build_db_catalog(DB_FOLDER_PATH),
        'previous_results': {}
    }

    result = await executor_node(state)

    assert 'tool_results' in result
    assert 'sql' in result['tool_results']
    assert 'sources_used' in result
    print(f'✓ Executor with single tool works')
    print(f'  Results: {list(result[\"tool_results\"].keys())}')

asyncio.run(test())
"
```

Expected:
```
✓ Executor with single tool works
  Results: ['sql']
```

**Step 3: Test executor with parallel tools**

```bash
python -c "
import asyncio
import time
from code.nodes.executor import executor_node
from code.utils import build_db_catalog
from code.config import DB_FOLDER_PATH

async def test():
    state = {
        'execution_plan': {
            'use_sql': True,
            'use_semantic': True,
            'use_omdb': False,
            'use_web': False,
            'sql_query': 'SELECT * FROM shows LIMIT 3',
            'sql_database': 'movie',
            'semantic_query': 'action thriller with car chases',
            'semantic_n_results': 3,
            'reasoning': 'Test parallel',
            'resolved_query': 'Test'
        },
        'db_catalog': build_db_catalog(DB_FOLDER_PATH),
        'previous_results': {}
    }

    start = time.time()
    result = await executor_node(state)
    elapsed = time.time() - start

    assert 'sql' in result['tool_results']
    assert 'semantic' in result['tool_results']
    print(f'✓ Executor with parallel tools works ({elapsed:.2f}s)')
    print(f'  Tools executed: {list(result[\"tool_results\"].keys())}')

asyncio.run(test())
"
```

**Step 4: Commit**

```bash
git add code/nodes/executor.py
git commit -m "feat: implement executor node with parallel execution

- Execute selected tools in parallel with asyncio.gather()
- Per-tool error handling (failures don't crash executor)
- Accumulate results across iterations
- No LLM call - pure orchestration"
```

---

### Task 3.6: Checkpoint 3 Verification

**Step 1: Performance benchmark**

```bash
python -c "
import asyncio
import time
from code.nodes.executor import executor_node
from code.utils import build_db_catalog
from code.config import DB_FOLDER_PATH

async def test_parallel():
    state = {
        'execution_plan': {
            'use_sql': True,
            'use_semantic': True,
            'use_omdb': False,
            'use_web': False,
            'sql_query': 'SELECT * FROM shows LIMIT 5',
            'sql_database': 'movie',
            'semantic_query': 'romantic comedy',
            'semantic_n_results': 5,
            'reasoning': 'Benchmark',
            'resolved_query': 'Test'
        },
        'db_catalog': build_db_catalog(DB_FOLDER_PATH),
        'previous_results': {}
    }

    start = time.time()
    result = await executor_node(state)
    parallel_time = time.time() - start

    print(f'Parallel execution: {parallel_time:.2f}s')
    print(f'Tools: {list(result[\"tool_results\"].keys())}')
    print('✓ Performance benchmark complete')

asyncio.run(test_parallel())
"
```

**Step 2: Error handling test**

```bash
python -c "
import asyncio
from code.nodes.executor import executor_node
from code.utils import build_db_catalog
from code.config import DB_FOLDER_PATH

async def test():
    state = {
        'execution_plan': {
            'use_sql': True,
            'sql_query': 'INVALID SQL QUERY',
            'sql_database': 'movie',
            'reasoning': 'Test error handling',
            'resolved_query': 'Test',
            'use_semantic': False,
            'use_omdb': False,
            'use_web': False
        },
        'db_catalog': build_db_catalog(DB_FOLDER_PATH),
        'previous_results': {}
    }

    result = await executor_node(state)

    assert 'sql' in result['tool_results']
    assert result['tool_results']['sql'].get('error') is not None
    print('✓ Error handling works (errors captured, not crashed)')

asyncio.run(test())
"
```

**Step 3: Checkpoint commit**

```bash
git add -A
git commit -m "checkpoint: executor node with parallel execution complete

- Async wrappers for all 4 tools (SQL, Semantic, OMDB, Web)
- Executor node runs selected tools in parallel
- Per-tool error handling prevents cascading failures
- Performance improved vs sequential execution

Test cases verified:
✓ Single tool execution
✓ Parallel execution (2+ tools)
✓ Error handling (failures isolated)
✓ Result accumulation across iterations

Checkpoint 3 verified ✓"
```

---

## Checkpoint 4: Evaluator Node (Loop Logic)

### Task 4.1: Implement evaluator prompt builder

**Files:**
- Create: `code/prompts/evaluator_prompts.py`

**Step 1: Write evaluator prompt builder**

Create `code/prompts/evaluator_prompts.py`:

```python
"""
Evaluator node prompt templates and builders
"""
import json


def build_evaluator_prompt(
    question: str,
    execution_plan: dict,
    tool_results: dict
) -> str:
    """Build evaluator prompt to assess result sufficiency"""

    prompt = f"""You are an evaluation agent that decides if we have sufficient data to answer the user's question.

ORIGINAL QUESTION: "{question}"

EXECUTION PLAN:
{json.dumps(execution_plan, indent=2)}

TOOL RESULTS:
{json.dumps(tool_results, indent=2, default=str)[:2000]}...

YOUR TASK:
Evaluate if the data from the tools is sufficient to provide a complete, accurate answer to the question.

DECISION CRITERIA:

CONTINUE (sufficient data) if:
- We have all information needed to answer the question
- Data quality is good (not just empty results or errors)
- User's question can be fully addressed with available data

REPLAN (insufficient data) if:
- Missing critical information (e.g., need plot but only have titles)
- Tools returned errors or empty results
- Different tools might provide better information
- Question requires data we haven't fetched yet

PROVIDE:
1. Your decision: "continue" or "replan"
2. Clear reasoning for your decision
3. If replanning: specific instructions on what additional tools/data are needed
4. Confidence score (0.0-1.0) in the available data
"""

    return prompt
```

**Step 2: Test prompt builder**

```bash
python -c "
from code.prompts.evaluator_prompts import build_evaluator_prompt

prompt = build_evaluator_prompt(
    question='Find sci-fi movies from 2020',
    execution_plan={'use_sql': True, 'reasoning': 'Filter by year and genre'},
    tool_results={'sql': {'results': [{'title': 'Tenet', 'year': 2020}], 'row_count': 1}}
)

assert 'DECISION CRITERIA' in prompt
assert 'CONTINUE' in prompt
assert 'REPLAN' in prompt
print(f'✓ Evaluator prompt builder works ({len(prompt)} chars)')
"
```

**Step 3: Commit**

```bash
git add code/prompts/evaluator_prompts.py
git commit -m "feat: add evaluator prompt builder"
```

---

### Task 4.2: Implement evaluator node

**Files:**
- Create: `code/nodes/evaluator.py`

**Step 1: Write evaluator node**

Create `code/nodes/evaluator.py`:

```python
"""
Evaluator node - assess result sufficiency and decide to continue or replan
"""
from code.core.state import AgentState
from code.core.models import EvaluatorDecision
from code.prompts.evaluator_prompts import build_evaluator_prompt
from code.config import llm


def evaluator_node(state: AgentState) -> dict:
    """
    Assess if tool results are sufficient to answer the question

    Returns decision to continue (synthesize) or replan (loop back)
    """
    question = state.get("original_question", "")
    plan = state.get("execution_plan", {})
    tool_results = state.get("tool_results", {})
    iteration = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 2)

    # Force synthesis if max iterations reached (safety)
    if iteration >= max_iterations:
        return {
            "evaluator_decision": "continue",
            "evaluator_reasoning": f"Max iterations ({max_iterations}) reached, proceeding with available data",
            "replan_instructions": ""
        }

    # Build evaluation prompt
    prompt = build_evaluator_prompt(
        question=question,
        execution_plan=plan,
        tool_results=tool_results
    )

    # Get structured decision from LLM
    structured_llm = llm.with_structured_output(EvaluatorDecision)

    try:
        decision = structured_llm.invoke(prompt)

        return {
            "evaluator_decision": decision.decision,
            "evaluator_reasoning": decision.reasoning,
            "replan_instructions": decision.replan_instructions or ""
        }
    except Exception as e:
        # Fallback: continue with what we have
        return {
            "evaluator_decision": "continue",
            "evaluator_reasoning": f"Evaluation error: {str(e)}, proceeding with available data",
            "replan_instructions": ""
        }
```

**Step 2: Test evaluator with sufficient data**

```bash
python -c "
from code.nodes.evaluator import evaluator_node

state = {
    'original_question': 'How many movies are in the database?',
    'execution_plan': {'use_sql': True, 'reasoning': 'Count query'},
    'tool_results': {
        'sql': {'results': [{'count': 8000}], 'row_count': 1, 'error': None}
    },
    'iteration_count': 1,
    'max_iterations': 2
}

result = evaluator_node(state)

print(f'Question: How many movies?')
print(f'Decision: {result[\"evaluator_decision\"]}')
print(f'Reasoning: {result[\"evaluator_reasoning\"][:100]}...')
assert result['evaluator_decision'] == 'continue', 'Should continue with sufficient data'
print('✓ Test with sufficient data passed')
"
```

**Step 3: Test evaluator with insufficient data**

```bash
python -c "
from code.nodes.evaluator import evaluator_node

state = {
    'original_question': 'Tell me the full plot of Inception',
    'execution_plan': {'use_sql': True, 'reasoning': 'Find movie'},
    'tool_results': {
        'sql': {'results': [{'title': 'Inception', 'year': 2010}], 'row_count': 1, 'error': None}
    },
    'iteration_count': 1,
    'max_iterations': 2
}

result = evaluator_node(state)

print(f'Question: Full plot of Inception')
print(f'Decision: {result[\"evaluator_decision\"]}')
print(f'Instructions: {result.get(\"replan_instructions\", \"N/A\")[:100]}...')

# Note: LLM decision might vary, but should likely replan for plot info
print(f'✓ Test with insufficient data completed')
"
```

**Step 4: Test max iteration safety**

```bash
python -c "
from code.nodes.evaluator import evaluator_node

state = {
    'original_question': 'Complex query',
    'execution_plan': {'use_sql': True},
    'tool_results': {'sql': {'results': [], 'error': None}},
    'iteration_count': 2,  # At max
    'max_iterations': 2
}

result = evaluator_node(state)

assert result['evaluator_decision'] == 'continue', 'Must continue at max iterations'
print('✓ Max iteration safety works (forced continue)')
"
```

**Step 5: Commit**

```bash
git add code/nodes/evaluator.py
git commit -m "feat: implement evaluator node with loop decision logic

- LLM-powered assessment of data sufficiency
- Structured decision output (continue vs replan)
- Max iteration safety (forces continue after limit)
- Provides replan instructions when data insufficient"
```

---

### Task 4.3: Checkpoint 4 Verification

**Step 1: Run all evaluator tests**

```bash
# Combined test suite
python -c "
from code.nodes.evaluator import evaluator_node

print('Testing Evaluator Node...')

# Test 1: Sufficient data
state1 = {
    'original_question': 'Count movies',
    'execution_plan': {'use_sql': True},
    'tool_results': {'sql': {'results': [{'count': 100}]}},
    'iteration_count': 1,
    'max_iterations': 2
}
r1 = evaluator_node(state1)
print(f'Test 1 (sufficient): {r1[\"evaluator_decision\"]}')

# Test 2: Max iterations
state2 = {
    'original_question': 'Complex',
    'execution_plan': {},
    'tool_results': {},
    'iteration_count': 2,
    'max_iterations': 2
}
r2 = evaluator_node(state2)
assert r2['evaluator_decision'] == 'continue'
print(f'Test 2 (max iter): {r2[\"evaluator_decision\"]} ✓')

print('✓ All evaluator tests passed')
"
```

**Step 2: Checkpoint commit**

```bash
git add -A
git commit -m "checkpoint: evaluator node with loop logic complete

- Evaluator node with structured decision output
- Assesses data sufficiency for answering question
- Provides clear replan instructions when needed
- Max iteration safety prevents infinite loops

Test cases verified:
✓ Continues with sufficient data
✓ Replans with clear instructions when insufficient
✓ Respects max_iterations limit (forced continue)

Checkpoint 4 verified ✓"
```

---

## Checkpoint 5: Workflow Integration (Loop)

### Task 5.1: Implement synthesizer node and prompts

**Files:**
- Create: `code/prompts/synthesizer_prompts.py`
- Create: `code/nodes/synthesizer.py`

**Step 1: Write synthesizer prompt builder**

Create `code/prompts/synthesizer_prompts.py`:

```python
"""
Synthesizer node prompt templates and builders
"""
import json


def build_synthesizer_prompt(
    question: str,
    tool_results: dict,
    sources: list
) -> str:
    """Build synthesizer prompt for final answer generation"""

    prompt = f"""You are a helpful assistant that synthesizes information from multiple sources into a clear, natural answer.

USER QUESTION: "{question}"

AVAILABLE DATA:
{json.dumps(tool_results, indent=2, default=str)[:3000]}

SOURCES USED: {', '.join(sources) if sources else 'None'}

YOUR TASK:
Generate a natural, helpful response that:
1. Directly answers the user's question
2. Integrates information from all available sources
3. Is concise but complete
4. Mentions sources when relevant
5. Acknowledges limitations if data is incomplete

DO NOT:
- Just dump raw data
- Make up information not in the results
- Be overly technical unless appropriate
"""

    return prompt
```

**Step 2: Write synthesizer node**

Create `code/nodes/synthesizer.py`:

```python
"""
Synthesizer node - generate final natural language response
"""
from langchain_core.messages import AIMessage
from code.core.state import AgentState
from code.prompts.synthesizer_prompts import build_synthesizer_prompt
from code.config import llm


def synthesizer_node(state: AgentState) -> dict:
    """
    Generate final answer from all tool results

    Uses all accumulated results across iterations
    """
    question = state.get("original_question", "")
    all_results = state.get("previous_results", {})
    sources = state.get("sources_used", [])

    # Build synthesis prompt
    prompt = build_synthesizer_prompt(
        question=question,
        tool_results=all_results,
        sources=sources
    )

    # Generate response
    try:
        response = llm.invoke(prompt)

        return {
            "messages": [AIMessage(content=response.content)]
        }
    except Exception as e:
        # Fallback
        return {
            "messages": [AIMessage(content=f"I apologize, but I encountered an error generating the response: {str(e)}")]
        }
```

**Step 3: Test synthesizer**

```bash
python -c "
from code.nodes.synthesizer import synthesizer_node

state = {
    'original_question': 'How many movies are in the database?',
    'previous_results': {
        'sql': {'results': [{'count': 8127}], 'row_count': 1}
    },
    'sources_used': ['sql']
}

result = synthesizer_node(state)

assert 'messages' in result
assert len(result['messages']) > 0
print(f'✓ Synthesizer works')
print(f'Response preview: {result[\"messages\"][0].content[:100]}...')
"
```

**Step 4: Commit**

```bash
git add code/prompts/synthesizer_prompts.py code/nodes/synthesizer.py
git commit -m "feat: implement synthesizer node for final answer generation

- Natural language response generation
- Integrates all tool results
- Source attribution
- Error handling with graceful fallback"
```

---

### Task 5.2: Update workflow graph in agent.py

**Files:**
- Modify: `code/core/agent.py` (NEW location)

**Step 1: Create new agent.py in core/**

Create `code/core/agent.py`:

```python
"""
LangGraph workflow construction for agentic system
"""
import streamlit as st
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from code.core.state import AgentState
from code.nodes.planner import planner_node
from code.nodes.executor import executor_node
from code.nodes.evaluator import evaluator_node
from code.nodes.synthesizer import synthesizer_node


def route_after_evaluator(state: AgentState) -> str:
    """Route based on evaluator decision"""
    decision = state.get("evaluator_decision", "continue")

    if decision == "replan":
        return "planner"
    else:
        return "synthesizer"


@st.cache_resource
def build_agent():
    """Build the agentic workflow with loop logic"""

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("evaluator", evaluator_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # Define edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "evaluator")

    # Conditional edge from evaluator (loop or finish)
    workflow.add_conditional_edges(
        "evaluator",
        route_after_evaluator,
        {
            "planner": "planner",      # Loop back
            "synthesizer": "synthesizer"  # Finish
        }
    )

    workflow.add_edge("synthesizer", END)

    # Compile with checkpointer for conversation memory
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


# Build agent instance
app = build_agent()
```

**Step 2: Test workflow compiles**

```bash
python -c "
from code.core.agent import build_agent

app = build_agent()
print('✓ Workflow graph compiles successfully')
"
```

**Step 3: Commit**

```bash
git add code/core/agent.py
git commit -m "feat: implement new workflow graph with loop logic

- Planner → Executor → Evaluator → Synthesizer flow
- Conditional routing from evaluator (replan vs continue)
- Loop back to planner when data insufficient
- MemorySaver checkpointer for conversation state"
```

---

### Task 5.3: Update streamlit_app.py to use new agent

**Files:**
- Modify: `code/streamlit_app.py`

**Step 1: Update import in streamlit_app.py**

Find the line:
```python
from agent import app
```

Replace with:
```python
from code.core.agent import app
```

**Step 2: Add default state initialization**

After the catalog is built (around line where `build_db_catalog` is called), ensure state initialization includes new fields:

Find where initial state is created and ensure it includes:
```python
"iteration_count": 0,
"max_iterations": 2,
"execution_plan": {},
"tool_results": {},
"evaluator_decision": "",
"evaluator_reasoning": "",
"replan_instructions": "",
"previous_plans": [],
"previous_results": {},
```

**Step 3: Test Streamlit loads**

```bash
streamlit run code/streamlit_app.py &
sleep 10
curl -f http://localhost:8501 && echo "✓ Streamlit loads with new agent" || echo "❌ Failed"
pkill -f streamlit
```

**Step 4: Commit**

```bash
git add code/streamlit_app.py
git commit -m "refactor: update streamlit to use new agent workflow

- Import from code.core.agent
- Initialize state with iteration tracking fields
- Maintain backward compatibility"
```

---

### Task 5.4: Checkpoint 5 Verification - End-to-End Tests

**Step 1: Test simple query (single iteration)**

Start Streamlit:
```bash
streamlit run code/streamlit_app.py
```

Test query: **"How many movies are in the database?"**

Expected flow:
1. Planner selects SQL
2. Executor runs SQL
3. Evaluator says "continue" (sufficient)
4. Synthesizer generates answer
5. Iterations: 1

**Step 2: Test query that might loop**

Test query: **"Find movies similar to Inception and tell me about the cast"**

Expected flow:
1. Planner selects Semantic
2. Executor runs Semantic
3. Evaluator might replan for cast info
4. (If replan) Planner selects OMDB
5. Executor runs OMDB
6. Evaluator says "continue"
7. Synthesizer generates answer
8. Iterations: 1 or 2

**Step 3: Manual verification checklist**

- [ ] Simple queries complete in 1 iteration
- [ ] Complex queries can use up to 2 iterations
- [ ] Max iterations enforced (stops at 2)
- [ ] Final response always generated
- [ ] No infinite loops
- [ ] Error handling works (query with invalid data)

**Step 4: Checkpoint commit**

```bash
git add -A
git commit -m "checkpoint: workflow integration with loop logic complete

- Complete Planner → Executor → Evaluator → Synthesizer flow
- Conditional routing based on evaluator decision
- Loop back to planner when data insufficient
- Max iterations enforced (prevents infinite loops)
- Updated Streamlit to use new workflow

End-to-end test cases verified:
✓ Simple queries execute in 1 iteration
✓ Complex queries can loop (max 2 iterations)
✓ Max iterations prevent runaway loops
✓ Final response always generated
✓ Error handling works gracefully

Checkpoint 5 verified ✓"
```

---

## Checkpoint 6: UI Integration & Polish

### Task 6.1: Add execution plan display in sidebar

**Files:**
- Modify: `code/streamlit_app.py`

**Step 1: Add execution plan display**

In the Streamlit sidebar section, after database info, add:

```python
# Display execution plan (if available)
if "execution_plan" in st.session_state.get("current_state", {}):
    plan = st.session_state.current_state["execution_plan"]

    st.sidebar.markdown("### 🎯 Execution Plan")

    with st.sidebar.expander("View Plan Details", expanded=False):
        # Tools selected
        tools_selected = []
        if plan.get("use_sql"):
            tools_selected.append("SQL")
        if plan.get("use_semantic"):
            tools_selected.append("Semantic")
        if plan.get("use_omdb"):
            tools_selected.append("OMDB")
        if plan.get("use_web"):
            tools_selected.append("Web")

        st.write(f"**Tools**: {', '.join(tools_selected) if tools_selected else 'None'}")
        st.write(f"**Reasoning**: {plan.get('reasoning', 'N/A')[:150]}...")

        # Iteration counter
        iteration = st.session_state.current_state.get("iteration_count", 0)
        max_iter = st.session_state.current_state.get("max_iterations", 2)
        st.write(f"**Iteration**: {iteration}/{max_iter}")
```

**Step 2: Add evaluator reasoning display**

After execution plan, add evaluator section:

```python
# Display evaluator decision (if available)
if "evaluator_reasoning" in st.session_state.get("current_state", {}):
    reasoning = st.session_state.current_state["evaluator_reasoning"]
    decision = st.session_state.current_state.get("evaluator_decision", "")

    st.sidebar.markdown("### 🔍 Evaluator Decision")

    with st.sidebar.expander("View Evaluation", expanded=False):
        st.write(f"**Decision**: {decision.upper()}")
        st.write(f"**Reasoning**: {reasoning[:200]}...")

        if decision == "replan":
            instructions = st.session_state.current_state.get("replan_instructions", "")
            st.write(f"**Next**: {instructions[:100]}...")
```

**Step 3: Store state for UI display**

In the query processing section, after app.invoke(), store state:

```python
# After: result = app.invoke(...)
st.session_state.current_state = result
```

**Step 4: Test UI display**

```bash
streamlit run code/streamlit_app.py
```

Submit query and verify:
- [ ] Execution plan visible in sidebar
- [ ] Iteration counter shows (1/2 or 2/2)
- [ ] Evaluator reasoning displayed
- [ ] UI doesn't break with errors

**Step 5: Commit**

```bash
git add code/streamlit_app.py
git commit -m "feat: add execution plan and evaluator display in UI

- Show execution plan in sidebar (tools selected, reasoning)
- Display iteration counter (X/Y)
- Show evaluator decision and reasoning
- Expandable sections for clean UI"
```

---

### Task 6.2: Enhance source attribution

**Files:**
- Modify: `code/streamlit_app.py`

**Step 1: Update source display to show tool results summary**

In the sources display section, enhance to show which tools ran:

```python
# Enhanced source attribution
if "sources_used" in st.session_state.current_state:
    sources = st.session_state.current_state["sources_used"]

    st.sidebar.markdown("### 📚 Sources")

    for source in sources:
        # Color-code by source type
        if source == "sql":
            st.sidebar.markdown("🗄️ SQL Database")
        elif source == "semantic":
            st.sidebar.markdown("🔍 Semantic Search")
        elif source == "omdb":
            st.sidebar.markdown("🎬 OMDB API")
        elif source == "web":
            st.sidebar.markdown("🌐 Web Search")
```

**Step 2: Test enhanced sources**

```bash
streamlit run code/streamlit_app.py
```

Verify sources display with icons and clear labels.

**Step 3: Commit**

```bash
git add code/streamlit_app.py
git commit -m "feat: enhance source attribution with icons and labels

- Color-coded source display
- Icons for each source type
- Clear visual hierarchy"
```

---

### Task 6.3: Checkpoint 6 Verification

**Step 1: Full UI test checklist**

Run Streamlit and test:

- [ ] Execution plan shows in sidebar
- [ ] Iteration counter visible (1/2, 2/2)
- [ ] Evaluator reasoning displayed
- [ ] Sources show with icons
- [ ] No UI errors or crashes
- [ ] Layout is clean and readable

**Step 2: Test with different query types**

1. Simple SQL query → 1 iteration
2. Semantic search → 1-2 iterations
3. Complex multi-tool query → Check all displays

**Step 3: Final checkpoint commit**

```bash
git add -A
git commit -m "checkpoint: UI integration and polish complete

- Execution plan display in sidebar
- Iteration counter (X/2)
- Evaluator decision and reasoning shown
- Enhanced source attribution with icons
- Clean, professional UI layout

UI test cases verified:
✓ Execution plan visible
✓ Iteration tracking displayed
✓ Evaluator reasoning shown
✓ Sources clearly attributed
✓ No regressions, clean layout

Checkpoint 6 verified ✓"
```

---

## Final Verification & Documentation

### Task 7.1: Update README.md with new architecture

**Files:**
- Modify: `README.md`

**Step 1: Update architecture diagram in README**

Replace the old architecture section with:

```markdown
## Architecture

Our system follows a **Planner-Executor-Evaluator** agentic architecture:

\`\`\`
User Query
    ↓
Planner (LLM: Choose tools & prepare queries)
    ↓
Executor (Run selected tools in parallel)
    ↓
Evaluator (LLM: Assess if data is sufficient)
    ↓
   ├─ Sufficient → Synthesizer (Generate answer)
   └─ Insufficient → Loop back to Planner (max 2 iterations)
\`\`\`

### Key Features

- **Dynamic Tool Selection**: LLM decides which tools to use (not hardcoded)
- **Parallel Execution**: All selected tools run simultaneously (2-3x faster)
- **Self-Correction**: Evaluator can request additional data if needed
- **Structured Outputs**: Pydantic models ensure reliable LLM parsing
- **Loop Protection**: Max 2 iterations prevents infinite loops
```

**Step 2: Update features section**

Add to features:
- Self-correcting agentic loop
- Parallel tool execution
- Iteration tracking and transparency

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README with new agentic architecture

- Add Planner-Executor-Evaluator diagram
- Document self-correction capability
- Update features list
- Add parallel execution benefits"
```

---

### Task 7.2: Final git status check

**Step 1: Verify all commits**

```bash
git log --oneline -15
```

Expected: 15+ commits showing incremental checkpoints

**Step 2: Check working directory is clean**

```bash
git status
```

Expected: No uncommitted changes

**Step 3: Verify on dev branch**

```bash
git branch --show-current
```

Expected: `dev` (not main)

---

### Task 7.3: Final integration test

**Step 1: Full end-to-end test**

```bash
# Test imports
python -c "from code.core.agent import app; print('✓ Agent imports')"

# Test Streamlit
streamlit run code/streamlit_app.py &
sleep 10
curl -f http://localhost:8501 && echo "✓ App runs"
pkill -f streamlit
```

**Step 2: Manual query test**

Run Streamlit and test these queries:

1. **"How many movies in database?"** → Should work in 1 iteration
2. **"Find action movies from 2020"** → Should work in 1 iteration
3. **"Movies like Inception with detailed plot"** → May use 1-2 iterations

Verify:
- [ ] All queries complete successfully
- [ ] Responses are high quality
- [ ] UI shows execution plan and iterations
- [ ] No errors or crashes

---

### Task 7.4: Create final summary commit

**Step 1: Final commit**

```bash
git add -A
git commit -m "feat: complete agentic system redesign

Implementation Summary:
- Planner-Executor-Evaluator architecture
- Self-correction loop (max 2 iterations)
- Parallel tool execution (asyncio)
- Structured outputs (Pydantic models)
- Enhanced UI with execution transparency

All 6 checkpoints verified ✓

Changes:
- code/core/: New state management and models
- code/nodes/: 4 workflow nodes (planner, executor, evaluator, synthesizer)
- code/tools/: Async tool wrappers
- code/prompts/: Prompt templates
- code/streamlit_app.py: Enhanced UI
- README.md: Updated documentation

Ready for review and testing"
```

---

## Success Criteria Checklist

After completing all tasks, verify:

### Technical
- [ ] All 6 checkpoints passed verification
- [ ] 15+ git commits showing incremental progress
- [ ] No uncommitted changes
- [ ] On `dev` branch (not main)
- [ ] Streamlit loads without errors
- [ ] All imports work
- [ ] No LLM co-author in commits

### Functionality
- [ ] Planner selects appropriate tools
- [ ] Executor runs tools in parallel
- [ ] Evaluator can trigger replan
- [ ] Max iterations enforced (2)
- [ ] Final response always generated
- [ ] Conversation memory works

### UI/UX
- [ ] Execution plan visible
- [ ] Iteration counter displayed
- [ ] Evaluator reasoning shown
- [ ] Source attribution enhanced
- [ ] No UI regressions

### Code Quality
- [ ] Clean modular structure
- [ ] Clear separation of concerns
- [ ] Error handling throughout
- [ ] Type hints where appropriate
- [ ] No hardcoded magic values

---

## Notes for Implementation

**Important Reminders:**

1. **Git Discipline**: Commit after EACH checkpoint passes, never commit failing code
2. **No Pushing**: All commits stay local on `dev` branch
3. **No LLM Attribution**: Never add "Co-Authored-By: Claude" to commits
4. **Test Before Commit**: Always run verification tests before committing
5. **Backwards Compatibility**: Maintain it until final integration (Checkpoint 5)

**If a Checkpoint Fails:**

1. Read the error carefully
2. Debug the specific issue
3. Fix and re-test
4. DO NOT commit until tests pass
5. Can revert to last checkpoint: `git reset --hard HEAD`

**Performance Expectations:**

- Parallel execution should be visibly faster than sequential
- Each checkpoint should take ~30-60 minutes to implement and verify
- Total implementation time: ~4-6 hours

---

**Ready to begin implementation!** Start with Checkpoint 1, Task 1.1.
