"""
Hook script: PostToolUse on Write/Edit/NotebookEdit
- Appends modified source file paths to .claude/pending-context-updates.txt
  so Claude can catch changes made outside its immediate edit cycle.
- Ensures .folder-context.md is always present in .gitignore whenever .gitignore
  is written or created.

Install location in project: .claude/scripts/mark-context-dirty.py
"""

import sys
import json
import os

GITIGNORE_ENTRY = ".folder-context.md"
GITIGNORE_COMMENT = "# context-manager skill"

IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", "dist", "build", "out",
    ".venv", "venv", ".next", ".nuxt", "coverage", ".turbo",
    "target", "vendor", "bin", "obj",
}


def ensure_context_in_gitignore(gitignore_path: str) -> None:
    """Append .folder-context.md entry to .gitignore if not already present."""
    content = ""
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

    lines = content.splitlines()
    if GITIGNORE_ENTRY in lines:
        return

    suffix = "\n" if content and not content.endswith("\n") else ""
    with open(gitignore_path, "a", encoding="utf-8") as f:
        f.write(f"{suffix}{GITIGNORE_COMMENT}\n{GITIGNORE_ENTRY}\n")


def is_in_ignored_dir(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return any(part in IGNORED_DIRS for part in parts)


try:
    data = json.load(sys.stdin)
except (json.JSONDecodeError, EOFError):
    sys.exit(0)

tool_input = data.get("tool_input", {})
file_path = (
    tool_input.get("file_path")
    or tool_input.get("path")
    or tool_input.get("notebook_path")
    or ""
)

if not file_path:
    sys.exit(0)

# Normalise to forward slashes for consistent matching
norm_path = file_path.replace("\\", "/")
basename = os.path.basename(norm_path)

# If .gitignore was written, protect the .folder-context.md entry immediately
if basename == ".gitignore":
    ensure_context_in_gitignore(file_path)
    sys.exit(0)

# Never track .folder-context.md files (avoids infinite loops)
if basename == ".folder-context.md":
    sys.exit(0)

# Skip .claude/ directory and common generated directories
if "/.claude/" in norm_path or norm_path.startswith(".claude/"):
    sys.exit(0)

if is_in_ignored_dir(norm_path):
    sys.exit(0)

# Append to dirty list, deduplicating
dirty_file = ".claude/pending-context-updates.txt"
os.makedirs(".claude", exist_ok=True)

existing = set()
if os.path.exists(dirty_file):
    with open(dirty_file, "r", encoding="utf-8") as f:
        existing = set(line.strip() for line in f if line.strip())

if file_path not in existing:
    with open(dirty_file, "a", encoding="utf-8") as f:
        f.write(f"{file_path}\n")
