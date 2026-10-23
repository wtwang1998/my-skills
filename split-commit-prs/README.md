# Split Commit PRs

一个可复用的 Git 工作流 Skill：将一个已有 commit 拆分为多个可独立合并的分支和 Conventional Commits，并验证路径覆盖与合并冲突。

## 在 Codex 中使用

将此仓库中的目录安装到 Codex 的 skills 目录，然后调用：

```text
Use $split-commit-prs to split commit <commit-sha> into independently mergeable PR branches.
```

## 在其他工具中使用

直接阅读 [`SKILL.md`](SKILL.md)，将其中的流程作为系统提示、项目规则或团队 Git 操作规范使用。`SKILL.md` 不会被所有 AI 工具自动发现，因此第三方工具需要通过自己的规则文件引用它。

## 工作边界

- 默认不自动 stash、reset、clean、force-push 或 push。
- 每个变更路径只归属一个输出分支。
- 每个分支从目标基线创建，使用 Conventional Commits 1.0.0。
- 创建完成后验证路径覆盖、提交格式和合并冲突，并恢复原分支。

## 许可证

本项目使用 MIT License，见 [`LICENSE`](LICENSE)。
