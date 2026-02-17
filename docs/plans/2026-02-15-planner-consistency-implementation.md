# Enhanced Planner Prompt Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve tool selection consistency by adding explicit rules, keyword triggers, and examples to the planner prompt

**Architecture:** Single file modification to `code/prompts/planner_prompts.py` - add mandatory tool selection rules, decision matrix, and few-shot examples to the prompt template

**Tech Stack:** Python, LangChain prompts, OpenAI structured outputs

---

## Task 1: Add Mandatory Tool Selection Rules Section

**Files:**
- Modify: `code/prompts/planner_prompts.py:56-73` (after AVAILABLE TOOLS section)

**Step 1: Read current prompt structure**

Run: `cat code/prompts/planner_prompts.py`

Expected: See current prompt with TOOL SELECTION GUIDELINES section at lines 62-73

**Step 2: Add MANDATORY TOOL SELECTION RULES section**

Insert after line 40 (after AVAILABLE TOOLS list), before YOUR TASK section:

```python
    prompt += """
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

"""
```

**Step 3: Verify syntax**

Run: `python -m py_compile code/prompts/planner_prompts.py`

Expected: No syntax errors

**Step 4: Commit**

```bash
git add code/prompts/planner_prompts.py
git commit -m "feat: add mandatory tool selection rules to planner prompt"
```

---

## Task 2: Add Tool Combination Patterns Section

**Files:**
- Modify: `code/prompts/planner_prompts.py` (append after MANDATORY RULES)

**Step 1: Add TOOL COMBINATION PATTERNS section**

Insert after MANDATORY TOOL SELECTION RULES section:

```python
    prompt += """
TOOL COMBINATION PATTERNS:

Single Tool Cases:
- Poster request: OMDB only
- "How many" queries: SQL only (all databases)
- Qualitative search: Semantic only

Multi-Tool Cases:
- "Poster for top rated movie": SQL (find top rated) + OMDB (get poster)
- "Dark sci-fi from 2020": SQL (year filter) + Semantic (dark sci-fi atmosphere)

"""
```

**Step 2: Verify syntax**

Run: `python -m py_compile code/prompts/planner_prompts.py`

Expected: No syntax errors

**Step 3: Commit**

```bash
git add code/prompts/planner_prompts.py
git commit -m "feat: add tool combination patterns to planner prompt"
```

---

## Task 3: Add SQL Aggregation Rules Section

**Files:**
- Modify: `code/prompts/planner_prompts.py` (append after TOOL COMBINATION PATTERNS)

**Step 1: Add SQL AGGREGATION RULES section**

Insert after TOOL COMBINATION PATTERNS section:

```python
    prompt += """
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

"""
```

**Step 2: Verify syntax**

Run: `python -m py_compile code/prompts/planner_prompts.py`

Expected: No syntax errors

**Step 3: Commit**

```bash
git add code/prompts/planner_prompts.py
git commit -m "feat: add SQL aggregation rules to planner prompt"
```

---

## Task 4: Add Few-Shot Examples Section

**Files:**
- Modify: `code/prompts/planner_prompts.py` (append after SQL AGGREGATION RULES)

**Step 1: Add FEW-SHOT EXAMPLES section**

Insert after SQL AGGREGATION RULES section:

```python
    prompt += """
FEW-SHOT EXAMPLES:

Example 1: Poster Request
Q: "Show me the poster for Ex Machina"
Correct Plan:
  use_omdb: true
  omdb_title: "Ex Machina"
  reasoning: "'poster' keyword detected → OMDB mandatory"

Example 2: Semantic Search
Q: "Films with dark investigation atmosphere"
Correct Plan:
  use_semantic: true
  semantic_query: "dark investigation thriller mystery suspense atmosphere"
  reasoning: "'atmosphere' keyword detected → semantic mandatory"

Example 3: SQL Aggregation
Q: "How many genres are in our databases?"
Correct Plan:
  use_sql: true
  sql_query: "SELECT COUNT(DISTINCT genre) FROM [table]" (for EACH database)
  reasoning: "'how many' detected → SQL on all databases for aggregation"

Example 4: Combination Query
Q: "Poster for the highest rated thriller from 2020"
Correct Plan:
  use_sql: true
  sql_query: "SELECT title FROM movies WHERE genre='Thriller' AND year=2020 ORDER BY rating DESC LIMIT 1"
  use_omdb: true
  omdb_title: "{result from SQL}"
  reasoning: "SQL finds movie, OMDB gets poster"

Example 5: Semantic Similarity
Q: "Movies like Blade Runner"
Correct Plan:
  use_semantic: true
  semantic_query: "dystopian cyberpunk noir future artificial intelligence replicants"
  reasoning: "'like' keyword detected → semantic with descriptive query, NOT just title"

"""
```

**Step 2: Verify syntax**

Run: `python -m py_compile code/prompts/planner_prompts.py`

Expected: No syntax errors

**Step 3: Commit**

```bash
git add code/prompts/planner_prompts.py
git commit -m "feat: add few-shot examples to planner prompt"
```

---

## Task 5: Update TOOL SELECTION GUIDELINES Section

