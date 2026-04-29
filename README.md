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
    SKILL.md                  # The skill definition read by Claude Code
    mark-context-dirty.py     # Hook script installed into .claude/scripts/
.claude-plugin/
  plugin.json                 # Plugin metadata for claude plugin add
```

The hook script is copied into your project at initialization time. It has no external dependencies — standard library Python only.

---

## Requirements

- Claude Code with plugin support
- Python 3 available as `python3` in your project's shell environment (for the hook script)
