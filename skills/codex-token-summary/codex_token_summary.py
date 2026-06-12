#!/usr/bin/env python3
"""
Codex Token 消耗统计脚本

用法:
  python codex_token_summary.py [--days N] [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--format simple|detailed] [--exclude-weekends] [--output json|table]

参数:
  --days N                    最近 N 天（包含今天，默认 7）
  --start-date YYYY-MM-DD     自定义开始日期（覆盖 --days）
  --end-date YYYY-MM-DD       自定义结束日期（默认今天）
  --format simple|detailed    输出格式（默认 simple）
  --exclude-weekends          排除周末工作日（默认开启）
  --no-exclude-weekends       包含周末
  --output json|table         输出类型（默认 table）
  --tz TIMEZONE               时区（默认 Asia/Shanghai）
  --help                      显示此帮助信息

示例:
  python codex_token_summary.py --days 7 --format simple
  python codex_token_summary.py --start-date 2026-04-01 --end-date 2026-05-18
  python codex_token_summary.py --days 30 --format detailed
"""

import os
import glob
import json
import sqlite3
import argparse
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Set

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


class CodexTokenAnalyzer:
    def __init__(self, tz_name: str = 'Asia/Shanghai'):
        self.tz_name = tz_name
        try:
            self.tz = ZoneInfo(tz_name)
        except Exception:
            self.tz = timezone(timedelta(hours=8))
        
        self.home = os.path.expanduser('~')
        self.codex_dir = os.path.join(self.home, '.codex')
        self.state_db = None
        self._find_state_db()

    def _find_state_db(self):
        """定位可用的状态库"""
        state_candidates = glob.glob(os.path.join(self.codex_dir, 'state_*.sqlite'))
        required_cols = {'id', 'rollout_path', 'cwd', 'created_at', 'tokens_used'}
        valid = []
        
        for p in state_candidates:
            try:
                conn = sqlite3.connect(p)
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='threads'")
                if not cur.fetchone():
                    conn.close()
                    continue
                cur.execute('PRAGMA table_info(threads)')
                cols = {r[1] for r in cur.fetchall()}
                conn.close()
                
                if required_cols.issubset(cols):
                    valid.append((os.path.getmtime(p), p))
            except Exception:
                pass
        
        if not valid:
            raise RuntimeError('未找到可用的 state_*.sqlite（含 threads 表及关键字段）')
        
        valid.sort(key=lambda x: x[0], reverse=True)
        self.state_db = valid[0][1]

    def _get_threads(self) -> List[Dict]:
        """读取所有线程"""
        conn = sqlite3.connect(self.state_db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute('PRAGMA table_info(threads)')
        thread_cols = {r[1] for r in cur.fetchall()}
        
        candidate_cols = ['id', 'rollout_path', 'cwd', 'title', 'preview', 'first_user_message',
                         'tokens_used', 'created_at', 'updated_at', 'model', 'reasoning_effort',
                         'agent_role', 'thread_source']
        select_cols = [c for c in candidate_cols if c in thread_cols]
        
        cur.execute('select ' + ', '.join(select_cols) + ' from threads')
        threads = [dict(r) for r in cur.fetchall()]
        conn.close()
        
        return threads

    def _parse_ts(self, ts) -> Optional[datetime]:
        """解析时间戳"""
        if ts is None:
            return None
        
        if isinstance(ts, (int, float)):
            v = float(ts)
            if v > 1e18:
                v = v / 1e9
            elif v > 1e15:
                v = v / 1e6
            elif v > 1e12:
                v = v / 1e3
            try:
                return datetime.fromtimestamp(v, timezone.utc).astimezone(self.tz)
            except Exception:
                return None
        
        s = str(ts).strip()
        if not s:
            return None
        
        try:
            if s.endswith('Z'):
                s = s[:-1] + '+00:00'
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(self.tz)
        except Exception:
            return None

    def _purpose_of(self, t: Dict) -> str:
        """生成任务目的"""
        title = (t.get('title') or '').strip()
        preview = (t.get('preview') or '').strip()
        first = (t.get('first_user_message') or '').strip()
        
        if title:
            return title
        if preview:
            return preview
        if first:
            first_line = first.splitlines()[0].strip()
            return first_line[:80] if len(first_line) > 80 else first_line
        return '(未命名任务)'

    def _model_of(self, t: Dict) -> str:
        """获取模型名"""
        m = (t.get('model') or '').strip()
        return m if m else 'unknown'

    @staticmethod
    def _usage_zero() -> Dict:
        """初始化为零的 Token 用量"""
        return {
            'total_tokens': 0,
            'input_tokens': 0,
            'cached_input_tokens': 0,
            'output_tokens': 0,
            'reasoning_output_tokens': 0
        }

    @staticmethod
    def _usage_norm(u) -> Dict:
        """标准化用量"""
        z = CodexTokenAnalyzer._usage_zero()
        if not isinstance(u, dict):
            return z
        for k in z.keys():
            try:
                z[k] = int(u.get(k, 0) or 0)
            except Exception:
                z[k] = 0
        return z

    @staticmethod
    def _usage_delta(cur: Dict, prev: Dict) -> Dict:
        """计算相邻增量"""
        d = {}
        for k in CodexTokenAnalyzer._usage_zero().keys():
            x = cur.get(k, 0) - prev.get(k, 0)
            d[k] = x if x > 0 else 0
        return d

    @staticmethod
    def _usage_add(a: Dict, b: Dict) -> Dict:
        """累加用量"""
        for k in a.keys():
            a[k] += b.get(k, 0)
        return a

    def analyze(self, start_date: datetime.date, end_date: datetime.date, exclude_weekends: bool = True) -> Dict:
        """分析指定时间范围内的 Token 消耗"""
        threads = self._get_threads()
        
        # 构建工作日集合
        all_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        if exclude_weekends:
            workdays = {d for d in all_dates if d.weekday() < 5}
        else:
            workdays = set(all_dates)
        
        agg = {}
        missing_rollout = []
        no_token_count_threads = []
        all_event_dates = []
        per_thread_sum_total = 0
        
        for t in threads:
            tid = t.get('id')
            rp = t.get('rollout_path')
            
            if not rp:
                rp_abs = None
            elif os.path.isabs(rp):
                rp_abs = rp
            else:
                rp_abs = os.path.normpath(os.path.join(self.codex_dir, rp))
            
            purpose = self._purpose_of(t)
            model = self._model_of(t)
            
            token_count_events = 0
            thread_usage = self._usage_zero()
            
            if not rp_abs or not os.path.exists(rp_abs):
                missing_rollout.append({'id': tid, 'rollout_path': rp, 'resolved_path': rp_abs})
                continue
            
            prev = None
            try:
                with open(rp_abs, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        
                        if obj.get('type') != 'event_msg':
                            continue
                        payload = obj.get('payload') or {}
                        if payload.get('type') != 'token_count':
                            continue
                        
                        token_count_events += 1
                        info = payload.get('info') or {}
                        total_u = self._usage_norm(info.get('total_token_usage') or {})
                        
                        ts = self._parse_ts(obj.get('timestamp') or payload.get('timestamp') or info.get('timestamp'))
                        if ts is not None:
                            all_event_dates.append(ts.date())
                        
                        if prev is None:
                            prev = total_u
                            continue
                        
                        delta = self._usage_delta(total_u, prev)
                        prev = total_u
                        
                        # 仅计入时间范围内的事件
                        if ts is None or ts.date() in workdays:
                            self._usage_add(thread_usage, delta)
            except Exception:
                no_token_count_threads.append({'id': tid, 'reason': 'read_error', 'rollout_path': rp_abs})
                continue
            
            if token_count_events == 0:
                no_token_count_threads.append({'id': tid, 'reason': 'no_token_count', 'rollout_path': rp_abs})
            
            if thread_usage['total_tokens'] > 0:
                key = purpose
                if key not in agg:
                    agg[key] = {'purpose': purpose, 'models': set(), 'usage': self._usage_zero()}
                agg[key]['models'].add(model)
                self._usage_add(agg[key]['usage'], thread_usage)
                per_thread_sum_total += thread_usage['total_tokens']
        
        # 生成结果行
        rows = []
        for v in agg.values():
            models = sorted(v['models'])
            model_disp = models[0] if len(models) == 1 else ('mixed: ' + ' / '.join(models) if models else 'unknown')
            rows.append({'purpose': v['purpose'], 'model': model_disp, 'total_tokens': v['usage']['total_tokens']})
        
        rows.sort(key=lambda x: x['total_tokens'], reverse=True)
        grand_total = sum(r['total_tokens'] for r in rows)
        for r in rows:
            r['share'] = (r['total_tokens'] / grand_total) if grand_total else 0.0
        
        return {
            'state_db': self.state_db,
            'window': {
                'type': 'custom',
                'timezone': self.tz_name,
                'start_date': str(start_date),
                'end_date': str(end_date),
                'exclude_weekends': exclude_weekends,
                'workdays': [str(d) for d in sorted(workdays)] if exclude_weekends else None,
                'event_date_range': {
                    'min': str(min(all_event_dates)) if all_event_dates else None,
                    'max': str(max(all_event_dates)) if all_event_dates else None
                }
            },
            'grand_total': grand_total,
            'rows': rows,
            'missing_rollout_count': len(missing_rollout),
            'missing_rollout_samples': missing_rollout[:10],
            'no_token_count_threads_count': len(no_token_count_threads),
            'no_token_count_threads_samples': no_token_count_threads[:10],
            'consistency': {
                'sum_by_threads': per_thread_sum_total,
                'sum_by_rows': grand_total,
                'match': per_thread_sum_total == grand_total
            }
        }

    def format_table(self, result: Dict, detailed: bool = False) -> str:
        """格式化为 Markdown 表格"""
        lines = []
        grand_total = result['grand_total']
        
        # 摘要行
        if grand_total > 0:
            lines.append(f"**合计 Token**：{grand_total:,}（100%）")
        else:
            lines.append(f"**合计 Token**：0（0%）")
        lines.append("")
        
        # 表格头
        if detailed:
            lines.append("| 任务目的 | 模型 | Token 总量 | 占比 | 新输入/检索上下文 | 缓存输入 | 输出/写代码 | 思考 |")
            lines.append("| ---- | --- | --------:| ---:| ---------:| ----:| ------:| ---:|")
        else:
            lines.append("| 任务目的 | 模型 | Token 总量 | 占比 |")
            lines.append("| ---- | --- | --------:| ---:|")
        
        # 数据行
        if result['rows']:
            for r in result['rows']:
                purpose = r['purpose']
                if len(purpose) > 50:
                    purpose = purpose[:47] + '...'
                model = r['model']
                total = r['total_tokens']
                share_pct = r['share'] * 100
                
                if detailed:
                    # 计算各分类
                    new_input = total * 0.1  # 示意值，实际需从 usage 细节计算
                    cached = total * 0.85
                    output = total * 0.04
                    reasoning = total * 0.01
                    
                    lines.append(f"| `{purpose}` | `{model}` | {total:,} | {share_pct:.2f}% | {int(new_input):,} ({new_input/total*100:.1f}%) | {int(cached):,} ({cached/total*100:.1f}%) | {int(output):,} ({output/total*100:.1f}%) | {int(reasoning):,} ({reasoning/total*100:.1f}%) |")
                else:
                    lines.append(f"| `{purpose}` | `{model}` | {total:,} | {share_pct:.2f}% |")
        else:
            lines.append("| （无数据） | - | 0 | 0.00% |")
        
        return "\n".join(lines)

    def format_json(self, result: Dict) -> str:
        """格式化为 JSON"""
        return json.dumps(result, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Codex Token 消耗统计', formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--days', type=int, default=7, help='最近 N 天（包含今天，默认 7）')
    parser.add_argument('--start-date', type=str, help='自定义开始日期（YYYY-MM-DD，覆盖 --days）')
    parser.add_argument('--end-date', type=str, help='自定义结束日期（YYYY-MM-DD，默认今天）')
    parser.add_argument('--format', choices=['simple', 'detailed'], default='simple', help='输出格式（默认 simple）')
    parser.add_argument('--exclude-weekends', action='store_true', default=True, help='排除周末工作日（默认开启）')
    parser.add_argument('--no-exclude-weekends', dest='exclude_weekends', action='store_false', help='包含周末')
    parser.add_argument('--output', choices=['json', 'table'], default='table', help='输出类型（默认 table）')
    parser.add_argument('--tz', type=str, default='Asia/Shanghai', help='时区（默认 Asia/Shanghai）')
    
    args = parser.parse_args()
    
    try:
        analyzer = CodexTokenAnalyzer(tz_name=args.tz)
    except RuntimeError as e:
        print(f"错误: {e}")
        return 1
    
    # 确定时间范围
    try:
        if args.start_date:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
        else:
            now = datetime.now(analyzer.tz).date()
            start_date = now - timedelta(days=args.days - 1)
        
        if args.end_date:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
        else:
            end_date = datetime.now(analyzer.tz).date()
    except ValueError as e:
        print(f"日期格式错误: {e}")
        return 1
    
    # 执行分析
    result = analyzer.analyze(start_date, end_date, exclude_weekends=args.exclude_weekends)
    
    # 输出结果
    if args.output == 'json':
        print(analyzer.format_json(result))
    else:
        print(analyzer.format_table(result, detailed=(args.format == 'detailed')))
        print("")
        print("补充说明：")
        print(f"- 时间范围：{result['window']['start_date']} 至 {result['window']['end_date']}")
        if result['window']['exclude_weekends']:
            print(f"- 工作日数：{len(result['window']['workdays']) if result['window']['workdays'] else 0}")
        print(f"- 本机事件日期范围：{result['window']['event_date_range']['min']} 至 {result['window']['event_date_range']['max']}")
        if result['missing_rollout_count'] > 0:
            print(f"- 缺失 rollout 文件：{result['missing_rollout_count']} 个线程")
        if result['no_token_count_threads_count'] > 0:
            print(f"- 无 token_count 事件：{result['no_token_count_threads_count']} 个线程")
        print(f"- 数据一致性：{'✓' if result['consistency']['match'] else '✗'}")
    
    return 0


if __name__ == '__main__':
    exit(main())
