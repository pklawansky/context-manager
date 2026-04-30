---
name: context-manager-brief
description: Use when running /context-manager:brief or when the user wants a synthesised prose overview of the project — what it does, how modules relate, what is in progress, and any open issues. Reads context files and annotations; does not load source.
---

# Context Manager Brief

## Overview

Synthesises `.folder-context.md` files, annotations, WIP entries, and open todos into a single structured prose document. Does not load source files. Useful at session start, before writing a README, for onboarding, or for handing off context to another session.

---

## Prerequisites

Check `.claude/context-manager.json` exists. If not, tell the user to run `context-manager:context-manager` first.

---

## What to Read

| Source | Purpose |
|--------|---------|
| All `.folder-context.md` files | Architecture, module purposes, file roles |
| `.claude/context-annotations.json` | Human notes and institutional knowledge |
| `.claude/context-manager-todos.json` | Open high/medium todos |

Read all `.folder-context.md` files in one pass (this is the one context where loading all of them at once is correct — the goal is a whole-project synthesis). Load source files only if the user explicitly asks for deeper detail on a specific area.

---

## Output Structure

```markdown
# Project Brief — [root folder name or project name from README]
*Generated [date] · context-manager*

## What This Project Does
[2–3 sentences synthesised from root Purpose and top-level subfolder descriptions.
What problem does it solve? Who uses it?]

## Architecture
[Prose description of how the main modules relate. Mention key data flows or
boundaries where they are obvious from Key logic sections. 2–4 short paragraphs.]

## Key Modules

### `src/auth/` — [one-line purpose]
[1–2 sentences. Include any annotations for this folder.]

### `src/api/` — [one-line purpose]
[1–2 sentences. Include any annotations.]

[... one entry per top-level module folder. Skip generated/vendor/ignored dirs.]

## Currently In Progress
[Bulleted list of all active WIP entries, grouped by folder.
Use verbatim WIP text — do not paraphrase.
If no WIP: "No active work in progress."]

## Open Issues
[Bulleted list of high and medium todos from context-manager-todos.json.
Skip low-severity todos and all DONE items.
If no open todos: omit this section.]

## Annotations
[Bulleted list of all annotations, path + note.
If no annotations: omit this section.]
```

---

## Output Destination

Output to chat by default. If the user asks to save it, write to a file they name (e.g. `BRIEF.md`). Do not create a file unless explicitly asked — the brief is transient by default.

---

## Tone and Length

- Prose, not bullet-point soup — the point is readability for a human or a new session
- Architecture section: aim for 150–300 words
- Key Modules: 1–2 sentences per module, no more
- Do not invent information — only synthesise what is in the context files
- If context files are sparse or missing for major folders, note it: "Note: several folders lack context — run `/context-manager:audit` for a full picture."

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Loading source files | Read only `.folder-context.md`, annotations, and todos |
| Reading context files one by one top-down | Load all at once — brief is a whole-project synthesis |
| Paraphrasing WIP text | Use verbatim WIP entries |
| Inventing architecture details not in context files | Only synthesise what is documented |
| Writing the brief to a file without being asked | Output to chat unless the user requests a file |
