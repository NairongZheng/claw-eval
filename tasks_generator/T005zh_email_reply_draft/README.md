# T005zh Email Reply Draft Generator

用于批量生成 `T005zh_email_reply_draft` 中文变体任务。

## Usage

在仓库根目录执行：

```bash
python tasks_generator/T005zh_email_reply_draft/generate.py --output-dir tasks --count 10 --force

python tasks_generator/T005zh_email_reply_draft/generate.py --output-dir tasks_gen/T005zh_email_reply_draft --count 50 --force
```

## Common flags

- `--output-dir`: 输出目录，默认 `tasks`
- `--count`: 生成数量
- `--start-index`: 起始编号
- `--seed`: 随机种子
- `--id-prefix`: 任务 ID 前缀，默认 `Tgen_T005zh_email_reply_draft_gen`
- `--force`: 覆盖已存在目录

## Outputs

每个生成任务都会包含：

- `task.yaml`
- `grader.py`（standalone）
- `generation_meta.json`
- `local_gmail_server.py`
- `fixtures/gmail/inbox.json`

## Diversity model

这个 generator 会同时变化：

- 客户线程：客户身份、项目名、延期背景、补救措施、催办措辞
- 老板转发：老板身份、竞品对象、报告周期、重点关注维度
- 干扰邮件：监控告警、HR投票、内部通知、培训邀请、newsletter
- prompt 表达：不同中文任务指令和输出偏好提示

任务核心保持一致：

- 识别客户线程邮件并起草回复草稿
- 识别老板转发的竞品/研究邮件并起草回复草稿
- 只能 `save draft`，不能直接 `send`

> 注意：`task.yaml` 中 fixture 路径按 benchmark 约定写成 `tasks/<task_id>/fixtures/...`。如果先生成到别处，评测前需要把任务目录移动到 `tasks/<task_id>/`。