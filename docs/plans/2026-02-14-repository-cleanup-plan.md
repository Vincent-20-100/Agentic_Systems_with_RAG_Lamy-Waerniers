# Repository Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Clean up repository after Checkpoints 1-5 refactoring by removing obsolete files and updating documentation.

**Architecture:** Sequential cleanup with verification - verify Langfuse compatibility, delete old architecture files, update README to reflect new Planner→Executor→Evaluator→Synthesizer pattern, test, and commit.

**Tech Stack:** Git, Python imports verification, README markdown

---

## Task 1: Verify Langfuse Integration Compatibility

**Files:**
- Read: `code/streamlit_app.py`
- Read: `code/config.py`

**Step 1: Check Langfuse integration in streamlit_app.py**

Run:
```bash
grep -n "langfuse" code/streamlit_app.py
```

Expected output:
- Line with `from langfuse.langchain import CallbackHandler`
- Line with `langfuse_handler = CallbackHandler()`
- Line with `"callbacks": [langfuse_handler]` in config dict

**Step 2: Verify config dict usage with app.invoke()**

Run:
```bash
grep -A 5 "callbacks.*langfuse_handler" code/streamlit_app.py
```

Expected: Config dict passed to `app.invoke()` or `app.stream()` method

**Step 3: Check Langfuse configuration**

Run:
```bash
grep -n "LANGFUSE" code/config.py
```

Expected: LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY defined

**Step 4: Document verification result**

Create verification note:
```bash
echo "✓ Langfuse integration verified:
- CallbackHandler imported from langfuse.langchain
- Handler instance created: langfuse_handler
- Passed to LangGraph via config={'callbacks': [langfuse_handler]}
- LangGraph supports LangChain callbacks (official documentation)
- No changes needed for new workflow" > langfuse_verification.txt
```

**Step 5: Commit verification note**

```bash
git add langfuse_verification.txt
git commit -m "docs: verify langfuse integration with new workflow"
```

---

## Task 2: Delete Obsolete Architecture Files

**Files:**
- Delete: `code/agent.py`
- Delete: `code/models.py`
- Delete: `code/nodes.py`
- Delete: `code/tools.py`

**Step 1: Verify files exist and are obsolete**

Run:
```bash
ls -la code/agent.py code/models.py code/nodes.py code/tools.py
```

Expected: All 4 files exist

**Step 2: Double-check these files are not imported anywhere**

Run:
```bash
grep -r "from code.agent import\|from agent import" code/ --include="*.py" | grep -v "code/core/agent.py"
grep -r "from code.models import\|from models import" code/ --include="*.py" | grep -v "code/core/models.py"
grep -r "from code.nodes import\|from nodes import" code/ --include="*.py" | grep -v "code/nodes/"
grep -r "from code.tools import\|from tools import" code/ --include="*.py" | grep -v "code/tools/"
```

Expected: No results (or only results from the files themselves)

**Step 3: Remove obsolete files using git rm**

Run:
```bash
git rm code/agent.py code/models.py code/nodes.py code/tools.py
```

Expected output:
```
rm 'code/agent.py'
rm 'code/models.py'
rm 'code/nodes.py'
rm 'code/tools.py'
```

**Step 4: Verify files are staged for deletion**

Run:
```bash
git status
```

Expected: Shows 4 files deleted in staging area

**Step 5: Do NOT commit yet - wait for README update**

(Files staged, will commit together with README changes in Task 4)

---

## Task 3: Update README Architecture and Workflow Sections

**Files:**
- Modify: `README.md` (lines ~28-50 for architecture, add workflow section)

**Step 1: Read current README architecture section**

Run:
```bash
sed -n '28,50p' README.md
```

Expected: Current description of old architecture

**Step 2: Update "What Makes It Special?" section**

Find the section starting with "Unlike traditional chatbots, Albert Query:" (around line 34)

