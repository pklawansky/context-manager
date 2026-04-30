---
name: context-manager-search
description: Use when running /context-manager:search or when the user asks where something lives in the codebase — searches across all .folder-context.md files for a keyword, symbol, or concept without loading source files.
---

# Context Manager Search

## Overview

Searches every `.folder-context.md` in the project for a keyword, symbol name, or concept and returns matching folders and file entries with the relevant snippet. Keeps discovery entirely within context files — no source files loaded.

---

## Prerequisites

Check `.claude/context-manager.json` exists. If not, tell the user to run `context-manager:context-manager` first.

---

## Accepting the Query

If the user invoked the skill with a search term (e.g. `/context-manager:search authentication`), use that term directly. If invoked with no argument, ask: "What are you looking for?"

---

## Search Scope

Search within these fields of every `.folder-context.md`:

| Field | Where it appears |
|-------|-----------------|
| Folder **Purpose** | Top-level description of the folder |
| File **Role** | What the file does |
| File **Exports** | Exported names and functions |
| File **Key logic** | Non-obvious behavior descriptions |
| File **WIP** | In-progress state |
| **Subfolder descriptions** | One-line summaries in the Subfolders section |

Match case-insensitively. Match partial words (e.g. "auth" matches "authentication", "authorize", "AuthService").

---

## Ranking Results

Return results in this order:
1. **Folder Purpose match** — the whole folder is about this concept (highest signal)
2. **Exports match** — the symbol is directly exported from this file
3. **Role match** — the file's primary responsibility involves this concept
4. **Key logic / WIP match** — the concept appears in implementation detail
5. **Subfolder description match** — a subfolder is relevant (lowest signal)

Within the same rank, sort by folder depth ascending (root folders first).

---

## Display Format

```
Search: "authentication"  —  4 matches

src/auth/                          [folder]
  Handles user authentication, session management, and token validation.

src/auth/auth.ts                   [exports, role]
  Role: Entry point for all auth flows — login, logout, refresh
  Exports: AuthService, createSession(), validateToken()

src/middleware/auth-guard.ts       [key logic]
  Key logic: Validates JWT on every request; skips public routes in auth.config.json

src/api/routes/users.ts            [wip]
  WIP: Auth middleware not yet wired to these routes
```

Show the matched field(s) only — not the entire file entry. Label which fields matched in brackets.

If no matches: "No matches for '[query]' in context files. The concept may not be documented yet — try `/context-manager:audit` to refresh context, then search again."

---

## After Results

Ask: **"Would you like me to navigate to any of these?"**
- **Yes** → load the relevant `.folder-context.md` (and source file if needed) and proceed with the user's task
- **No** → stop

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Loading source files during search | Search operates only on `.folder-context.md` content |
| Case-sensitive matching | Always match case-insensitively |
| Showing the full file entry for every match | Show only the matched fields, not the entire entry |
| Returning zero results without a suggestion | Always suggest audit + retry if nothing is found |
