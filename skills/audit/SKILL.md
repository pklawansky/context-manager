---
name: context-manager-audit
description: Use when running /context-manager:audit to scan the project for stale context, missing context files, WIP entries, and latent code issues, then populate a prioritized todo list in .claude/context-manager-todos.json.
---

# Context Manager Audit

## Overview

Scans the project in two passes: a fast metadata sweep over all `.folder-context.md` files, then a targeted deep read on any flagged source files. Writes a prioritized todo list to `.claude/context-manager-todos.json` and offers to begin resolving items sequentially.

---

## Prerequisites

Check `.claude/context-manager.json` exists. If it does not, tell the user to run `context-manager:context-manager` first to initialize, then stop.

---

## Phase 1: Metadata Scan

Walk every `.folder-context.md` in the project, respecting the same ignore rules as `context-manager:context-manager` (no gitignored paths, no `.claude/`, no generated directories).

For each folder check all four conditions:

### 1a. Missing context
Folder contains at least one source code file but has no `.folder-context.md`.
- Severity: **medium**

### 1b. Stale context
Any entry in `tracked_files` has a `last_modified` older than the file's actual mtime on disk.
- Severity: **medium**
- Note the specific files that drifted

### 1c. WIP entries
Any source file entry has a `WIP:` field that is non-empty.
- Base severity: **low** — escalate to **high** if the WIP text mentions a bug, crash, broken state, or security risk
- Flag file and WIP text for Phase 2

### 1d. Structural suspicion in Key logic
`Key logic` text contains any of: `assumes`, `always`, `never`, `no validation`, `TODO`, `FIXME`, `hack`, `workaround`, `ignores`, `skips`, `bypasses`, `unsafe`, `unchecked`, `trust`, `blindly`.
- Severity: **medium** pending Phase 2 confirmation
- Flag file for Phase 2

---

## Phase 2: Deep Code Read (Flagged Files Only)

For each source file flagged in Phase 1 (WIP, stale, or suspicious Key logic), read the actual file and look for:

- **Unhandled edge cases**: null/undefined dereference, empty collection access, off-by-one, unchecked type assertions, divide-by-zero
- **Missing error handling**: uncaught exceptions, ignored return values from error-returning functions, fire-and-forget async without `.catch()`
- **Logic bugs**: conditions that can never be true or false, unreachable branches, incorrect operator precedence, wrong loop bounds
- **Booby traps**: mutable default arguments, shared state mutated between calls, implicit ordering dependencies, silent integer truncation or overflow
- **Security issues**: injection risks, missing authorization checks, hardcoded credentials, logging of sensitive data

For each real issue found, record it as a `code_issue` todo with the specific line number and a concrete recommendation.

Do **not** read files that were not flagged in Phase 1. The metadata scan is the gate.

---

## Priority Scoring

After collecting all todos, score each item and sort descending. Assign `priority` values 1, 2, 3… in descending score order (1 = highest priority).

| Category | Base score | Severity modifier |
|----------|-----------|-------------------|
| `code_issue` | 10 | high ×3, medium ×2, low ×1 |
| `wip_review` | 5 | high ×3, medium ×2, low ×1 |
| `stale_context` | 4 | — |
| `missing_context` | 2 | — |

Within the same score, prefer items in folders closer to the project root (broader impact).

---

## Todo File

Write to `.claude/context-manager-todos.json`:

```json
{
  "audited_at": "<ISO timestamp>",
  "todos": [
    {
      "id": "todo-001",
      "priority": 1,
      "category": "code_issue",
      "severity": "high",
      "path": "src/auth.ts",
      "folder": "src/",
      "title": "Unhandled null in token validation",
      "description": "getToken() can return null but line 42 calls .split() without a null check — throws at runtime when no token is present.",
      "recommendation": "Add `if (!token) return null;` guard before the split call at line 42.",
      "status": "PENDING",
      "resolved_at": null
    }
  ]
}
```

**Merging on re-audit:** If the file already exists, preserve any `DONE` items. For the same `path`, replace existing `PENDING` or `IN_PROGRESS` items with the fresh finding. Add new paths as new items.

---

## After Audit

Display a summary:
```
Audit complete — N issues found (X high, Y medium, Z low)

Top priorities:
1. [HIGH] src/auth.ts — Unhandled null in token validation
2. [MEDIUM] src/utils/ — Stale context (3 files modified since last update)
3. [LOW] src/db/queries.ts — WIP: connection pooling not implemented
```

Then ask: **"Would you like me to start resolving these now, beginning with [#1 title]?"**

- **Yes** → follow `context-manager:audit-resolve` workflow starting from priority 1
- **No** → "Run `/context-manager:audit-resolve` anytime to pick up where we left off, or `/context-manager:audit-clean` to remove completed items."

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Reading all source files in Phase 1 | Phase 1 reads only `.folder-context.md` files — source files only in Phase 2 |
| Overwriting DONE todos on re-audit | Merge: keep DONE, replace PENDING/IN_PROGRESS for the same path |
| Running Phase 2 on list-only files (config, assets) | Deep read applies to source files only |
| Creating todos for gitignored paths | Apply the same ignore rules as context-manager |
| Flagging every `Key logic` section | Only flag entries containing the specific suspicion keywords listed above |
