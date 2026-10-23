---
name: release-changelog
description: Generate concise Chinese Markdown changelogs directly suitable for GitHub Releases from a Git tag, commit range, or release target.
metadata:
  short-description: Generate Chinese Release changelogs from Git history
---

# Release Changelog

Use this skill when the user asks for a changelog, release notes, or GitHub Release description based on a Git repository's history. The deliverable is Chinese Markdown that can be pasted directly into a Release description.

## Scope and references

Treat the requested start and end refs as the source of truth. A request such as “从 0.1.0 到 `<commit>`” means summarize commits after `0.1.0` through the specified commit. A request for a version's changelog means summarize the commits introduced by that release; when there is no earlier release tag, use the repository's initial commit or the parent of the release commit as the baseline, whichever represents the first shipped state.

Do not modify the repository, create tags, push, or open a Release unless the user separately asks for those actions.

## Workflow

1. Resolve and verify both endpoints with Git before interpreting the history:
   - `git rev-parse --verify <ref>^{commit}`
   - `git log --oneline --decorate --all --max-count=30`
   - If a displayed tag cannot be resolved, inspect `git show-ref --tags`, packed refs, and available remote refs. Do not silently substitute an unrelated commit. If a matching release commit is the only reliable local baseline, use it only when the final response states that assumption.
2. Inspect the range, in chronological order:
   - `git log --reverse --format=... <start>..<end>`
   - `git diff --shortstat <start> <end>`
   - `git diff --name-status <start> <end>`
   - Read the relevant README, packaging metadata, release notes, and focused source files for user-visible behavior. Use commit diffs when commit subjects alone are ambiguous.
3. Classify changes by user impact rather than merely copying Conventional Commit prefixes:
   - **新增功能**: new capabilities users can operate.
   - **改进**: behavior, usability, reliability, performance, or compatibility improvements.
   - **修复**: corrected defects or regressions.
   - **依赖与兼容性**: runtime requirements, platform support, important dependency changes, or migration notes.
   - **测试与发布**: meaningful test coverage, packaging, or validation improvements.
   Keep internal refactors out of the main feature list unless they materially affect maintainability, extensibility, or reliability; summarize them briefly under improvements when useful.
4. Write the release body in Chinese. Prefer concrete user-facing wording and group related changes into a few bullets. Do not list every commit, file, or internal helper. Do not claim behavior that is not supported by the inspected code or documentation.
5. Return only the paste-ready Markdown body, optionally preceded by one short note if a ref or baseline had to be inferred. Use a version heading and include only non-empty sections. Do not place a general summary sentence or paragraph below the version heading; begin directly with the first non-empty section. Keep this rule for future changelogs unless the user explicitly asks for an overview:

   ```markdown
   ## 项目名 版本号

   ### ✨ 新增功能

   - ...

   ### 🛠️ 改进

   - ...

   ### 🐛 修复

   - ...

   ### 📦 依赖与兼容性

   - ...

   ### ✅ 测试与发布

   - ...
   ```

## Release-writing rules

- Do not add a general summary sentence or paragraph between the title and the categorized release notes. Start directly with the first non-empty section unless the user explicitly asks for an overview.
- Keep the output directly usable in GitHub's Markdown renderer; avoid raw command output, commit hashes, or a methodology dump unless they clarify the range or a baseline assumption.
- Mention security, privacy, data-loss, authentication, migration, or platform caveats when the change affects them.
- Mention optional integrations as optional and state their default behavior, especially for network or LLM features.
- For an initial release, describe the shipped capability as a coherent product rather than pretending there were incremental fixes.
- Preserve exact user-facing names, commands, version numbers, limits, and file formats from the repository.
- If the range is empty, ambiguous, or cannot be verified, stop and report the specific Git evidence instead of fabricating a changelog.
