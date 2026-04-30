# context-manager

A Claude Code skill that maintains a live, hierarchical map of your codebase through `.folder-context.md` files — one per folder. Claude reads these files to navigate large codebases without loading everything into context, and keeps them current automatically as you edit.

---

## Why this matters

Every Claude Code session starts fresh. On a large codebase, that means Claude either burns context loading files it may not need, or operates blind. Both are expensive.

`context-manager` solves this by maintaining a lightweight index of your codebase in plain Markdown files, stored alongside your source. Each `.folder-context.md` captures what every file in that folder does, what it exports, and its current WIP state. Claude reads these top-down to find relevant code fast — without touching source files it doesn't need.

The result:

- **Faster navigation** — Claude locates relevant code by reading context files, not by scanning directories or loading full source
- **Session continuity** — after `/clear` or a new session, Claude reconstructs project understanding in seconds rather than re-reading everything
- **Accurate WIP tracking** — in-progress state, known issues, and recent changes persist across context resets
- **Lower token cost** — hierarchical context files are small; loading a 200-line `.folder-context.md` beats loading 20 source files

---

## Installation

### Prerequisites

**1. Install Claude Code**

Claude Code is Anthropic's official CLI for interacting with Claude directly in your terminal and editor. Install it via npm:

```bash
npm install -g @anthropic-ai/claude-code
```

Then log in:

```bash
claude
```

This opens a browser to authenticate with your Anthropic account. Once complete, you can run `claude` in any project directory to start a session.

> If you already have Claude Code installed, make sure it's up to date before proceeding:
> ```bash
> npm update -g @anthropic-ai/claude-code
> ```
> The `/plugin` command required below was added in a recent version. If you see "unknown command" when running `/plugin`, update first.

---

**2. Have Python 3 available**

The hook script that keeps context files current is written in Python. Verify it's installed:

```bash
python3 --version
```

