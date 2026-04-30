---
name: context-manager-wip
description: Use when running /context-manager:wip to surface all active WIP entries across the project in one list, or when the user asks what is currently in progress or unfinished.
---

# Context Manager WIP

## Overview

Extracts every active `WIP:` entry from every `.folder-context.md` in the project and presents them in a single list. The natural use at session start: "what was I in the middle of?"

---

## Prerequisites

Check `.claude/context-manager.json` exists. If not, tell the user to run `context-manager:context-manager` first.

---

## Workflow

1. Walk all `.folder-context.md` files in the project (same ignore rules as context-manager).
2. For each file, collect every source file entry where `WIP:` is non-empty.
3. If no WIP entries exist anywhere, say: "No active WIP — the project is clean." Stop.
4. Display the list (see format below).
5. Ask: **"Would you like to start working on any of these, or mark any as resolved?"**
   - **Work on one** → read the source file and begin; update `WIP:` in `.folder-context.md` as you go
   - **Mark as resolved** → remove the `WIP:` field from the entry in `.folder-context.md`
   - **No action** → stop

---

## Display Format

Sort by folder depth ascending (root-level folders first — broadest impact). Within the same folder, preserve file order from the `.folder-context.md`.

```
Active WIP — N items

src/auth/session.py
  Migration to Valkey in progress — get_session() temporarily dual-reads both stores

src/api/routes/users.ts
  Rate limiting not yet implemented — all user routes currently unprotected

tests/integration/db.ts
  Setup incomplete — database fixtures missing, tests skipped
```

Use the exact WIP text from the context file — do not paraphrase.

---

## Resolving a WIP

When a WIP item is resolved (either by fixing it or confirming it's no longer relevant):

1. Remove the `WIP:` line from the source file's entry in its `.folder-context.md`
2. Update `context_updated` in the frontmatter
3. Cascade upward if the subfolder description referenced the WIP state

Do **not** mark WIP as resolved without either reading the source file to confirm the work is done, or explicit user instruction that it's no longer relevant.

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Paraphrasing WIP text | Display verbatim from `.folder-context.md` |
| Marking WIP resolved without confirmation | Read the file or get explicit user instruction first |
| Sorting by file name instead of folder depth | Broader folders first — root items are highest impact |
| Showing WIP entries where the field is empty | Only show non-empty `WIP:` fields |
