---
name: git-commiter
description: 团队 Git 工作流统一工具：基于 Conventional Commits 规范自动生成提交信息并提交，支持自动创建 GitHub PR。使用 commit-message-writer 子 agent 分析仓库变更生成标准化消息，通过 gh CLI 推送并创建 Pull Request。
version: 1.0.0
language: zh-CN
tags:
  - git
  - conventional-commits
  - commit-message
  - pr
  - github
  - workflow
  - team-standards
---

# Git Commiter — 团队标准化提交流程

## 适用场景

当用户需要将当前工作区的变更提交到 Git 仓库，或需要在 GitHub 上创建 Pull Request 时，使用本技能。适用于：

- 日常开发完成后的代码提交
- 需要生成符合 Conventional Commits 规范的提交信息
- 需要将分支推送到远端并创建 PR
- 团队希望统一提交风格，便于自动化 changelog 生成

## 核心原则

1. **提交信息由子 agent 生成，不靠主 agent 凭空编造。** 提交信息必须基于实际 `git diff` 内容分析得出。
2. **遵循 Conventional Commits 1.0.0 规范。** 格式：`<type>(<scope>): <summary>`。
3. **PR 创建为可选步骤。** 仅在用户明确要求或分支有推送需要时创建。
4. **不做多余的事。** 不自动 `git add` 未跟踪文件，不修改仓库配置，不 force push。

---

## 工作流：一键标准提交

### 完整流程

```
用户说"提交" / "commit" / "创建 PR"
        │
        ▼
┌─────────────────────────────┐
│ 1. 检查工作区状态            │
│    git status --short        │
│    → 无变更则终止，提示用户   │
└──────────────┬──────────────┘
               │ 有变更
               ▼
┌─────────────────────────────┐
│ 2. 暂存变更（如未暂存）      │
│    git add <changed-files>   │
│    ⚠ 跳过未跟踪文件          │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ 3. 生成提交信息              │
│    委托 commit-message-writer│
│    子 agent 分析 diff         │
│    → 产出 Conventional       │
│      Commits 消息            │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ 4. 提交                      │
│    git commit -m "<message>" │
└──────────────┬──────────────┘
               │ 用户要求 PR / 推送
               ▼
┌─────────────────────────────┐
│ 5. 推送 + 创建 PR（可选）    │
│    git push -u origin HEAD   │
│    gh pr create …            │
└─────────────────────────────┘
```

### Step 1: 检查工作区状态

```bash
git status --short --branch
```

- 若无任何变更（工作区干净）→ 告知用户并终止。
- 若有未暂存变更 → 进入 Step 2。
- 若已全部暂存 → 跳过 Step 2，直接进入 Step 3。

### Step 2: 暂存变更

仅暂存已跟踪文件的修改，**不自动添加未跟踪文件**（`??` 状态的文件）。

```bash
# 列出已跟踪但修改/删除的文件
git diff --name-only  # 未暂存的修改
git diff --cached --name-only  # 已暂存的修改

# 暂存已跟踪文件的变更
git add -u
```

如用户指定了具体文件，则只暂存指定文件。

### Step 3: 生成提交信息（委托子 agent）

**这是核心步骤。** 委托 `commit-message-writer` 子 agent 分析仓库变更并生成标准化提交信息。

子 agent 配置位于：`agents/commit-message-writer.toml`

**委托方式：**

使用 `task` 工具，指定 `agent` 为 `commit-message-writer`（若环境中注册了该 agent），或将子 agent 的 `developer_instructions` 作为 prompt 直接执行分析。

**子 agent 行为：**

1. 自动检测仓库默认分支（`origin/main`、`origin/master` 等）
2. 分析当前分支相对于默认分支的 diff
3. 分析暂存区和工作区的 diff
4. 生成符合 Conventional Commits 格式的提交信息
5. 输出格式：
   ````
   ```text
   feat(scope): 简洁的变更描述
   ```
   ````
   附带变更区域、类型/范围选择理由。

**消息规范：**

