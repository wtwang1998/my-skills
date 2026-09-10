---
name: safe-pr-branch-workflow
description: Create a task branch before code changes, validate the result, and prepare a Conventional Commit and PR handoff for repository modifications.
metadata:
  short-description: Work on a clean PR branch by default
---

# Safe PR Branch Workflow

Use this skill for implementation, bug fixes, refactors, tests, and documentation changes in a Git repository when the user expects a reviewable PR. Do not use it for read-only reviews, explanations, status reports, or commands that only inspect the repository.

## Branch policy

- Inspect `git status --short --branch`, the current branch, and repository remotes before changing files.
- If the worktree is dirty before the task starts, preserve the existing changes and stop for direction. Do not stash, reset, clean, checkout over files, or silently include unrelated edits.
- Create a new branch before editing. Use the `codex/` prefix and a lowercase, hyphenated name such as `codex/fix-mihomo-lan-address`, `codex/feat-lan-console`, `codex/refactor-parser`, `codex/test-login-flow`, or `codex/docs-installation`.
- Choose the Conventional Commit type from the requested outcome: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, or `chore`.
- If the proposed branch already exists, do not overwrite or delete it. Stop and report the collision.
- Do not push, open a PR, amend unrelated commits, force-push, or delete branches unless the user separately asks.

## Implementation workflow

1. Establish the task scope and affected files from the current source tree. Record the starting branch and clean status.
2. Create the task branch from the current branch before making edits. If the repository uses a protected base such as `main` or `master`, keep that base unchanged.
3. Implement only the requested change. Preserve unrelated user edits and project conventions.
4. Add or update focused tests when behavior changes. Avoid real network calls, external services, or destructive data operations unless explicitly requested.
5. Run proportionate validation: project tests, focused tests, static checks, and `git diff --check`. If a check cannot run, state the exact reason.
6. Review the final diff for accidental files, secrets, generated artifacts, and unrelated changes.
7. Create one Conventional Commit when validation passes. Use an imperative subject with an optional scope, for example `fix(web): prefer physical lan address over tun interface`.
8. Report the branch, commit hash, changed behavior, validation results, and the next PR action. Leave the user on the task branch with a clean worktree unless the repository's workflow requires otherwise.

## Exceptions

- If the user explicitly asks for multiple commits or independently mergeable PRs, use a separate commit-splitting workflow and preserve dependency order.
- If the user explicitly asks to work directly on a named branch, follow that request after confirming the branch and worktree state.
- If no file changes are needed, do not create an empty branch or commit.
- If tests fail because of an unrelated pre-existing problem, do not hide it; distinguish the failure from regressions caused by the task.

## Completion checklist

Before handing off, confirm:

- The task branch exists and has the `codex/` prefix unless the user chose another name.
- The commit message follows Conventional Commits 1.0.0.
- The diff contains only task-related changes.
- Focused validation and `git diff --check` passed, or failures are explicitly reported.
- No remote mutation was performed without explicit authorization.
