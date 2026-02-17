# Planner Consistency Test Results

## Summary

This document tracks the results of the planner consistency tests before and after implementing enhanced prompt engineering improvements.

## Test Methodology

The test suite (`test_planner_consistency.py`) evaluates 8 different user queries across various scenarios:
1. Poster request for specific movie (Ex Machina)
2. Director query (Inception)
3. Thematic search (dark investigation movies)
4. Similarity search (films like Blade Runner)
5. Database statistics (genre count)
6. Filtered search (action movies from 2020)
7. Combined query (poster for top rated thriller)
8. Complex filtered search (dark sci-fi from 2015-2020)

Each test verifies that the planner selects the correct tools (SQL, Semantic Search, OMDB) based on the query.

## Baseline Results (Before Enhancements)

**Pass Rate:** 75% (6/8 passed)

The baseline was established before implementing the enhanced prompt engineering improvements.

## Current Results (After Enhancements)

### Run 1
- **Date:** 2026-02-15
- **Pass Rate:** 75% (6/8 passed)
- **Passed Tests:** 1, 4, 5, 6, 7, 8
- **Failed Tests:** 2, 3

### Run 2
- **Date:** 2026-02-15
- **Pass Rate:** 75% (6/8 passed)
- **Passed Tests:** 1, 4, 5, 6, 7, 8
- **Failed Tests:** 2, 3

### Run 3
- **Date:** 2026-02-15
- **Pass Rate:** 75% (6/8 passed)
- **Passed Tests:** 1, 4, 5, 6, 7, 8
- **Failed Tests:** 2, 3

## Consistency Analysis

**Result:** 100% Consistent

All three test runs produced identical results:
- Same pass rate (75%)
- Same tests passed (1, 4, 5, 6, 7, 8)
- Same tests failed (2, 3)
- Similar reasoning patterns for failed tests

This demonstrates that the planner is deterministic and stable in its decision-making process.

## Detailed Failure Analysis

### Test 2: "Who directed Inception?"

**Expected Tools:** `{'omdb': True}`

**Actual Tools:** `{'sql': True, 'omdb': True}`

**Issue:** The planner is selecting both SQL and OMDB when only OMDB is needed.

**Reasoning (Run 1):**
> "The question asks for the director of 'Inception', which requires specific metadata about the movie. The OMDB API is used to retrieve detailed information about the movie, including the director. Additionally, I will query the SQL databases to check if 'Inception' is listed there and to find the director from those sources as well."

**Reasoning (Run 2):**
> "The question asks for the director of 'Inception', which requires both SQL to check the databases for the director and OMDB to ensure accurate metadata retrieval."

**Reasoning (Run 3):**
> "The question asks for the director of 'Inception', which requires specific metadata about the movie. The OMDB API is used to retrieve detailed information about the movie, including the director. Additionally, I will query the SQL databases to check if 'Inception' is listed there and to confirm the director's name."

**Analysis:**
The planner is being overly cautious and trying to check both internal databases and external OMDB API. While this provides redundancy, it's inefficient. For specific metadata queries about well-known movies, OMDB alone should suffice. The prompt may need stronger guidance about when SQL is truly necessary vs. when OMDB can handle the query independently.

### Test 3: "Dark investigation movies with suspense"

**Expected Tools:** `{'semantic': True}`

**Actual Tools:** `{'sql': True, 'semantic': True}`

**Issue:** The planner is selecting both SQL and Semantic Search when only Semantic Search is needed.

**Reasoning (Run 1):**
> "The query involves finding movies with a specific atmosphere (dark investigation with suspense), which requires both SQL for structured filtering and Semantic Search for qualitative similarity. SQL will filter by genre and description, while Semantic Search will capture the mood and tone."

**Reasoning (Run 2):**
> "The query involves finding movies with a specific atmosphere (dark investigation with suspense), which requires both SQL for structured filtering and semantic search for qualitative similarity. SQL will filter by genre and description, while semantic search will capture the mood and themes."

**Reasoning (Run 3):**
> "The query involves finding movies with a specific atmosphere (dark investigation with suspense), which requires both SQL for structured filtering and semantic search for qualitative similarity. SQL will filter by genre and description, while semantic search will enhance the results based on mood and atmosphere. OMDB is not needed as we are not requesting detailed metadata or visuals."

**Analysis:**
This is a purely thematic/atmospheric query without any structured criteria (no year, no specific genre from predefined list, no rating threshold). The planner is incorrectly assuming that SQL can help with filtering by "genre and description," but SQL cannot effectively filter on subjective terms like "dark," "investigation," and "suspense." This is exactly what Semantic Search excels at. The prompt needs to emphasize that when queries are purely about mood, atmosphere, or themes without structured criteria, Semantic Search alone should be used.

## Observations

1. **Consistency:** The planner shows excellent consistency across runs, producing identical results each time.

2. **Conservative Approach:** Both failures stem from the planner being overly conservative and selecting additional tools "just to be safe."

3. **Tool Combination Logic:** The planner seems to default to combining tools when there's any ambiguity, rather than choosing the most appropriate single tool.

4. **Reasoning Quality:** The reasoning provided is logical and well-articulated, showing that the planner understands what each tool does. However, it's not optimally applying the principle of minimal tool selection.

## Recommendations for Further Improvement

1. **Strengthen Single-Tool Guidance:** Add explicit rules about when a single tool is sufficient:
   - "If a query can be fully answered by one tool, do not add additional tools"
   - "Prefer the most specialized tool for the task rather than combining multiple tools"

2. **OMDB vs SQL Clarity:** Add guidance that for specific movie metadata (director, actors, plot, ratings from OMDB/IMDb):
   - Use OMDB alone unless the query explicitly requires filtering/aggregation across the database
   - Example: "Who directed X?" → OMDB only
   - Example: "How many movies did director X make in our database?" → SQL + potentially OMDB

3. **Semantic-Only Scenarios:** Strengthen the guidance for pure thematic queries:
   - "If the query contains ONLY subjective/thematic terms (mood, atmosphere, themes) with NO structured criteria (year, genre, rating), use Semantic Search alone"
   - Add examples of semantic-only queries vs. hybrid queries

4. **Cost/Efficiency Emphasis:** Add a principle about efficiency:
   - "Choose the minimum set of tools needed to answer the query effectively"
   - "Additional tools should only be added if they provide essential information not available from the primary tool"

## Conclusion

The enhanced prompt engineering has maintained the baseline 75% pass rate with perfect consistency. While the pass rate hasn't improved, the consistency is a positive indicator that the planner's decision-making is stable and predictable. The two persistent failures are both related to over-selection of tools rather than under-selection, which suggests the prompt could benefit from stronger guidance on tool minimization and clearer decision boundaries between single-tool and multi-tool scenarios.
