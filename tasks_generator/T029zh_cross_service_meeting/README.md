# T029zh Cross-Service Meeting Generator

用于批量生成 `T029zh_cross_service_meeting` 变体任务。

## 用法

在仓库根目录执行：

```bash
/Users/zhengnairong/miniconda3/envs/dev/bin/python tasks_generator/T029zh_cross_service_meeting/generate.py --output-dir tasks --count 10 --force
```

## 常用参数

- `--output-dir`：输出目录（默认 `tasks`）
- `--count`：生成数量
- `--start-index`：起始编号
- `--seed`：随机种子
- `--id-prefix`：任务前缀（默认 `Tgen_T029zh_cross_service_meeting_gen`）
- `--force`：覆盖已存在目录

## 输出内容

每个任务包含：

- `task.yaml`
- `grader.py`（standalone）
- `generation_meta.json`
- `fixtures/gmail/inbox.json`
- `fixtures/contacts/contacts.json`
- `fixtures/calendar/events.json`

## 多样性说明（结构性，不是仅改名字）

生成器会在不同 scenario 下变化以下约束：

- 会议时长：60 / 90 / 120 分钟
- 时间粒度：支持半点（如 13:30-15:00）
- 冲突拓扑：工程与产品各自不同 busy 区间
- 场地约束：线下会议室 / Zoom / Google Meet 等
- 回复要求：部分场景必须在邮件中包含备选时间

> 注意：`task.yaml` 默认按 benchmark 约定引用 `tasks/<task_id>/fixtures/...`。如果先输出到其他目录，评测前请放回 `tasks/<task_id>/`。
