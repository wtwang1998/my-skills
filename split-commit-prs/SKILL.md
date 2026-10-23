---
name: split-commit-prs
description: Split one Git commit into independently mergeable PR branches with Conventional Commits, dependency-aware ordering, and merge validation.
---

# Split Commit PRs

Use this skill when the user asks to decompose one existing Git commit into multiple branches/commits for separate pull requests. It applies across repositories and languages; infer the functional boundaries from the actual diff instead of relying on project-specific filenames.

## Safety and scope

- Preserve the user's current branch and all existing work. Before switching branches, require `git status --short` to be empty. If the worktree is dirty, stop and ask the user to commit or stash it; do not auto-stash, reset, clean, or checkout over changes.
- Resolve the requested commit and a merge base before mutating Git state. Prefer the repository's requested target branch (`main` when stated, otherwise `main` or `master`). The safest automatic path is when the target commit's first parent is exactly that base. If it is not, inspect the ancestry and stop for direction rather than silently replaying a potentially stale full-file snapshot.
- Do not rewrite, amend, reset, force-push, delete user branches, or push to a remote. Creating local branches and commits is authorized only when the user asked for this workflow.
- Keep each changed path in exactly one output branch by default. If a single file contains unrelated hunks, either keep those changes together or explicitly explain the dependency and use a patch-based split; never copy a whole file into two branches.
- Every output commit must be submitted with both a commit message and commit details at the same time. Both are required and must be written entirely in English; do not create or accept a commit with either field missing or written in another language.

## Workflow

1. Inspect the current branch, clean status, requested commit, first parent, target base, changed paths, diff statistics, and existing branch names. Record the original branch so it can be restored at the end.
2. Read enough of the diff to classify changes by behavior and ownership. Typical categories are `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, and `chore`. Keep tightly coupled implementation and regression tests together unless the user explicitly asks for test-only branches. Separate independent bug fixes, documentation-only changes, and test-maintenance changes when they can merge without path overlap.
3. Present or internally establish a manifest with, for every branch: a valid lowercase branch name, one Conventional Commit message, the exact changed paths, and any prerequisite branches. Use names such as `feat/<area>`, `fix/<area>`, `refactor/<area>`, `docs/<area>`, or `test/<area>`.
4. Check the manifest before creating anything:
   - the union of grouped paths equals `git diff --name-only <parent> <commit>`;
   - no path appears in more than one group;
   - every group has at least one path;
   - branch names do not already exist;
   - each message matches Conventional Commits 1.0.0: `<type>[optional scope][!]: <description>`.
5. For each group, create the branch from the target base, restore only that group's paths from the requested commit, stage only those paths, and create exactly one commit. Use the repository's normal Git tooling and line-ending conventions. If a branch needs another branch's files to run, keep the paths disjoint and record the merge order rather than duplicating files.
6. Validate every result without changing the user's working context:
   - `git diff --name-only <base> <branch>` contains exactly the group paths;
   - `git log -1 --format=%s <branch>` is Conventional Commit compliant;
   - `git merge-tree` (or an equivalent dry-run) reports no conflict against the target base;
   - all target paths are covered exactly once;
   - run focused tests or static checks when the repository makes them available, but do not make real network/API calls unless explicitly requested.
7. Restore the original branch and verify `git status --short` is unchanged/clean. Do not push branches unless the user separately asks.

## Commit and merge-order guidance

- Use imperative, concise commit subjects, for example `fix(recorder): persist late-arriving hit marks` or `refactor(printer): split layout and discovery services`.
- Do not call a large architectural rewrite a feature merely because it changes UI behavior; use `refactor` when the primary purpose is ownership or structure.
- Give the user a compact table of branch name, commit hash, commit subject, scope, and prerequisites. Explain any test-only branch that must follow an implementation branch.
- Recommend an order that keeps each PR conflict-free and buildable: shared infrastructure first, dependent feature refactors next, independent fixes/docs/tests whenever convenient. State clearly that every branch is based on the target base and was dry-run checked for conflicts.

## Completion criteria

The task is complete only when the requested commit is fully partitioned, all local branches and commits exist, no paths are duplicated or omitted, merge checks pass, the original branch is restored, and the final report includes the branch/commit table and merge order. If any check fails, stop before creating more branches and report the exact blocker.
