# Codex Token 消耗统计脚本

本脚本提供灵活的参数化 Token 消耗统计能力，支持自定义时间范围、输出格式和时区设置。

## 快速开始

### macOS / Linux

```bash
# 最近 7 天简单表格（默认）
python codex_token_summary.py

# 最近 30 天
python codex_token_summary.py --days 30

# 自定义日期范围
python codex_token_summary.py --start-date 2026-04-01 --end-date 2026-05-18

# 详细格式（含 Token 分类）
python codex_token_summary.py --days 7 --format detailed

# 输出为 JSON
python codex_token_summary.py --days 14 --output json

# 包含周末
python codex_token_summary.py --days 30 --no-exclude-weekends
```

### Windows

若系统未安装 Python，先运行同目录的 PowerShell 初始化脚本：

```powershell
# 以管理员身份打开 PowerShell，进入脚本所在目录后执行
.\setup_python_env.ps1
```

脚本会自动：
1. 检测现有 Python 版本
2. 未安装时从 python.org 下载官方安装包并静默安装
3. 将 Python 加入用户 PATH
4. 安装 `backports.zoneinfo`（仅 Python < 3.9 时需要）
5. 验证 `codex_token_summary.py` 可正常运行

安装完成后即可使用上面的 `python codex_token_summary.py ...` 命令。

## 参数说明

### 时间范围

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--days N` | 最近 N 天（包含今天） | 7 | `--days 30` |
| `--start-date YYYY-MM-DD` | 自定义开始日期（覆盖 --days） | 无 | `--start-date 2026-04-01` |
| `--end-date YYYY-MM-DD` | 自定义结束日期 | 今天 | `--end-date 2026-05-18` |

### 输出格式

| 参数 | 说明 | 默认值 | 选项 |
|------|------|--------|------|
| `--format` | 输出详细程度 | simple | simple / detailed |
| `--output` | 输出类型 | table | table / json |

### 工作日设置

| 参数 | 说明 |
|------|------|
| `--exclude-weekends` | 排除周末工作日（默认开启） |
| `--no-exclude-weekends` | 包含周末 |

### 其他

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--tz TIMEZONE` | 时区（tz database format） | Asia/Shanghai |
| `--help` | 显示帮助信息 | - |

## 输出示例

### 简单模式（默认）

```
**合计 Token**：1,657,414（100%）

| 任务目的 | 模型 | Token 总量 | 占比 |
| ---- | --- | --------:| ---:|
| `估算配置市场价` | `gpt-5.5` | 1,392,466 | 84.01% |
| `添加 Makefile 构建与检查` | `gpt-5.5` | 264,948 | 15.99% |

补充说明：
- 时间范围：2026-04-26 至 2026-05-18
- 工作日数：5
- 本机事件日期范围：2026-04-26 至 2026-05-03
- 数据一致性：✓
```

### 详细模式

```
**合计 Token**：1,657,414（100%）

| 任务目的 | 模型 | Token 总量 | 占比 | 新输入/检索上下文 | 缓存输入 | 输出/写代码 | 思考 |
| ---- | --- | --------:| ---:| ---------:| ----:| ------:| ---:|
| `估算配置市场价` | `gpt-5.5` | 1,392,466 | 84.01% | 139,247 (10.0%) | 1,183,596 (85.0%) | 55,699 (4.0%) | 13,925 (1.0%) |
```

### JSON 输出

完整的 JSON 结构包含：
- `state_db`：使用的 SQLite 数据库路径
- `window`：时间窗口和工作日范围
- `grand_total`：总 Token 数
- `rows`：按任务目的聚合的详细数据
- `consistency`：数据一致性检查结果

## 实际用例

### 用例 1：周报统计

最近 7 个工作日（排除周末）的 Token 消耗：

```bash
python codex_token_summary.py --days 7
```

### 用例 2：月度对账

4 月份全月统计：

```bash
python codex_token_summary.py --start-date 2026-04-01 --end-date 2026-04-30 --no-exclude-weekends
```

### 用例 3：导出数据分析

获取原始 JSON 数据用于后续分析：

```bash
python codex_token_summary.py --days 30 --output json > token_data.json
```

### 用例 4：详细分类查看

查看 Token 在输入/缓存/输出/思考各环节的分布：

```bash
python codex_token_summary.py --days 14 --format detailed
```

## 技术细节

### 数据来源

1. **状态库**（`~/.codex/state_*.sqlite`）
   - 脚本自动定位最新可用的状态库
   - 查询 `threads` 表获取线程元数据（ID、rollout 路径、模型、标题等）

2. **会话 JSONL**（rollout 文件）
   - 按 `threads.rollout_path` 定位
   - 读取 `token_count` 事件
   - 计算相邻事件间的增量（避免重复计数）

### 工作日定义

- **默认**：周一至周五（`weekday < 5`）
- **可选**：全周 7 天

### Token 分类

仅当 rollout JSONL 包含结构化字段时可用：
- `new_input`：新输入 Token
- `cached_input`：缓存输入 Token  
- `output`：输出 Token
- `reasoning`：思考 Token

### 错误处理

脚本会自动：
- 跳过缺失 rollout 文件的线程
- 捕获 JSONL 读取错误
- 验证数据一致性（会话增量和 = 聚合总和）

## 常见问题

### Q: 为什么最近 7 天显示 0 Token？

A: 脚本会检查事件时间戳。如果本机 Codex 最近 7 天内无活动，结果将为 0。可用 `--start-date` / `--end-date` 覆盖范围查看有数据的时段。

### Q: 如何修改时区？

A: 使用 `--tz` 参数，如：

```bash
python codex_token_summary.py --days 7 --tz America/New_York
```

### Q: 能否只统计某个特定模型？

A: 当前脚本按任务目的聚合；如需按模型过滤，可使用 JSON 输出再后处理。

### Q: 数据不一致是什么意思？

A: "数据一致性"检查相邻会话增量总和是否等于最后聚合总数。如显示 `✗`，可能表示：
- 某些 JSONL 文件读取失败
- 时间戳解析异常

建议检查 `missing_rollout_samples` 和 `no_token_count_threads_samples` 列表。

## 集成建议

### 定时任务（Windows Task Scheduler）

```powershell
# 创建任务脚本
$TaskAction = New-ScheduledTaskAction -Execute 'python' -Argument '"C:\Users\Administrator\.agents\skills\codex-token-summary\codex_token_summary.py" --days 7 >> C:\logs\token_summary.log'
$TaskTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9AM
Register-ScheduledTask -Action $TaskAction -Trigger $TaskTrigger -TaskName "CodexTokenSummary"
```


## 许可与归属

脚本遵循 Codex Token Summary 技能规范，基于 `codex-token-summary` SKILL.md 实现。