**Files:**
- Modify: `code/prompts/planner_prompts.py:62-73`

**Step 1: Replace generic guidelines with specific ones**

Replace the existing TOOL SELECTION GUIDELINES section (lines 62-67) with:

```python
TOOL SELECTION GUIDELINES:
- Check MANDATORY RULES first - if keywords match, tool is REQUIRED
- For ambiguous queries, use combination patterns as reference
- SQL queries MUST use exact table/column names from catalog above
- Semantic queries MUST be descriptive natural language (not just keywords)
- OMDB titles should be exact movie names (not descriptions)
- When in doubt between tools, refer to FEW-SHOT EXAMPLES above
```

**Step 2: Verify syntax**

Run: `python -m py_compile code/prompts/planner_prompts.py`

Expected: No syntax errors

**Step 3: Commit**

```bash
git add code/prompts/planner_prompts.py
git commit -m "feat: update tool selection guidelines with rule references"
```

---

## Task 6: Create Test Suite Script

**Files:**
- Create: `test_planner_consistency.py`

**Step 1: Create test script**

```python
"""
Test suite for planner consistency
Runs 10 test queries and checks tool selection
"""
import streamlit as st
from code.utils import build_db_catalog
from code.core.agent import app
from code.config import DB_FOLDER_PATH

# Test queries from design doc
TEST_QUERIES = [
    # OMDB Tests
    {
        "query": "Show me the poster for Ex Machina",
        "expected_tools": {"omdb": True},
        "expected_params": {"omdb_title": "Ex Machina"}
    },
    {
        "query": "Who directed Inception?",
        "expected_tools": {"omdb": True},
        "expected_params": {"omdb_title": "Inception"}
    },
    # Semantic Tests
    {
        "query": "Dark investigation movies with suspense",
        "expected_tools": {"semantic": True},
        "expected_params": {"semantic_query_contains": ["dark", "investigation", "suspense"]}
    },
    {
        "query": "Films like Blade Runner",
        "expected_tools": {"semantic": True},
        "expected_params": {"semantic_query_contains": ["dystopian", "sci-fi", "noir"]}
    },
    # SQL Tests
    {
        "query": "How many genres are in our databases?",
        "expected_tools": {"sql": True},
        "expected_params": {"sql_aggregation": True}
    },
    {
        "query": "Action movies from 2020",
        "expected_tools": {"sql": True},
        "expected_params": {"sql_filters": ["genre", "year"]}
    },
    # Combination Tests
    {
        "query": "Poster for top rated thriller",
        "expected_tools": {"sql": True, "omdb": True},
        "expected_params": {}
    },
    {
        "query": "Dark sci-fi from 2015-2020",
        "expected_tools": {"sql": True, "semantic": True},
        "expected_params": {}
    },
]

def run_test_suite():
    """Run all test queries and report results"""
    print("=" * 60)
    print("PLANNER CONSISTENCY TEST SUITE")
    print("=" * 60)

    catalog = build_db_catalog(DB_FOLDER_PATH)
    passed = 0
    failed = 0

    for idx, test in enumerate(TEST_QUERIES, 1):
        print(f"\nTest {idx}: {test['query']}")
        print(f"Expected tools: {test['expected_tools']}")

        # Run planner (extract just the planning step)
        from code.nodes.planner import planner_node

        state = {
            "original_question": test['query'],
            "messages": [],
            "db_catalog": catalog,
            "iteration_count": 0,
            "previous_plans": [],
            "previous_results": {},
            "replan_instructions": ""
        }

        result = planner_node(state)
        plan = result["execution_plan"]

        # Check tool selection
        tools_selected = {
            "sql": plan.get("use_sql", False),
            "semantic": plan.get("use_semantic", False),
            "omdb": plan.get("use_omdb", False),
            "web": plan.get("use_web", False)
        }

        # Filter to only selected tools
        tools_selected = {k: v for k, v in tools_selected.items() if v}

        # Check if matches expected
        if tools_selected == test["expected_tools"]:
            print(f"✅ PASS - Tools: {tools_selected}")
            passed += 1
        else:
            print(f"❌ FAIL - Got: {tools_selected}, Expected: {test['expected_tools']}")
            print(f"   Reasoning: {plan.get('reasoning', 'N/A')}")
            failed += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{len(TEST_QUERIES)} passed")
    print(f"Pass rate: {100 * passed / len(TEST_QUERIES):.1f}%")
    print("=" * 60)

    return passed == len(TEST_QUERIES)

if __name__ == "__main__":
    success = run_test_suite()
    exit(0 if success else 1)
```

**Step 2: Run test suite (expect failures initially)**

Run: `python test_planner_consistency.py`

Expected: Some tests may fail with current prompt (baseline)

**Step 3: Commit test suite**

```bash
git add test_planner_consistency.py
git commit -m "test: add planner consistency test suite"
```

---

## Task 7: Run Test Suite and Verify Improvements

**Files:**
- Test: `test_planner_consistency.py`

**Step 1: Run test suite with enhanced prompt**

Run: `python test_planner_consistency.py`

Expected: Higher pass rate than baseline (target: 100%)

**Step 2: Check consistency (run 3x)**

