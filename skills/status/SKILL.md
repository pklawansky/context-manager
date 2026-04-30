---
name: context-manager-status
description: Use when running /context-manager:status to get a quick health snapshot of context coverage, staleness, WIP count, and open todos — without running a full audit.
---

# Context Manager Status

## Overview

Reads only `.folder-context.md` frontmatter and `.claude/context-manager-todos.json` — no source file reads, no deep analysis. Produces a project health snapshot in seconds. Use this to decide whether a full `/context-manager:audit` is worth running.

---

## Prerequisites

Check `.claude/context-manager.json` exists. If not, tell the user to run `context-manager:context-manager` first.

---

## What to Measure

### Coverage
Walk the project tree (same ignore rules as context-manager). Count:
- Folders that have a `.folder-context.md` — **covered**
- Folders that contain at least one source file but have no `.folder-context.md` — **missing**

### Staleness
For each `.folder-context.md`, compare each `tracked_files` entry's `last_modified` against the file's actual mtime. Count folders where at least one file is newer than recorded — **stale**.

### Active WIP
Count source file entries across all `.folder-context.md` files where `WIP:` is non-empty.

### Open Todos
Read `.claude/context-manager-todos.json` if it exists. Count items by status and severity:
- PENDING + IN_PROGRESS = open; DONE = completed
- Break open items down by severity: high / medium / low
- Record `audited_at` timestamp

### Last Audit
The `audited_at` field from `.claude/context-manager-todos.json`, or "never" if the file doesn't exist.

---

## Display Format

```
Context Manager Status

Coverage:     12 / 14 folders have context  (2 missing)
Staleness:    3 folders stale
Active WIP:   2 items
Open todos:   5  (2 high · 2 medium · 1 low)
Last audit:   2026-04-29T10:00:00Z

Suggestions:
  /context-manager:wip      — review active WIP
  /context-manager:audit    — run a full scan
```

Omit the todo row if `.claude/context-manager-todos.json` does not exist. Omit suggestions for commands where there is nothing to do (e.g. omit the WIP suggestion if Active WIP is 0).

If everything is healthy (no missing, no stale, no WIP, no open todos), say:
```
Context Manager Status

Coverage:    14 / 14 folders  ✓
Staleness:   none  ✓
Active WIP:  none  ✓
Open todos:  none  ✓

All good.
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Reading source files | Status reads only `.folder-context.md` frontmatter and the todos JSON — never source files |
| Running a staleness repair | Status is read-only; report stale counts, do not regenerate anything |
| Counting DONE todos as open | Only PENDING and IN_PROGRESS count as open |