| 组件 | 规则 |
|------|------|
| **type** | `feat` / `fix` / `docs` / `style` / `refactor` / `perf` / `test` / `build` / `ci` / `chore` / `revert` |
| **scope** | 小写，取自主要改动的包/模块/目录名；无法确定时可省略 |
| **summary** | 祈使语气，无句号，≤72 字符 |
| **body** | 可选，仅在需补充上下文时添加，72 字符换行 |
| **footer** | `BREAKING CHANGE:` / `Closes #123` / `Refs #123`，仅在有依据时添加 |
| **破坏性变更** | type 后加 `!`：`feat(api)!: drop support for v1 endpoints` |

**主 agent 职责：**

- 接收子 agent 产出的消息
- 向用户展示并简要解释
- **低置信度时**如实告知不确定性，不强行提交

### Step 4: 执行提交

```bash
git commit -m "<子agent生成的消息>"
```

若子 agent 返回了 body/footer，使用：

```bash
git commit -m "<summary>" -m "<body>" -m "<footer>"
```

### Step 5: 推送并创建 PR（可选）

仅在以下条件之一满足时执行：
- 用户明确要求"创建 PR" / "提 PR" / "push"
- 用户要求"提交并推送"

#### 5a. 推送分支

```bash
git push -u origin HEAD
```

#### 5b. 检测 gh CLI

```bash
# 检查 gh 是否可用
which gh && gh auth status
```

- 若 `gh` 不可用或未认证 → 提示用户手动创建 PR，给出分支名和远端 URL。
- 若 `gh` 可用 → 自动创建 PR。

#### 5c. 创建 PR

```bash
gh pr create \
  --title "<commit summary>" \
  --body "<PR 描述>" \
  --base <default-branch> \
  --head <current-branch>
```

**PR 描述自动生成规则：**

```
## 变更概述
<从 git log <base>..HEAD --oneline 提取的提交列表>

## 变更内容
<根据 diff --stat 总结改动的文件和模块>
```

**PR 标题：** 使用 Step 3 生成的 commit summary，去掉 type/scope 前缀（如 `feat(api): add user endpoint` → `Add user endpoint`），或保留完整 Conventional Commits 格式（团队约定）。

---

## 使用示例

### 场景 1：快速提交

> 用户："提交"
>
> 1. `git status --short --branch` → 有 3 个修改文件
> 2. `git add -u`
> 3. 委托 `commit-message-writer` → 产出 `feat(auth): add JWT token refresh`
> 4. `git commit -m "feat(auth): add JWT token refresh"`
> 5. 完成，提示用户

### 场景 2：提交并创建 PR

> 用户："提交并创建 PR"
>
> 1-4. 同上
> 5. `git push -u origin HEAD`
> 6. 检测 `gh` → 可用
> 7. `gh pr create --title "feat(auth): add JWT token refresh" --body "..." --base main`
> 8. 输出 PR URL

### 场景 3：多文件不相关变更

> 子 agent 检测到不相关的变更 → 输出建议：
>
> ```
> 检测到两类不相关变更，建议拆分为 2 个提交：
>
> 1. feat(api): add user search endpoint
>    - src/api/users.ts, tests/api/users.test.ts
>
> 2. fix(ui): correct button alignment in navbar
>    - src/ui/Navbar.tsx
> ```
>
> 主 agent 向用户展示拆分建议，由用户决定。

---

## 错误处理

| 情况 | 处理 |
|------|------|
| 工作区干净 | 提示"没有需要提交的变更"，终止 |
| 子 agent 无法确定默认分支 | 回退到 `git diff --stat` + `git diff --cached --stat` |
| 子 agent 置信度低 | 展示消息并标注低置信度，让用户确认后再提交 |
| `gh` 未安装 | 提示安装：`brew install gh`，给出手动创建 PR 的分支名 |
| `gh` 未认证 | 提示运行 `gh auth login` |
| push 失败（无远端） | 提示添加远端：`git remote add origin <url>` |
| push 失败（权限） | 提示检查仓库权限，不自动 force push |

---

## 注意事项

- **不自动 force push。** 如需 rebase 后推送，用户需明确说明。
- **不修改 git config。** 不自动设置 `user.name`、`user.email` 等。
- **不自动合并或变基。** 分支操作由用户控制。
- **子 agent 是只读的。** 它只分析 diff、生成消息，不执行任何写操作。
- **PR body 自动生成为辅助。** 用户可在创建前审查和修改。