Run test 3 times to verify same results:
```bash
python test_planner_consistency.py
python test_planner_consistency.py
python test_planner_consistency.py
```

Expected: Same tool selections across all 3 runs

**Step 3: Document results**

Create file `test_results.md` with:
```markdown
# Planner Consistency Test Results

## Baseline (before enhancements)
- Pass rate: X%
- Failed queries: [list]

## After Enhancements
- Pass rate: Y%
- Failed queries: [list]

## Consistency Check (3 runs)
- Run 1: Y%
- Run 2: Y%
- Run 3: Y%
- Consistent: [Yes/No]
```

**Step 4: Commit results**

```bash
git add test_results.md
git commit -m "docs: add planner consistency test results"
```

---

## Task 8: Manual Testing in Streamlit App

**Files:**
- Test: Manual testing in Streamlit UI

**Step 1: Launch Streamlit app**

Run: `streamlit run code/streamlit_app.py`

Expected: App starts successfully

**Step 2: Test the 3 example queries from sidebar**

Click each example button:
1. "Combien de genres de films y a-t-il dans nos bases de données ?"
2. "Montre moi l'affiche de Ex Machina."
3. "Propose des films d'enquêtes avec une ambiance sombre et une intrigue à suspense."

Expected behavior:
1. Query 1: Should use SQL on all DBs, show detail + total
2. Query 2: Should use OMDB, show poster image
3. Query 3: Should use semantic search, return relevant films from DB

**Step 3: Check Langfuse traces**

Go to https://cloud.langfuse.com and verify:
- Tool selection matches expected for each query
- Execution plan reasoning mentions keyword triggers
- Consistent across multiple runs

**Step 4: Document manual test results**

Add to `test_results.md`:
```markdown
## Manual Testing in Streamlit

Example 1: "Combien de genres..."
- Tools used: [list]
- Result quality: [Good/Issues]
- Langfuse trace: [link]

Example 2: "Affiche de Ex Machina"
- Tools used: [list]
- Result quality: [Good/Issues]
- Langfuse trace: [link]

Example 3: "Films d'enquêtes sombres"
- Tools used: [list]
- Result quality: [Good/Issues]
- Langfuse trace: [link]
```

**Step 5: Commit manual test results**

```bash
git add test_results.md
git commit -m "docs: add manual testing results from Streamlit"
```

---

## Task 9: Iterate on Prompt if Needed

**Files:**
- Modify: `code/prompts/planner_prompts.py` (if tests fail)

**Step 1: Analyze failures**

If any tests failed, review:
- Langfuse traces for incorrect tool selections
- Planner reasoning field for why it chose wrong tools
- Pattern of failures (specific keywords missed?)

**Step 2: Refine prompt rules**

If needed, update:
- Add missing keywords to trigger rules
- Clarify ambiguous examples
- Add more specific combination patterns

**Step 3: Re-run tests**

Run: `python test_planner_consistency.py`

Expected: Improved pass rate

**Step 4: Commit refinements**

```bash
git add code/prompts/planner_prompts.py
git commit -m "refine: update planner prompt based on test failures"
```

**Step 5: Repeat until 100% pass rate**

Continue iterating until all 10 tests pass consistently

---

## Task 10: Final Verification and Documentation

**Files:**
- Update: `README.md` (if needed)
- Update: `docs/plans/2026-02-15-planner-consistency-design.md`

**Step 1: Final test run**

Run: `python test_planner_consistency.py`

Expected: 100% pass rate

**Step 2: Update design doc with actual results**

Update design doc section "Expected Outcomes" with actual metrics:
```markdown
## Actual Results (2026-02-15)

- Test suite pass rate: 100% (10/10)
- Consistency across 3 runs: 100%
- OMDB usage for poster requests: 100%
- Semantic usage for qualitative queries: 100%
- Manual testing: All 3 examples work correctly
```

**Step 3: Commit final updates**

```bash
git add docs/plans/2026-02-15-planner-consistency-design.md
git commit -m "docs: update design doc with actual implementation results"
```

**Step 4: Create summary commit**

```bash
git commit --allow-empty -m "feat: complete planner consistency enhancement

Enhanced planner prompt with:
- Mandatory tool selection rules with keyword triggers
- Tool combination patterns
- SQL aggregation rules for multi-DB queries
- Few-shot examples for common patterns
- Updated selection guidelines

Results:
- Test suite: 100% pass rate (10/10 queries)
- Consistency: 100% across multiple runs
- All manual tests passing

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Success Criteria

✅ All tasks completed
✅ Test suite: 100% pass rate (10/10 queries)
✅ Consistency: Same tool selection across 3 runs
✅ Manual testing: All 3 example queries work correctly
✅ Langfuse traces: Show correct tool selection reasoning
✅ No breaking changes to existing functionality
✅ Code committed with clear messages

---

## Rollback Plan

If issues arise:

```bash
# Revert to previous version
git log --oneline  # Find commit before changes
git revert <commit-hash>  # Revert specific commit

# Or reset to before enhancement
git reset --hard HEAD~10  # Reset 10 commits back
```

Design doc preserved for future reference even if rollback needed.
