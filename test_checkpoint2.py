"""
Checkpoint 2 Verification Tests
Tests the planner node with 3 different query types to verify tool selection logic
"""

from code.nodes.planner import planner_node
from code.utils import build_db_catalog
from code.config import DB_FOLDER_PATH

print("=" * 60)
print("CHECKPOINT 2 VERIFICATION TESTS")
print("=" * 60)
print()

# Build catalog once for all tests
db_catalog = build_db_catalog(DB_FOLDER_PATH)

# =============================================================================
# Test 1: SQL query (structured data)
# =============================================================================
print("TEST 1: SQL query (structured data)")
print("-" * 60)

state = {
    'original_question': 'How many comedy movies are in the database?',
    'messages': [],
    'db_catalog': db_catalog,
    'iteration_count': 0,
    'previous_plans': [],
    'previous_results': {}
}

result = planner_node(state)
plan = result['execution_plan']

print(f'Query: How many comedy movies are in the database?')
print(f'  SQL: {plan["use_sql"]}')
print(f'  Semantic: {plan["use_semantic"]}')
print(f'  Reasoning: {plan["reasoning"][:150]}...')
print()

# Verify expectations
assert plan["use_sql"] == True, "Should select SQL for counting"
print("[PASS] TEST 1: SQL selected for counting query")
print()

# =============================================================================
# Test 2: Semantic selection
# =============================================================================
print("TEST 2: Semantic selection")
print("-" * 60)

state = {
    'original_question': 'Find movies with plots similar to The Matrix - dystopian themes about questioning reality',
    'messages': [],
    'db_catalog': db_catalog,
    'iteration_count': 0,
    'previous_plans': [],
    'previous_results': {}
}

result = planner_node(state)
plan = result['execution_plan']

print(f'Query: Find movies with plots similar to The Matrix - dystopian themes about questioning reality')
print(f'  SQL: {plan["use_sql"]}')
print(f'  Semantic: {plan["use_semantic"]}')
print(f'  Semantic query: {plan.get("semantic_query", "N/A")}')
print(f'  Reasoning: {plan["reasoning"][:150]}...')
print()

# Verify expectations
assert plan["use_semantic"] == True, "Should select semantic for plot-based search"
print("[PASS] TEST 2: Semantic selected for plot-based query")
print()

# =============================================================================
# Test 3: Hybrid query
# =============================================================================
print("TEST 3: Hybrid query")
print("-" * 60)

state = {
    'original_question': 'Find drama movies from 2015-2020 with plots about redemption and second chances',
    'messages': [],
    'db_catalog': db_catalog,
    'iteration_count': 0,
    'previous_plans': [],
    'previous_results': {}
}

result = planner_node(state)
plan = result['execution_plan']

print(f'Query: Find drama movies from 2015-2020 with plots about redemption and second chances')
print(f'  SQL: {plan["use_sql"]}')
print(f'  Semantic: {plan["use_semantic"]}')
print(f'  SQL query: {plan.get("sql_query", "N/A")[:100]}...' if plan.get("sql_query") else '  SQL query: N/A')
print(f'  Semantic query: {plan.get("semantic_query", "N/A")}')
print(f'  Reasoning: {plan["reasoning"][:150]}...')
print()

# Verify expectations
assert plan["use_sql"] == True and plan["use_semantic"] == True, \
    "Should select both SQL (year/genre filter) and semantic (redemption themes)"
print("[PASS] TEST 3: Both SQL and semantic selected for hybrid query")
print()

# =============================================================================
# Summary
# =============================================================================
print("=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)
print()
print("Test cases verified:")
print("[PASS] SQL selection for counting/filtering")
print("[PASS] Semantic selection for descriptive queries")
print("[PASS] Combined selection for hybrid queries")
print()
print("Ready for checkpoint commit!")
