"""
Test suite for planner consistency
Runs 10 test queries and checks tool selection
"""
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

from utils import build_db_catalog
from config import DB_FOLDER_PATH

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
        from nodes.planner import planner_node

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
            print(f"[PASS] Tools: {tools_selected}")
            passed += 1
        else:
            print(f"[FAIL] Got: {tools_selected}, Expected: {test['expected_tools']}")
            print(f"       Reasoning: {plan.get('reasoning', 'N/A')}")
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
