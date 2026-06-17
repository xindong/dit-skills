# dit-skills

XD Digital IT 团队可复用的 Codex / Claude Code skills 集合。

这些 skill 主要用于两类场景：

- 团队内部通用效率能力
- 结合公司内部系统或工作流的专项能力

## 目录结构

```text
skills/<skill-name>/SKILL.md
```

## 安装

不建议一次性全部安装，推荐按需安装单个 skill。

```bash
# install all skills
npx skills add xindong/dit-skills

# install only one skill
npx skills add xindong/dit-skills --skill <skill-name>
```

## 当前 Skill 列表

### `codex-token-summary`

统计本机 Codex 最近一段时间的 Token 消耗，并输出按任务目的、模型和 Token 类型拆分的中文统计结果。

适用场景：

- 想看最近 7 天或 30 天 Codex 消耗了多少
- 想按任务/模型看 Token 分布
- 想导出 JSON 做进一步分析

核心能力：

- 读取本机 `~/.codex` 下的状态库与会话 JSONL
- 统计 `input_tokens`、`cached_input_tokens`、`output_tokens`、`reasoning_output_tokens`
- 输出表格或 JSON
- 支持时间范围、时区、是否排除周末等参数

安装：

```bash
npx skills add xindong/dit-skills --skill codex-token-summary
```

### `project-sess-summary`

把项目开发对话中的高价值上下文沉淀为结构化记忆文件，并结合 `jcemb` 做向量化检索，帮助新会话快速召回历史约束和决策。

适用场景：

- 长周期项目需要保留业务约束和架构决策
- 新开对话时希望自动召回历史背景
- 想减少重复解释、重复梳理需求

核心能力：

- 将对话总结为结构化 Markdown 记忆文件
- 规范记忆文件命名和目录组织
- 通过 `jcemb scan` 做向量化入库
- 通过 `jcemb query` 检索项目历史记忆

安装：

```bash
npx skills add xindong/dit-skills --skill project-sess-summary
```

### `xdoa-office-docs`

基于 `xdoa` CLI 的办公文档检索、个人 OA 实时查询、以及 Flow/OA 流程提交辅助 skill。这个 skill 已经合并了 CLI 使用说明、自动安装说明、知识检索工作流和流程提交工作流。

适用场景：

- 查询办公制度、VPN、账号、SSO、设备、会议室、工位、内网系统等内部知识
- 查询当前用户自己的资产、会议室预定、工位、待办审批、OKR 等实时数据
- 搜索、构建、确认并提交 OA / Flow 审批流程

核心能力：

- 若未安装 `xdoa`，先自动执行安装脚本
- 使用 `xdoa doc query` / `xdoa doc view` 检索和阅读内部文档
- 使用 `xdoa asset` / `reserve` / `space` / `okr` / `flow get task` 处理用户态 OA 查询
- 使用 `xdoa flow search` / `form` / `build` / `submit` 完成流程提交前后的标准操作
- 明确要求提交流程前先做人类可读确认，避免直接提交敏感审批

安装：

```bash
npx skills add xindong/dit-skills --skill xdoa-office-docs
```

## 贡献方式

如果你要新增或更新某个 skill，建议保持以下结构：

- skill 目录名与 skill 名称一致
- 入口文件固定为 `skills/<skill-name>/SKILL.md`
- 在根 README 同步补充该 skill 的能力说明、适用场景和安装方式