Replace the bullet points with:
```markdown
Unlike traditional chatbots, Albert Query:
- **Agentic architecture** - Planner→Executor→Evaluator→Synthesizer workflow with self-correction
- **Self-correcting loops** - Evaluator can request additional data if initial results insufficient (max 2 iterations)
- **Parallel execution** - All selected tools run simultaneously for faster responses
- **Multi-source intelligence** - Combines SQL databases, vector search, external APIs, and web search
- **Semantic understanding** - Uses OpenAI embeddings to find movies by plot similarity
- **Source attribution** - Always shows where information comes from
- **Context-aware** - Maintains conversation history for follow-up questions
```

**Step 3: Add new Architecture section after "Use Cases"**

After the Use Cases section (around line 48), add:

```markdown
---

## Architecture

### Agentic Workflow Pattern

Albert Query uses a **Planner-Executor-Evaluator-Synthesizer** pattern with self-correction capabilities:

```
┌─────────────────────────────────────────────────┐
│                    START                        │
└──────────────────┬──────────────────────────────┘
                   ↓
         ┌─────────────────┐
         │    PLANNER      │  ← Analyzes query, selects tools
         └────────┬────────┘
                  ↓
         ┌─────────────────┐
         │    EXECUTOR     │  ← Runs tools in parallel
         └────────┬────────┘
                  ↓
         ┌─────────────────┐
         │   EVALUATOR     │  ← Assesses data sufficiency
         └────────┬────────┘
                  ↓
          [Data Sufficient?]
           ↙              ↘
    [No - Replan]    [Yes - Continue]
           ↓                ↓
    (back to Planner)  ┌─────────────────┐
    (max 2 iterations) │  SYNTHESIZER    │  ← Generates answer
                       └────────┬────────┘
                                ↓
                              END
```

### Key Features

- **Planner**: LLM-powered tool selection based on query analysis
- **Executor**: Parallel tool execution using asyncio for speed
- **Evaluator**: Assesses if data is sufficient; can trigger replanning
- **Synthesizer**: Natural language response generation with source attribution
- **Loop Safety**: Maximum 2 iterations prevents infinite loops
- **State Management**: LangGraph checkpointing maintains conversation context

### Available Tools

1. **SQL Database** - Structured queries on 8,000+ movies/shows (filters, aggregations)
2. **Semantic Search** - Vector similarity search for plot-based discovery
3. **OMDB API** - Enriched metadata (cast, ratings, detailed plots)
4. **Web Search** - Current information and trending topics
```

**Step 4: Test README renders correctly**

Run:
```bash
python -c "
import re
with open('README.md', 'r', encoding='utf-8') as f:
    content = f.read()
    # Check new sections exist
    assert 'Agentic architecture' in content, 'Missing agentic architecture mention'
    assert 'Self-correcting loops' in content, 'Missing self-correction mention'
    assert 'Parallel execution' in content, 'Missing parallel execution mention'
    assert 'PLANNER' in content, 'Missing planner in workflow'
    assert 'EXECUTOR' in content, 'Missing executor in workflow'
    assert 'EVALUATOR' in content, 'Missing evaluator in workflow'
    assert 'SYNTHESIZER' in content, 'Missing synthesizer in workflow'
    print('✓ README update verified - all new sections present')
"
```

Expected: `✓ README update verified - all new sections present`

**Step 5: Do NOT commit yet - wait for final commit in Task 4**

(README changes staged, will commit together with deleted files)

---

## Task 4: Final Verification and Commit

**Files:**
- Staged: `code/agent.py` (deleted)
- Staged: `code/models.py` (deleted)
- Staged: `code/nodes.py` (deleted)
- Staged: `code/tools.py` (deleted)
- Staged: `README.md` (modified)
- Staged: `langfuse_verification.txt` (new)

**Step 1: Verify import still works**

Run:
```bash
python -c "from code.core.agent import app; print('✓ Import successful')"
```

Expected: `✓ Import successful`

**Step 2: Check git status before commit**

Run:
```bash
git status
```

Expected:
- 4 files deleted: agent.py, models.py, nodes.py, tools.py
- 1 file modified: README.md
- 1 file added: langfuse_verification.txt

**Step 3: Stage all changes**

Run:
```bash
git add -A
```

**Step 4: Create cleanup commit**

