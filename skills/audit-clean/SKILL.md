---
name: context-manager-audit-clean
description: Use when running /context-manager:audit-clean to purge all DONE items from the context manager todo list.
---

# Context Manager Audit Clean

## Overview

Removes all completed items from `.claude/context-manager-todos.json` and reports what was purged. Leaves PENDING and IN_PROGRESS items untouched.

---

## Workflow

1. Read `.claude/context-manager-todos.json`. If it does not exist, say: "Nothing to clean — no todo list found. Run `/context-manager:audit` to generate one."
2. Count items by status: DONE, PENDING, IN_PROGRESS.
3. If DONE count is 0, say: "Nothing to clean — no completed items in the list." Stop.
4. Remove all items where `status: DONE` from the `todos` array.
5. Write the updated file.
6. Report:
   ```
   Cleaned X completed items. Y items remain (Z high, W medium, V low).
   ```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Removing PENDING or IN_PROGRESS items | Only remove DONE |
| Deleting the file when all items are DONE | Write the file with an empty `todos` array so `audited_at` is preserved |
