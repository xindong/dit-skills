# dit-skills

XD Digital IT 团队可复用的 XD Maker/Codex / Claude Code skills 集合。

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

### `xdoa-skill`

`xdoa` 的主入口 skill。主 skill 负责安装、升级、能力总览和路由到子 skill 文件；具体 CLI 使用、文档检索、流程提交细节按需从子文件读取。

适用场景：

- 查询办公制度、VPN、账号、SSO、设备、会议室、工位、内网系统等内部知识
- 查询当前用户自己的资产、会议室预定、工位、待办审批、OKR 等实时数据
- 搜索、构建、确认并提交 OA / Flow 审批流程

结构：

- 主 skill：`skills/xdoa-skill/SKILL.md`
- 子 skill 文件：`references/cli-skill.md`
- 子 skill 文件：`references/doc-skill.md`
- 子 skill 文件：`references/flow-skill.md`

核心能力：

- 若未安装 `xdoa`，先自动执行安装脚本
- 执行 `xdoa version` 时如果发现有新版本，提示再次执行安装脚本完成升级
- 说明 `xdoa` 的主要能力边界，并按任务类型路由到子 skill 文件
- `cli-skill`：说明 auth、自动刷新、静默补 token、通用命令使用和实时 OA 查询
- `doc-skill`：说明 `xdoa doc query` / `xdoa doc view` 的文档检索工作流
- `flow-skill`：说明 `xdoa flow` 的搜索、构造、确认、提交、验证工作流

安装：

```bash
npx skills add xindong/dit-skills --skill xdoa-skill
```

## 贡献方式

如果你要新增或更新某个 skill，建议保持以下结构：

- skill 目录名与 skill 名称一致
- 入口文件固定为 `skills/<skill-name>/SKILL.md`
- 在根 README 同步补充该 skill 的能力说明、适用场景和安装方式