Run:
```bash
git commit -m "chore: cleanup repository after checkpoint 1-5 refactoring

- Remove obsolete files from old architecture:
  - code/agent.py (replaced by code/core/agent.py)
  - code/models.py (replaced by code/core/state.py + models.py)
  - code/nodes.py (replaced by modular code/nodes/*)
  - code/tools.py (replaced by modular code/tools/*)

- Update README to reflect new architecture:
  - Planner → Executor → Evaluator → Synthesizer flow
  - Self-correction loop with max 2 iterations
  - Parallel tool execution
  - New Architecture section with workflow diagram

- Verify Langfuse integration compatible with new workflow

All obsolete files safely preserved in git history (commit bb82192)"
```

Expected: Commit successful with message

**Step 5: Verify commit**

Run:
```bash
git log --oneline -1
git show --stat
```

Expected: Shows cleanup commit with all file changes

---

## Task 5: Post-Cleanup Verification

**Files:**
- Test: Application still runs

**Step 1: Test import again after commit**

Run:
```bash
python -c "from code.core.agent import app; print('✓ Import still works after cleanup')"
```

Expected: `✓ Import still works after cleanup`

**Step 2: Test Streamlit loads**

Run:
```bash
timeout 30 streamlit run code/streamlit_app.py &
sleep 15
curl -s -f http://localhost:8501 > /dev/null && echo "✓ Streamlit loads successfully" || echo "❌ Streamlit failed to load"
pkill -f streamlit
```

Expected: `✓ Streamlit loads successfully`

**Step 3: Check for any broken imports or errors**

Run:
```bash
python -c "
import sys
sys.path.insert(0, 'code')
try:
    from core.agent import app
    from core.state import AgentState
    from core.models import ExecutionPlan, EvaluatorDecision
    from nodes.planner import planner_node
    from nodes.executor import executor_node
    from nodes.evaluator import evaluator_node
    from nodes.synthesizer import synthesizer_node
    print('✓ All critical imports working')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
```

Expected: `✓ All critical imports working`

**Step 4: Remove verification file (cleanup)**

Run:
```bash
git rm langfuse_verification.txt
git commit -m "chore: remove temporary verification file"
```

Expected: Verification file removed

**Step 5: Final status check**

Run:
```bash
git status
echo ""
echo "=== CLEANUP SUMMARY ==="
echo "✓ 4 obsolete files deleted"
echo "✓ README updated with new architecture"
echo "✓ Langfuse integration verified"
echo "✓ Application compiles and runs"
echo "✓ Clean git history"
echo ""
echo "Repository cleanup complete!"
```

Expected: Clean working tree, all checkmarks green

---

## Verification Checklist

After completing all tasks, verify:

- [ ] `code/agent.py` deleted
- [ ] `code/models.py` deleted
- [ ] `code/nodes.py` deleted
- [ ] `code/tools.py` deleted
- [ ] README describes Planner→Executor→Evaluator→Synthesizer pattern
- [ ] README includes self-correction loop explanation
- [ ] README mentions parallel execution
- [ ] README has new Architecture section with workflow diagram
- [ ] Langfuse integration code reviewed and verified compatible
- [ ] `python -c "from code.core.agent import app"` works
- [ ] Streamlit application loads without errors
- [ ] Git commit created with descriptive message
- [ ] Git history is clean (1-2 commits for cleanup)
- [ ] No broken imports or missing files

---

## Rollback Procedure

If issues arise during cleanup:

```bash
# Undo last commit (keep changes staged)
git reset --soft HEAD~1

# Or completely undo cleanup
git reset --hard HEAD~1

# Restore deleted files from previous commit
git checkout HEAD~1 -- code/agent.py code/models.py code/nodes.py code/tools.py
```

---

## Success Criteria

Cleanup is complete when:
1. All 4 obsolete files successfully removed from repository
2. README accurately describes new agentic architecture
3. Application imports and starts without errors
4. Langfuse integration verified as compatible
5. Clean git history with descriptive commit message
6. No regression in functionality (Streamlit loads, imports work)
