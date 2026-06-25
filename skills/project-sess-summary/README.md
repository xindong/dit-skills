# project-sess-summary

项目会话记忆管理技能。将开发对话中的关键上下文（架构决策、业务约束、踩坑记录等）总结为结构化 Markdown 文件，通过 `jcemb` 向量工具实现跨对话的上下文检索与召回，解决 AI Agent "对话失忆"问题。

## 依赖：jcemb

`jcemb` 是本技能的核心 CLI 工具，负责记忆文件的向量化与检索。

### 安装

> `jcemb` 为独立 CLI 工具，需单独安装。



**MAC安装**

```bash
brew install jcemb
```

**Windwos下安装**

_依赖 `scoop`_ https://scoop.sh/


```
scoop bucket add bspiritxp https://github.com/bspiritxp/scoop-bucket.git
scoop install jcemb
```



安装后验证和配置：

```bash
jcemb version
jcemb config
```

若命令不可用，请检查 PATH 环境变量。

> 配置可选择使用 openai ，然后使用taptap的endpoint和api_key

### 基本使用

**扫描并向量化记忆文件：**

```bash
# 递归扫描 memory/ 目录下所有 .md 文件，执行向量化并入库
jcemb scan ./memory -r
```

**检索历史记忆：**

```bash
# 根据关键词检索相关记忆，以 JSON 格式输出
jcemb query "用户登录模块的业务约束" --path ./memory --json
```

**参数说明：**

| 参数              | 命令      | 说明                            |
| --------------- | ------- | ----------------------------- |
| `<path>`        | `scan`  | 必选，要扫描的记忆文件目录（通常为 `./memory`） |
| `-r`            | `scan`  | 可选，递归扫描子目录                    |
| `"<query>"`     | `query` | 必选，检索关键词/自然语言提问，需用双引号包裹       |
| `--path <path>` | `query` | 必选，检索目标目录（与 scan 的 path 一致）   |
| `--json`        | `query` | 可选，以 JSON 格式输出结果，便于 Agent 解析  |

## AGENTS.tmp.md 使用说明

`AGENTS.tmp.md` 是一个**项目自动化规范模板**，将其内容追加到目标项目的 `AGENTS.md` 或 `CLAUDE.md` 后，AI Agent 将在该项目中自动执行记忆管理的完整生命周期。

### 1. 引入到项目

将 `AGENTS.tmp.md` 的内容复制到目标项目的 `AGENTS.md` 或 `CLAUDE.md` 末尾：

```bash
cat skills/project-sess-summary/AGENTS.tmp.md >> /path/to/your-project/AGENTS.md
```

### 2. 自动化行为

引入后，Agent 会自动触发以下三个环节：

| 阶段                 | 触发时机          | Agent 行为                                                 |
| ------------------ | ------------- | -------------------------------------------------------- |
| **召回 (Recall)**    | 新需求/重构/排查 Bug | 静默执行 `jcemb query "<核心词>" --path ./memory --json`，检索历史约束 |
| **总结 (Summarize)** | 任务完成并确认       | 按价值判定标准过滤：高价值内容生成 `.md` 记忆文件存入 `memory/`，低价值跳过           |
| **入库 (Scan)**      | 总结并落盘后        | 自动执行 `jcemb scan ./memory -r`，增量向量化新记忆                   |

### 3. 记忆价值判定标准

AGENTS.tmp.md 内置了过滤器，Agent 会自行判断是否值得总结：

- **必须总结**：架构选型、业务约束、踩坑复盘、编码规范约定、接口设计
- **禁止总结**：拼写修复、基础 API 询问、一次性脚本、常规 CRUD 代码

### 4. 目录结构

引入后，项目中将出现 `memory/` 目录：

```
your-project/
├── AGENTS.md              # 已追加 AGENTS.tmp.md 内容
├── memory/                # 记忆文件目录（由 Agent 自动创建和维护）
│   ├── 2026-05-08_需求与业务约束_用户登录模块.md
│   ├── 2026-05-09_修改记录与踩坑总结_订单接口参数调整.md
│   └── 2026-05-10_编码规范与写法约定_Go语言命名.md
└── ...
```

## 技能安装

```bash
npx skills add bspiritxp/JC-Skills --skill project-sess-summary
```
