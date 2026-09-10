---
name: skill-release-changelog
description: Generate Chinese Markdown changelogs that match an existing release-note style and are directly suitable for GitHub Releases.
metadata:
  short-description: Generate Chinese Release changelogs from Git history
---

# Release Changelog

Use this skill when the user asks for a changelog, release notes, or GitHub Release description based on a Git repository's history. The deliverable is Chinese Markdown that can be pasted directly into a Release description.

## Scope and references

Treat the requested start and end refs as the source of truth. A request such as “从 0.1.0 到 `<commit>`” means summarize commits after `0.1.0` through the specified commit. A request for a version's changelog means summarize the commits introduced by that release; when there is no earlier release tag, use the repository's initial commit or the parent of the release commit as the baseline, whichever represents the first shipped state.

Do not modify the repository, create tags, push, or open a Release unless the user separately asks for those actions.

When the repository contains earlier release notes, treat the latest one to three shipped versions as the style reference. Match their section names, heading level, emoji, sentence shape, tone, and level of directness before applying the default format below. Existing release-note style takes precedence over this skill's fallback template.

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
3. Inspect the existing release-note style before drafting:
   - Locate the previous one to three version files, commonly with `rg --files -g '*0.*.md' -g '*changelog*.md'` or by inspecting the repository's release-note directory.
   - Read those files rather than inferring the format from filenames. Record their section order, heading level, emoji, opening summary, and bullet style.
   - If earlier notes use direct bullets such as `新增...`、`优化...`、`修复...`, keep that sentence pattern. Do not introduce bold inline labels, mini-headings, or long explanatory paragraphs unless the existing notes already use them.
4. Classify changes by user impact rather than merely copying Conventional Commit prefixes:
   - **新增**: new capabilities users can operate. State the capability and its meaningful scope, inputs, outputs, or supported flow when those details distinguish the change.
   - **优化**: behavior, usability, reliability, performance, or workflow improvements. State what user-visible flow became better and under what conditions.
   - **修复**: corrected defects or regressions. State the affected behavior and the failure or inconsistency that is no longer present.
   - **依赖与兼容性**: by default, list only dependencies that were added or removed. Do not fill this section with operating-system limits, runtime-version reminders, old-data compatibility, migration details, or optional-capability disclaimers unless the user explicitly asks for them or an immediate user action is required.
   - Do not add separate **安全** or **测试与发布** sections by default. Put security, privacy, packaging, or validation changes under the user-facing category where they have a concrete effect, or omit them when they are only internal.
   - Treat an optional integration as a normal feature when it provides a capability users can actively use; do not add a low-value note merely saying that it is optional.
   Keep internal refactors out of the main feature list unless they materially affect maintainability, extensibility, or reliability visible to users; summarize them briefly under improvements when useful.
5. Set the detail level by coverage, not by paragraph length:
   - When the user asks for a detailed changelog, include more distinct user-visible capabilities, improvements, and fixes from the verified range.
   - Keep each bullet concise, normally one sentence with one primary change. Make the scope concrete enough to distinguish the change from a vague “完善稳定性” statement, but do not turn a bullet into a commit dump or implementation essay.
   - Group only closely related changes that users experience as one flow. Split unrelated settings, workflows, platforms, or defect classes into separate bullets so the release's breadth is visible.
   - Prefer direct verbs matching the section, such as `新增`、`优化`、`修复`; use `支持`、`完善` or `重构` only when that is the clearest description of the actual user-visible change.
6. Write the release body in Chinese. Prefer concrete user-facing wording and group related changes into a useful number of concise bullets. Do not list every commit, file, or internal helper. Do not claim behavior that is not supported by the inspected code or documentation.
7. Return only the paste-ready Markdown body, optionally preceded by one short note if a ref or baseline had to be inferred. Use the repository's established heading style; if no style exists, use a version heading and include only non-empty sections:

   ```markdown
   # 🎉 版本号

   一句话概述本次版本的重点。

   ## ✨ 新增

   - ...

   ## 🚀 优化

   - ...

   ## 🐛 修复

   - ...

   ## 🔧 依赖与兼容性

   - 新增 `dependency-name` 依赖，用于...
   - 移除 `dependency-name` 依赖。
   ```

## Release-writing rules

- Keep the output directly usable in GitHub's Markdown renderer; avoid raw command output, commit hashes, or a methodology dump unless they clarify the range or a baseline assumption.
- Mention security, privacy, data-loss, authentication, or migration behavior only when it changes what users need to do or protects them from a concrete failure; place it under `优化` or `修复` when that matches the existing style.
- Do not add generic platform caveats, old-data compatibility notes, or optional-capability disclaimers merely to make the changelog look complete.
- In `依赖与兼容性`, mention only added or removed dependencies unless the user explicitly requests a broader compatibility summary.
- For an initial release, describe the shipped capability as a coherent product rather than pretending there were incremental fixes.
- Preserve exact user-facing names, commands, version numbers, limits, and file formats from the repository.
- If the user asks for “详细”, make the list of meaningful changes more complete while keeping each item short and direct; do not satisfy the request by expanding every item into a long paragraph.
- Do not add a separate testing/release section unless the user asks for it or the repository's established changelog style consistently includes one.
- If the range is empty, ambiguous, or cannot be verified, stop and report the specific Git evidence instead of fabricating a changelog.
