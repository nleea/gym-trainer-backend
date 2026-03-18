# AGENTS - trainerGM

## Task Classification — do this first

Classify before loading any context.

**SIMPLE — act directly, no MCP:**
- Add/modify a field in an existing model or schema
- Fix a typo, label, or static response text
- Change a config value or constant
- Add a validator to an existing endpoint

**FAMILIAR — `search_notes()` only if uncertain:**
- New endpoint following an existing pattern in the same router
- New repository method similar to existing ones
- New service method with the same layer pattern

**COMPLEX — full MCP protocol:**
- Bug with no obvious cause
- New domain module or cross-cutting feature
- Changes to auth, sessions, DB schema, or core architecture
- API contract change affecting frontend

---

## Mandatory Workflow

1. **Classify the task first** (see above).
2. Query memory MCP only for FAMILIAR or COMPLEX tasks.
3. Use `project="fitness-app"` filters in memory queries.
4. Validate existing architecture decisions before schema or API contract updates.

## MCP Call Order (lightest to heaviest)

```
1. rank_context_templates(task, project)   → find relevant context without loading it
2. search_bug_fixes(query, project)        → check for prior solutions
3. search_notes(query, project)            → load relevant chunks by similarity
4. get_note(note_id)                       → load one specific note in full
5. get_context_pack(task, project)         → WARNING: ~15k tokens, use only when
                                             module is unfamiliar or 1–4 insufficient
```

## Suggested Queries

- `rank_context_templates("backend schema change", project="gym-trainer")`
- `search_decisions("backend architecture", project="gym-trainer")`
- `search_bug_fixes("endpoint error", project="gym-trainer")`
- `get_project_context("gym-trainer")`

## save_debug_note — required fields

```
title       : short slug (e.g. "upsert-duplicate-on-training-log")
summary     : one-line description of the bug (required — tool fails without it)
content     : full markdown body
project     : "gym-trainer"
relative_dir: "11-debugging"
```

## save_session_summary — required fields

```
title   : descriptive session title
task    : one-line description of what was worked on (required — tool fails without it)
content : full markdown body
project : "gym-trainer"
```

## Guardrails

- Do not introduce new business rules without checking existing notes.
- If a decision note conflicts with current code, surface the conflict explicitly.
