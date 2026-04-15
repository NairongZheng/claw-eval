# T091 Pinbench Humanize Blog Generator

用于批量生成 `T091_pinbench_humanize_blog` 英文改写任务变体。

## Usage

在仓库根目录执行：

```bash
python tasks_generator/T091_pinbench_humanize_blog/generate.py --output-dir tasks --count 50 --force

python tasks_generator/T091_pinbench_humanize_blog/generate.py --output-dir tasks_gen/T091_pinbench_humanize_blog --count 50 --force
```

## Common flags

- `--output-dir`: 输出目录（默认 `tasks`）
- `--count`: 生成数量
- `--start-index`: 起始编号
- `--seed`: 随机种子
- `--id-prefix`: 任务前缀（默认 `Tgen_T091_pinbench_humanize_blog_gen`）
- `--force`: 覆盖已存在目录

## Outputs

每个任务包含：

- `task.yaml`
- `grader.py`（standalone）
- `generation_meta.json`
- `fixtures/docs/ai_blog.txt`

## Diversity knobs

- 原文业务语境（团队场景）
- Prompt 描述库随机组合（opener / audience / style guard / format / preserve rule）
- 写作风格提示（prompt voice hint）
- grader 侧的禁用机械短语子集
- 长度要求阈值（850/900/950）
