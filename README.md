# my-skills

个人 Agent Skills 集合。每个技能位于同名目录，入口文件为 `SKILL.md`，可包含 `agents/openai.yaml`、参考文档和脚本。技能适配的平台和工具要求以各自目录中的说明为准；技能目录名与 `SKILL.md` frontmatter 中的 `name` 保持一致。

## Skills

### ChatGPT 与技能管理

- [`chatgpt-model-consistency`](chatgpt-model-consistency/)：核对 ChatGPT 网页请求的模型与服务端实际标注的模型是否一致。
- [`codex-with-chatgpt`](codex-with-chatgpt/)：让 ChatGPT 网页协助 Codex 规划、评审和排查问题，由 Codex 负责执行。
- [`find-skills`](find-skills/)：在开放的 Agent Skills 生态中发现和安装技能。
- [`manage-skills`](manage-skills/)：通过 Skills Manager 管理共享技能库、预设和各 Agent 的部署。

### 设计与测试

- [`grill-me`](grill-me/)：通过访谈打磨计划或设计。
- [`grill-with-docs`](grill-with-docs/)：通过访谈打磨设计，并整理 ADR 和领域词汇表。
- [`tdd`](tdd/)：指导测试先行、行为测试边界、测试替身和 Red-Green 循环。

### Git 与交付

- [`release-changelog`](release-changelog/)：根据 Git tag 或 commit 范围编写中文 GitHub Release changelog。
- [`safe-pr-branch-workflow`](safe-pr-branch-workflow/)：为代码改动准备任务分支、验证结果和 Conventional Commit/PR 交接。
- [`split-commit-prs`](split-commit-prs/)：将已有 commit 拆分为可独立合并的 PR 分支。
- [`triage`](triage/)：按状态流转分类和核验 issue 或外部 PR，并整理 agent brief。

### 界面验证

- [`flet-headless-ui-verify`](flet-headless-ui-verify/)：通过模拟 Page 和控件树断言，在无窗口环境下验证 Flet 界面。
- [`pyside6-headless-ui-verify`](pyside6-headless-ui-verify/)：通过 offscreen Qt 探针验证 PySide6/PyQt 界面行为和布局。

### 文档与汇报

- [`weekly-report`](weekly-report/)：根据当周工时截图和公司周报模板核对内容、展示预览，并在确认后生成保留模板格式的 DOCX。

## 安装与使用

不同 AI 助手的 Skill 安装方式不同，请按对应技能目录中的 README 操作。只想使用周报生成时，打开 [`weekly-report/README.md`](weekly-report/README.md)，将其中的一条 Prompt 与周报模板、当周工时截图一起发送给支持 Agent Skills 的 AI 助手；Prompt 会要求助手自行安装并执行该技能。
