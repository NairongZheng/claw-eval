# T002 Email Triage Generator

用于批量生成 `T002_email_triage` 英文变体任务。

## Usage

在仓库根目录执行：

```bash
python tasks_generator/T002_email_triage/generate.py --output-dir tasks --count 10 --force

python tasks_generator/T002_email_triage/generate.py --output-dir tasks_gen/T002_email_triage --count 50 --force
```

## Common flags

- `--output-dir`: 输出目录，默认 `tasks`
- `--count`: 生成数量
- `--start-index`: 起始编号
- `--seed`: 随机种子
- `--id-prefix`: 任务 ID 前缀，默认 `Tgen_T002_email_triage_gen`
- `--force`: 覆盖已存在目录

## Outputs

每个生成任务都会包含：

- `task.yaml`
- `grader.py`（standalone）
- `generation_meta.json`
- `fixtures/gmail/inbox.json`

## Diversity model

这个 generator 的多样性不是只换名字，而是同时变化：

- 邮件语义结构：明确需回复 / 明确 FYI / 明确 spam / 边界型邮件
- 发件人类型：经理、合作方、安全团队、HR、newsletter、spam、survey
- 行动强度：必须处理、可选回复、纯通知、诱导点击
- 提示措辞：不同 prompt 模板与输出偏好提示
- 收件箱表象：已读/未读、标签、时间分布、主题表述

其中边界型邮件会允许多种可接受分类，例如：

- `needs reply` 或 `FYI`
- `FYI` 或 `spam`

这样能更接近真实 triage 场景，同时避免生成样本过于模板化。

> 注意：`task.yaml` 中 fixture 路径按 benchmark 约定写成 `tasks/<task_id>/fixtures/...`。如果先生成到别处，评测前需要把任务目录移动到 `tasks/<task_id>/`。