# T003zh Calendar Scheduling Generator

这个目录包含 `T003zh_calendar_scheduling` 这一类任务的**完整生成入口**。

## 目录说明

- `generate.py`：生成脚本
- `README.md`：使用说明

## 用法

在仓库根目录执行：

```bash
/Users/zhengnairong/miniconda3/envs/dev/bin/python tasks_generator/T003zh_calendar_scheduling/generate.py --output-dir tasks --count 6 --force
```

这是**推荐方式**，因为生成出来的 `task.yaml` 默认假设最终 task 会放在 benchmark 的 `tasks/<task_id>/` 下面，并直接引用 `tasks/<task_id>/local_calendar_server.py`。

如果你想输出到别的目录：

```bash
/Users/zhengnairong/miniconda3/envs/dev/bin/python tasks_generator/T003zh_calendar_scheduling/generate.py --output-dir /tmp/calendar_tasks --count 20
```

注意：如果先输出到别的目录再手动拷贝进 `tasks/`，也是可以的；但**真正评测前**需要保证目录最终位于 `tasks/<task_id>/`。

## 常用参数

- `--output-dir`：输出目录，生成的 task 会写到这个目录下
- `--count`：生成多少个变体
- `--start-index`：起始编号
- `--seed`：随机种子
- `--id-prefix`：任务 ID 前缀（默认：`Tgen_T003zh_calendar_scheduling_gen`）
- `--force`：若目标 task 已存在则覆盖

## 输出结构

每个生成的 task 目录都会包含：

- `task.yaml`
- `grader.py`
- `generation_meta.json`
- `local_calendar_server.py`
- `fixtures/calendar/events.json`

## 说明

这个生成器是 **family 级入口**，目标是：

1. 让你直接看目录就知道怎么跑
2. 每个生成 task 自包含，不依赖共享 grader，也不依赖额外修改 benchmark 源码
3. 后续可以按这个模式继续扩成别的 task family
