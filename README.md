# My Skills Collection

这是我日常使用的 **Agent Skills 收藏清单**，包括个人编写的技能，以及日常使用或关注的其他技能。

**收录不代表原创。** 本仓库只保存个人编写的 Skill 源文件；其他 Skill 仅记录已确认的上游链接，不复制或维护其代码。安装和更新第三方 Skill 时，请以原项目的最新说明为准。

## 个人编写 · 本仓库维护

以下技能的目录和 `SKILL.md` 保存在本仓库，可直接查看、安装或继续修改。技能目录名与 `SKILL.md` frontmatter 中的 `name` 一致；支持的平台和依赖以各自目录中的说明为准。

### ChatGPT 与技能管理

- [`chatgpt-model-consistency`](chatgpt-model-consistency/)：核对 ChatGPT 网页请求的模型与服务端实际标注的模型是否一致。

### Git 与交付

- [`release-changelog`](release-changelog/)：根据 Git tag 或 commit 范围编写中文 GitHub Release changelog。
- [`safe-pr-branch-workflow`](safe-pr-branch-workflow/)：为代码改动准备任务分支、验证结果和 Conventional Commit/PR 交接。
- [`split-commit-prs`](split-commit-prs/)：将已有 commit 拆分为可独立合并的 PR 分支。

### 文档与汇报

- [`weekly-report`](weekly-report/)：根据当周工时截图和公司周报模板核对内容、展示预览，并在确认后生成保留模板格式的 DOCX。

## 第三方收藏 · 仅保留上游链接

以下 Skill 由其他作者提供，本仓库不保存其文件夹。链接直接指向对应的原项目或 Skill 目录。

### ChatGPT 与技能管理

- [`codex-with-chatgpt`](https://github.com/XiaoDuoYa/codex-with-chatgpt/tree/main/skill)：让 ChatGPT 网页协助 Codex 规划、评审和排查问题，由 Codex 负责执行。
- [`find-skills`](https://github.com/vercel-labs/skills/tree/main/skills/find-skills)：在开放的 Agent Skills 生态中发现和安装技能。
- [`manage-skills`](https://github.com/xingkongliang/skills-manager/tree/main/skills/manage-skills)：通过 Skills Manager 管理共享技能库、预设和各 Agent 的部署。

### 设计与测试

- [`grill-me`](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me)：通过访谈打磨计划或设计。
- [`grill-with-docs`](https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs)：通过访谈打磨设计，并整理 ADR 和领域词汇表。
- [`tdd`](https://github.com/mattpocock/skills/tree/main/skills/engineering/tdd)：指导测试先行、行为测试边界、测试替身和 Red-Green 循环。

### Git 与交付

- [`triage`](https://github.com/mattpocock/skills/tree/main/skills/engineering/triage)：按状态流转分类和核验 issue 或外部 PR，并整理 agent brief。

## 安装与使用

- **个人编写的 Skill**：打开本仓库对应目录，按其 `README.md` 或 `SKILL.md` 安装。使用 `weekly-report` 时，可以直接参考 [`weekly-report/README.md`](weekly-report/README.md) 中的安装及使用 Prompt。
- **第三方 Skill**：前往上述原项目查看其安装说明。部分 Skill 有其他依赖，不能保证仅复制单个 `SKILL.md` 就可以正常运行。