If not installed, download it from [python.org](https://www.python.org/downloads/) or use your system package manager (`brew install python3`, `apt install python3`, etc.).

---

### Step 1: Register this repo as a plugin source (one time)

Claude Code installs plugins from registered sources. This plugin is hosted directly on GitHub, not on any official marketplace — so you register the GitHub repo itself as a source.

Inside a Claude Code session, run:

```
/plugin marketplace add pklawansky/context-manager
```

Despite the name, this command just registers a plugin source — it isn't limited to "official" marketplaces. You only need to do this once; it persists across all sessions and projects.

---

### Step 2: Install the plugin

```
/plugin install context-manager@context-manager
```

The `@pklawansky-context-manager` suffix is how Claude Code identifies which registered source to pull from (it converts the `owner/repo` format to `owner-repo`). This downloads the plugin and makes the `context-manager` skill available globally in all your Claude Code sessions.

---

### Step 3: Reload plugins

```
/reload-plugins
```

This activates the newly installed plugin in your current session. After reloading, Claude will confirm the skill is loaded.

---

### Step 4: Verify the installation

```
/plugin
```

Navigate to the **Installed** tab. You should see `context-manager` listed. If it appears under errors, check that Python 3 is available in your shell.

---

### Step 5: Activate in a project

Navigate to your project directory and open Claude Code:

```bash
cd /path/to/your/project
claude
```

Then invoke the skill:

```
/context-manager
```

On first run, Claude will:

1. Add `.folder-context.md` to your project's `.gitignore` (creating one if needed)
2. Copy `mark-context-dirty.py` into `.claude/scripts/` inside your project
3. Register a `PostToolUse` hook in `.claude/settings.json` that fires after every file write or edit
4. Walk the entire project tree and generate `.folder-context.md` files for every folder with relevant content
5. Write `.claude/context-manager.json` to record that initialization is complete

This initial generation may take a moment on large codebases. Once complete, Claude will confirm and the skill is fully active.

Subsequent invocations detect the marker file and skip re-initialization — invoking `/context-manager` again is always safe.

---

### What gets added to your project

After initialization, two things are added to your project that you should be aware of:

- **`.claude/settings.json`** — adds a hook entry so the dirty-tracking script runs automatically. If you already have a `settings.json`, the hook is merged in; existing settings are preserved.
- **`.claude/scripts/mark-context-dirty.py`** — the hook script. This file should be committed to your repo so teammates get the same automatic tracking behavior.

The `.folder-context.md` files themselves are added to `.gitignore` — they are local working state, not something to commit.

---

## How it works

### The `.folder-context.md` file

Each folder in your project gets a `.folder-context.md` that looks like this:

```markdown
---
context_updated: 2026-04-29T10:00:00Z
tracked_files:
  - file: auth.ts
    last_modified: 2026-04-29T09:55:00Z
  - file: session.py
    last_modified: 2026-04-29T09:50:00Z
---

# src/auth

## Purpose
Handles user authentication, session management, and token validation.

## Source Files

### `auth.ts`
- **Role**: Entry point for all auth flows — login, logout, refresh
- **Exports**: `AuthService`, `createSession()`, `validateToken()`
- **Key logic**: Token rotation uses a 15-minute sliding window; refresh tokens are single-use

### `session.py`
- **Role**: Session store backed by Redis with TTL management
- **Exports**: `SessionStore`, `get_session()`, `invalidate_session()`
- **WIP**: Migration to Valkey in progress — `get_session()` temporarily dual-reads

## Other Files
`auth.config.json`, `README.md`

## Subfolders
- `./providers/` — OAuth provider integrations (Google, GitHub)
- `./middleware/` — Express middleware for route-level auth enforcement
```

Source files get full detail (role, exports, key logic, WIP). Config, data, and documentation files appear as a flat list under **Other Files** — present but not cluttering the index.

### Automatic updates via hook

The `mark-context-dirty.py` script runs after every `Write`, `Edit`, or `NotebookEdit` tool call. It:

- Appends the modified file path to `.claude/pending-context-updates.txt`
- Immediately protects `.folder-context.md` in `.gitignore` if `.gitignore` itself was just written

After each edit, Claude drains this list and updates affected `.folder-context.md` files. When a file deep in the tree changes, the update cascades upward — each parent folder's subfolder description is refreshed if it changed.

### Staleness detection

Each `.folder-context.md` stores the last-modified timestamp of every tracked source file in its frontmatter. At session start and on skill invocation, Claude compares these against actual file mtimes. Any mismatch triggers a regeneration for that folder before work begins.

### Hierarchical navigation

When starting a task, Claude reads the root `.folder-context.md` first, identifies relevant subtrees from the task description, and navigates down only those branches — loading actual source files only when the context file is insufficient. It never loads all context files at once.

---

## Companion commands

Nine commands extend the core skill. The core skill runs continuously and keeps `.folder-context.md` files current automatically — the companion commands are invoked deliberately for specific purposes.

### How they fit together

```
/context-manager              — initializes; keeps .folder-context.md files current (always running)
    │
    ├─▶ :status               — read-only health snapshot
    ├─▶ :wip                  — surface and act on active WIP
    ├─▶ :search <query>       — find where a concept lives
    ├─▶ :brief                — synthesised prose overview of the whole project
    ├─▶ :annotate             — manage persistent notes on files and folders
    ├─▶ :repair               — regenerate stale/missing context files (lightweight)
    │
    └─▶ :audit                — full scan → prioritized todo list
            │
            └─▶ :audit-resolve    — work through todos one by one
                    │
                    └─▶ :audit-clean   — purge completed items
```

**Typical workflows:**

| When | Commands |
|------|---------|
| Start of every session | `:status` → `:wip` |
| "Where does X live?" | `:search <term>` |
| Onboarding someone new, writing a README, starting a long session | `:brief` |
| Capturing institutional knowledge | `:annotate` |
| After pulling a big batch of changes without Claude | `:repair` |
| Periodic technical-debt pass | `:audit` → `:audit-resolve` → `:audit-clean` |

---

### `/context-manager:status`

**What it does:** A read-only health snapshot in seconds. Reads only `.folder-context.md` frontmatter, the todos file, and the annotations file — never source files, never makes changes.

**When to use it:** At session start, or before deciding whether to run a repair or full audit.

**Output:**
```
Context Manager Status

Coverage:      12 / 14 folders have context  (2 missing)
Staleness:     3 folders stale
Active WIP:    2 items
Annotations:   4
Open todos:    5  (2 high · 2 medium · 1 low)
Last audit:    2026-04-30T10:00:00Z

Suggestions:
  /context-manager:wip      — review active WIP
  /context-manager:repair   — fix stale and missing context
```

---

### `/context-manager:wip`

**What it does:** Extracts every active `WIP:` entry from every `.folder-context.md` across the project and surfaces them in one list, sorted root-first (broadest impact first). Shows the exact WIP text — never paraphrased.

**When to use it:** The natural session-start question: "what was I in the middle of?" Also useful after returning from a break or before deciding what to work on next.

**After listing:** Claude asks whether to start working on an item or mark any as resolved. Resolving a WIP removes its field from the context file and cascades upward if needed.

---

### `/context-manager:search`

**What it does:** Searches across all `.folder-context.md` files — folder Purpose, file Role, Exports, Key logic, WIP, subfolder descriptions — and annotation notes, for a keyword, symbol, or concept. Returns matching entries with the relevant snippet and a label showing which field matched. No source files are loaded.

**When to use it:** "Where is authentication handled?" "Which files export `UserService`?" "Is there anything about rate limiting?" — any discovery question where you don't already know which subtree to navigate to.

**Output:**
```
Search: "authentication"  —  4 matches

src/auth/                          [folder]
  Handles user authentication, session management, and token validation.

src/auth/auth.ts                   [exports, role]
  Role: Entry point for all auth flows — login, logout, refresh
  Exports: AuthService, createSession(), validateToken()

src/middleware/auth-guard.ts       [key logic]
  Key logic: Validates JWT on every request; skips public routes in auth.config.json

src/auth/                          [annotation]
  Being deprecated in Q3 — replacement is src/auth-v2/
```

---

### `/context-manager:brief`

**What it does:** Reads every `.folder-context.md`, all annotations, and the open todo list, then synthesises them into a structured prose document: what the project does, how the main modules relate, what is currently in progress, and any open issues or annotations. Does not load source files.

**When to use it:**
- Starting a long or complex session and wanting a full picture fast
- Onboarding a new developer
- Writing or updating a project README
- Handing off context to another Claude session

**Output format:**
```markdown
# Project Brief — my-project
*Generated 2026-04-30 · context-manager*

## What This Project Does
...

## Architecture
...

## Key Modules
### `src/auth/` — User authentication and session management
...

## Currently In Progress
- src/auth/session.py — Migration to Valkey in progress...

## Open Issues
- [HIGH] src/auth.ts — Unhandled null in token validation

## Annotations
- src/auth/ — Being deprecated in Q3
```

Output goes to chat by default. Ask Claude to save it to a file (e.g. `BRIEF.md`) if you want it persisted.

---

### `/context-manager:annotate`

**What it does:** Manages persistent human notes on files and folders, stored in `.claude/context-annotations.json`. Annotations capture institutional knowledge that Claude cannot infer from source — deprecation timelines, team ownership, vendor patches, architectural gotchas. They survive context regeneration and surface in search, brief, audit, wip, and repair results.

**When to use it:** Whenever you know something important about a file or folder that isn't obvious from the code — and you want Claude to remember it across all future sessions.

**Both you and Claude can author annotations.** Claude will suggest annotations when it spots something noteworthy (e.g. after an audit), but always asks for confirmation before writing.

**Supported actions (natural language):**
- `"Annotate src/auth/ — being deprecated in Q3"` → adds or updates annotation
- `"What's annotated on src/auth/?"` → shows annotations for that path
- `"/context-manager:annotate"` with no argument → lists all annotations
- `"Update the annotation on src/auth/ — moved to Q2"` → edits existing
- `"Remove the annotation on src/auth/session.py"` → removes with confirmation

**The annotation file** — `.claude/context-annotations.json`:
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
    }
  ]
}
```

`scope` is `"folder"` or `"file"`. `author` is `"user"` or `"claude"`. The file is safe to edit manually — the skill is the primary interface, but nothing prevents direct edits.

**Orphan detection:** If an annotated path is deleted or renamed, `repair` and `audit` will flag it and ask whether to remove or update the annotation.

---

### `/context-manager:repair`

**What it does:** Finds and regenerates only the `.folder-context.md` files that are stale or missing, then checks for orphaned annotations. No code review, no todos — just keeping context current.

**When to use it:** After `status` shows stale or missing folders. After pulling a large batch of commits that touched many files outside a Claude session. After a teammate made changes without Claude active. Much lighter than a full audit.

**Workflow:**
1. Scans all folders for staleness and missing context files
2. Reports what it found and asks to proceed
3. Regenerates only what needs it, cascading to parent folders
4. Checks `.claude/context-annotations.json` for orphaned paths and asks what to do

**Output:**
```
Repair complete

