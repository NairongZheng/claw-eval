# Tasks Generator

这里放的是 **task family 级别** 的生成入口。

## 约定结构

每个可批量生成的 case 放在独立目录下：

- `tasks_generator/T003zh_calendar_scheduling/`
  - `generate.py`
  - `README.md`
- `tasks_generator/T004_calendar_scheduling/`
  - `generate.py`
  - `README.md`
- `tasks_generator/T029zh_cross_service_meeting/`
  - `generate.py`
  - `README.md`
- `tasks_generator/T030_cross_service_meeting/`
  - `generate.py`
  - `README.md`
- `tasks_generator/T091_pinbench_humanize_blog/`
  - `generate.py`
  - `README.md`

可复用方法与经验沉淀放在：

- `tasks_generator/task_generator_skills/`
  - `AGENT_SKILL_PLAYBOOK.md`

## 设计原则

- `tasks_generator/` 负责“怎么生成”
- `tasks/` 负责“最终 benchmark 读取的任务产物”
- 每个生成出的 task 必须自包含，至少包括：
  - `task.yaml`
  - `grader.py`
  - `generation_meta.json`
  - `fixtures/...`

## 推荐使用方式

在仓库根目录执行某个 family 的 `generate.py`，并通过 `--output-dir` 指定输出目录。

例如：

```bash
/Users/zhengnairong/miniconda3/envs/dev/bin/python tasks_generator/T003zh_calendar_scheduling/generate.py --output-dir tasks --count 10 --force
```
