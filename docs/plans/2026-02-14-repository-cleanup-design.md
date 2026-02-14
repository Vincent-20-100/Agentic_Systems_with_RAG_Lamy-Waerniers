# Repository Cleanup Design

**Date:** 2026-02-14
**Status:** Approved
**Purpose:** Clean up repository after Checkpoints 1-5 refactoring

---

## 1. Scope & Objectives

### Goal
Clean up the repository after the Checkpoints 1-5 refactoring to remove obsolete files and update documentation to reflect the new agentic architecture.

### Success Criteria
- Old architecture files removed
- README accurately describes new Planner→Executor→Evaluator→Synthesizer pattern
- Langfuse integration verified as compatible
- Application compiles and runs without errors
- Clean git commit with clear description

### Out of Scope
- Checkpoint 6 implementation (UI polish)
- Performance optimizations
- Adding new features

---

## 2. Files to Delete

### Obsolete Files from Pre-Checkpoint Architecture

| File | Reason | Replacement |
|------|--------|-------------|
| `code/agent.py` | Old workflow without evaluator/loop | `code/core/agent.py` |
| `code/models.py` | Old AgentState definition | `code/core/state.py` + `code/core/models.py` |
| `code/nodes.py` | Monolithic node file | `code/nodes/planner.py`, `executor.py`, `evaluator.py`, `synthesizer.py` |
| `code/tools.py` | Monolithic tool file | `code/tools/sql_tool.py`, `semantic_tool.py`, `omdb_tool.py`, `web_tool.py` |

### Files to Keep
- All files in `code/core/` ✅
- All files in `code/nodes/` ✅
- All files in `code/prompts/` ✅
- All files in `code/tools/` ✅
- `code/config.py`, `code/utils.py`, `code/embedding.py` ✅
- `code/streamlit_app.py` ✅
- All notebooks, data files, docs ✅

**Rationale:** Old files are safely preserved in git history (commit bb82192). Keeping them creates confusion about which files are active in the current architecture.

---

## 3. Langfuse Integration Verification

### Current Integration
```python
from langfuse.langchain import CallbackHandler
langfuse_handler = CallbackHandler()
# ...
config = {"callbacks": [langfuse_handler]}
result = app.invoke(inputs, config=config)
```

### Verification Steps
1. Check that `CallbackHandler` is compatible with LangGraph's `.invoke()` and `.stream()` methods
2. Verify callback is passed correctly in config dict
3. Confirm no breaking changes needed for new workflow architecture

### Expected Result
Code review confirms integration is compatible (LangGraph supports LangChain callbacks as per official documentation).

---

## 4. README Updates

### Sections to Update

#### Architecture Section (~lines 18-50)
**Before:** "Plans before acting → Individual tool nodes → Synthesizer"

**After:** "Planner → Executor (parallel tools) → Evaluator → Synthesizer with self-correction loop"

**Additions:**
- Max iteration safety (prevents infinite loops)
- Evaluator can trigger replanning when data insufficient
- Parallel tool execution in Executor

#### Workflow Section
Update workflow diagram/description to show:
```
START → Planner → Executor → Evaluator → Decision
                                  ↓
                            [Sufficient?]
                            ↙         ↘
                        Replan      Synthesizer → END
                          ↓
                       (back to Planner, max 2 iterations)
```

#### Features Section
**Add:**
- "Self-correction loop" - System can replan when initial data is insufficient
- "Parallel execution" - All selected tools run simultaneously
- "Iteration safety" - Maximum 2 iterations to prevent runaway loops

### Sections to Keep As-Is
- Installation instructions ✅
- Monitoring with Langfuse ✅
- Use cases ✅
- Contributors ✅
- License ✅

---

## 5. Verification & Testing

### Pre-cleanup Checks
- Git status is clean (all changes committed)
- On `dev` branch

### Post-cleanup Verification
1. **Import test:** `python -c "from code.core.agent import app; print('✓ Import successful')"`
2. **Streamlit startup test:** `streamlit run code/streamlit_app.py` (verify loads without errors)
3. **Visual inspection:** No broken imports or missing files

### Rollback Plan
If issues arise, `git reset --hard HEAD~1` to undo cleanup commit.

---

## 6. Git Commit Strategy

### Single Commit with Message:
```
chore: cleanup repository after checkpoint 1-5 refactoring

- Remove obsolete files from old architecture:
  - code/agent.py (replaced by code/core/agent.py)
  - code/models.py (replaced by code/core/state.py + models.py)
  - code/nodes.py (replaced by modular code/nodes/*)
  - code/tools.py (replaced by modular code/tools/*)

- Update README to reflect new architecture:
  - Planner → Executor → Evaluator → Synthesizer flow
  - Self-correction loop with max 2 iterations
  - Parallel tool execution

- Verify Langfuse integration compatible with new workflow

All obsolete files safely preserved in git history (commit bb82192)
```

---

## 7. Implementation Approach

**Selected: Sequential Cleanup with Verification**

**Order of operations:**
1. Verify Langfuse integration code
2. Delete obsolete files (`git rm`)
3. Update README (Architecture, Workflow, Features sections)
4. Test compilation and imports
5. Single commit with all cleanup changes
6. Post-cleanup verification (Streamlit startup)

**Rationale:** Best balance of safety and efficiency. One clean commit, systematic verification, thorough but not excessive.

---

## 8. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking imports after file deletion | High | Pre-verify all imports point to new files, test after deletion |
| README inaccuracies | Low | Reference implementation plan documents for accuracy |
| Langfuse integration breaks | Medium | Code review confirms compatibility, can fix if issues found |
| Accidental deletion of needed files | High | Double-check file list, all files in git history as backup |

---

## 9. Success Metrics

- ✅ 4 obsolete files successfully removed
- ✅ README accurately describes new architecture
- ✅ Application starts without errors
- ✅ No broken imports or missing dependencies
- ✅ Clean git history with descriptive commit
- ✅ Langfuse integration code verified as compatible

---

## 10. Next Steps

After design approval:
1. Create detailed implementation plan using `writing-plans` skill
2. Execute cleanup following the plan
3. Verify all success metrics met
4. Proceed to Checkpoint 6 (UI Integration & Polish)