Regenerated:  3 stale folders
Created:      1 missing context file
Orphans:      1 annotation flagged (src/old-auth/ — folder no longer exists)
```

---

### `/context-manager:audit`

**What it does:** A thorough two-pass scan of the entire project.

**Phase 1 — metadata scan:** Reads every `.folder-context.md` and flags:
- Stale context (tracked files modified after the context was written)
- Missing context (folders with source files but no `.folder-context.md`)
- Active WIP entries
- Key logic sections containing suspicion keywords: `assumes`, `always`, `never`, `no validation`, `TODO`, `FIXME`, `hack`, `workaround`, `ignores`, `skips`, `bypasses`, `unsafe`, `unchecked`

**Phase 2 — targeted code read:** For flagged files only, reads the actual source and looks for: unhandled edge cases (null dereference, off-by-one, unchecked assertions), missing error handling, logic bugs (unreachable branches, wrong operator precedence), booby traps (mutable defaults, shared state), and security issues (injection, missing auth, hardcoded secrets).

Findings are scored by category and severity, ranked, and written to `.claude/context-manager-todos.json`. Claude shows the top items and asks whether to start resolving immediately.

Re-running merges results — `DONE` items are preserved, stale findings for the same path are refreshed.

**When to use it:** Periodic technical debt pass. Before a major release. When the codebase hasn't had a health check in a while. More thorough than `repair` but slower.

---

### `/context-manager:audit-resolve`

**What it does:** Works through the todo list one item at a time, always starting with the highest-priority unfinished item. Handles each category correctly:

| Category | Action |
|----------|--------|
| `code_issue` | Applies the fix, updates the relevant `.folder-context.md` |
| `stale_context` | Regenerates the context file for that folder |
| `missing_context` | Generates a new context file |
| `wip_review` | Reads the file, removes or updates the WIP entry |

State is written to disk after every step (`IN_PROGRESS` before, `DONE` after), so a context clear mid-session resumes cleanly. After each fix, Claude asks whether to continue with the next item.

**When to use it:** Immediately after `audit`, or anytime to resume an existing list from a previous session.

---

### `/context-manager:audit-clean`

**What it does:** Removes all `DONE` items from `.claude/context-manager-todos.json` and reports the count. `PENDING` and `IN_PROGRESS` items are untouched.

**When to use it:** After a resolve session, to keep the todo file tidy. Safe to run at any time.

---

### Persistent files

All data files live in `.claude/` and are never committed to the repository:

| File | Purpose |
|------|---------|
| `.claude/context-manager.json` | Records that the plugin has been initialized |
| `.claude/context-manager-todos.json` | Prioritized issue list from the last audit |
| `.claude/context-annotations.json` | Human and Claude-authored notes on files and folders |

The `.folder-context.md` files themselves are added to `.gitignore` at initialization — they are local working state.

---

## What gets tracked

| File type | Treatment |
|-----------|-----------|
| Source code (`.ts`, `.py`, `.go`, `.rs`, `.java`, etc.) | Full detail: role, exports, key logic, WIP |
| Config/data (`.json`, `.yaml`, `.env`, `.lock`) | Listed by name only |
| Markup/styles (`.html`, `.css`, `.scss`, `.svg`) | Listed by name only |
| Documentation (`.md`, `.txt`, `.rst`) | Listed by name only |
| Gitignored files | Excluded entirely |
| Generated dirs (`node_modules/`, `dist/`, `.venv/`, etc.) | Excluded entirely |
| `.claude/` directory | Excluded entirely |
| `.folder-context.md` files themselves | Never self-referential |

---

## What's in this repo

```
skills/
  context-manager/
    SKILL.md                  # Core skill — initializes and maintains .folder-context.md files
    mark-context-dirty.py     # Hook script installed into .claude/scripts/
  status/
    SKILL.md                  # /context-manager:status — read-only health snapshot
  wip/
    SKILL.md                  # /context-manager:wip — surface and act on active WIP entries
  search/
    SKILL.md                  # /context-manager:search — search context files by keyword or symbol
  brief/
    SKILL.md                  # /context-manager:brief — synthesised prose overview of the project
  annotate/
    SKILL.md                  # /context-manager:annotate — manage persistent notes on files and folders
  repair/
    SKILL.md                  # /context-manager:repair — regenerate stale/missing context files
  audit/
    SKILL.md                  # /context-manager:audit — full scan, writes prioritized todos
  audit-resolve/
    SKILL.md                  # /context-manager:audit-resolve — works through todos one by one
  audit-clean/
    SKILL.md                  # /context-manager:audit-clean — purges completed todos
.claude-plugin/
  plugin.json                 # Plugin metadata for claude plugin add
```

The hook script is copied into your project at initialization time. It has no external dependencies — standard library Python only.

---

## Updating the plugin

When a new version is pushed to GitHub, update your local installation inside any Claude Code session:

```
/plugin update context-manager
```

Then reload to activate the new version in your current session:

```
/reload-plugins
```

That's it. Your `.claude/` project files (settings, scripts, todos) are untouched — only the skill definitions are updated.

> **Note for contributors:** Changes to skill files in this repo take effect for all users on their next `/plugin update`. The plugin pulls directly from the `main` branch on GitHub, so merging to `main` is sufficient to ship a new version — there is no separate release or publish step.

---

## Requirements

- Claude Code with plugin support
- Python 3 available as `python3` in your project's shell environment (for the hook script)
