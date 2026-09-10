# my-skills

个人 Codex Skills 集合。每个子目录都是一个可独立安装的技能，入口文件为
`SKILL.md`，并可包含 `agents/openai.yaml` 及其他资源。

## Skills

- [`chatgpt-model-consistency`](chatgpt-model-consistency/)：检查 ChatGPT 网页请求模型与服务端模型标注是否一致。
- [`skill-release-changelog`](skill-release-changelog/)：根据 Git 历史生成中文 GitHub Release changelog。
- [`skill-safe-pr-branch-workflow`](skill-safe-pr-branch-workflow/)：按安全分支流程完成实现、验证和 Conventional Commit 交接。
- [`skill-split-commit-prs`](skill-split-commit-prs/)：将一个已有 commit 拆分为可独立合并的 PR 分支。

## 安装

将需要使用的技能目录复制到 Codex 的 skills 目录，然后按技能名称调用，例如：

```text
Use $chatgpt-model-consistency to check the current ChatGPT web model.
```
