---
name: context-manager-annotate
description: Use when running /context-manager:annotate or when the user wants to add, edit, remove, or view persistent human notes on a file or folder — notes that survive context regeneration and surface across all other context-manager commands.
---

# Context Manager Annotate

## Overview

Manages persistent human annotations on files and folders, stored in `.claude/context-annotations.json`. Annotations capture institutional knowledge that Claude cannot infer from source — deprecation plans, team ownership, vendor patches, known gotchas. They survive context regeneration and surface in search, brief, audit, wip, and repair.

Both the user and Claude can author annotations. Claude should suggest annotations when it spots something noteworthy (e.g. after an audit surfaces a pattern), but always ask for confirmation before writing.

---

## Annotation File

`.claude/context-annotations.json` — lives in `.claude/`, never committed. Create it on first use.

```json
{
  "annotations": [
    {
      "id": "ann-001",
      "path": "src/auth/",
      "scope": "folder",
      "note": "Being deprecated in Q3 — replacement is src/auth-v2/",
      "author": "user",
      "created_at": "2026-04-30T10:00:00Z",
      "updated_at": "2026-04-30T10:00:00Z"
    },
    {
      "id": "ann-002",
      "path": "src/auth/session.py",
      "scope": "file",
      "note": "Vendor fork with a custom patch on line 84 — do not upgrade without consulting the platform team.",
      "author": "claude",
      "created_at": "2026-04-30T10:00:00Z",
      "updated_at": "2026-04-30T10:00:00Z"
    }
  ]
}
```

`scope` is `"folder"` or `"file"`. `author` is `"user"` or `"claude"`. IDs are sequential strings (`ann-001`, `ann-002`, …).

---

## Intents

Handle these user intents naturally — no rigid subcommand syntax required:

### Add or update
*"Annotate src/auth/ as deprecated in Q3"*
*"Add a note to src/auth/session.py about the vendor patch"*

1. Resolve the path (ask if ambiguous).
2. Check if an annotation already exists for that path — if yes, confirm overwrite.
3. Write the annotation. Set `author: "user"` for user-authored, `author: "claude"` for Claude-suggested (always confirm before writing Claude-authored annotations).
4. Confirm: "Annotation saved for `src/auth/`."

### List
*"Show all annotations"*
*"/context-manager:annotate"* (no argument)

Display all annotations grouped by folder, then file, sorted alphabetically:

```
Annotations — 3 items

src/auth/                                          [folder]
  Being deprecated in Q3 — replacement is src/auth-v2/
  Added by user · 2026-04-30

src/auth/session.py                                [file]
  Vendor fork with a custom patch on line 84 — do not upgrade without consulting the platform team.
  Added by Claude · 2026-04-30

src/api/routes/users.ts                            [file]
  Rate limiting not wired — all routes currently unprotected.
  Added by Claude · 2026-04-30
```

If no annotations exist: "No annotations yet. Use `/context-manager:annotate` to add one."

### View for a path
*"What's annotated on src/auth/?"*

Show all annotations for that exact path (and, if it's a folder, any annotations on files directly inside it).

### Edit
*"Update the annotation on src/auth/ — it's now deprecated in Q2, not Q3"*

Find the annotation by path, update the `note` and `updated_at`, preserve `author` and `created_at`.

### Remove
*"Remove the annotation on src/auth/session.py"*

Find by path, confirm with the user, then delete the entry. Confirm: "Annotation removed."

---

## Orphan Detection

An annotation is **orphaned** if its `path` no longer exists on disk (file deleted or renamed).

- `repair` and `audit` detect and flag orphaned annotations — they do not auto-delete.
- When flagged, ask the user: "The annotation for `src/old-module/` no longer exists on disk. Remove it, or update the path?"
- The `annotate` skill itself should also flag orphans when listing.

---

## Surfacing in Other Skills

All skills that read `.folder-context.md` should also check `.claude/context-annotations.json` for matching paths and surface any annotation alongside the context entry. Specific behaviors:

| Skill | How annotations surface |
|-------|------------------------|
| `search` | Annotation note text is included in the search scope; matches shown with `[annotation]` label |
| `brief` | Annotations appear under the relevant folder or file description |
| `status` | Shows total annotation count |
| `audit` | Folder/file annotations shown alongside findings; a "deprecated" annotation may indicate lower priority for code fixes |
| `wip` | Annotations shown alongside WIP entries for the same path |
| `repair` | Orphaned annotations flagged after stale context is repaired |

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Writing Claude-authored annotations without confirmation | Always ask before saving a Claude-suggested annotation |
| Creating duplicate annotations for the same path | Check for existing annotation before adding; offer to update |
| Auto-deleting orphaned annotations | Flag them and ask the user — don't delete without instruction |
| Storing annotations inside `.folder-context.md` | Annotations live only in `.claude/context-annotations.json` |
