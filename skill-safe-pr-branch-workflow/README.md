# Safe PR Branch Workflow

一个用于日常开发修改的 Codex Skill：在修改代码前创建 `codex/` 任务分支，完成实现和测试后生成 Conventional Commit，并输出可直接用于 PR 的交接信息。

## 适用场景

- 修复 Bug
- 新增功能
- 重构代码
- 增加测试
- 更新文档

只做审阅、解释、状态查询时，不应创建分支或提交。

## 使用方式

在 Codex 中调用：

```text
Use $safe-pr-branch-workflow to fix the reported issue and prepare a PR.
```

或者直接描述任务：

```text
修复这个问题，并按 PR 分支流程完成提交。
```

## 默认行为

- 分支名使用 `codex/<type>-<topic>`；
- 修改前检查工作区，发现已有未提交修改时暂停；
- 不自动 stash、reset、clean、force-push 或 push；
- 使用 Conventional Commits 1.0.0；
- 完成后运行针对性测试和 `git diff --check`；
- 输出分支名、commit、测试结果和 PR 操作建议。

## 文件

- [`SKILL.md`](SKILL.md)：完整工作流规则；
- [`agents/openai.yaml`](agents/openai.yaml)：Codex 界面元数据。

## 许可证

MIT License，见 [`LICENSE`](LICENSE)。
