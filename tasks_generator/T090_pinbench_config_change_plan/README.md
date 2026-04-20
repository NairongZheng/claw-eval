# T090 Pinbench Config Change Plan Generator

这个 family 用来生成 **自包含** 的 `config change plan` 任务变体，用于 hack / 训练 `T090_pinbench_config_change_plan` 类型能力。

## 特点

- 每个生成任务都包含自己的：
  - `task.yaml`
  - `grader.py`
  - `generation_meta.json`
  - `fixtures/config/integrations.json`
- **不再复用其他 task 目录的 fixture**
- 默认围绕：`degraded` / `expired` / `active 但存在治理缺口` 的 integration 组合
- prompt、业务场景、集成组合、风险主题、密钥形态都会变化

## 生成方式

建议在仓库根目录执行：

```bash
python tasks_generator/T090_pinbench_config_change_plan/generate.py --output-dir tasks --count 50 --force
```

如果你只是想先抽样验证，也可以输出到临时目录：

```bash
python tasks_generator/T090_pinbench_config_change_plan/generate.py --output-dir tasks_gen/T090_pinbench_config_change_plan --count 50 --force
```

## 多样性来源

- 10+ 业务场景
- 15+ 集成模板
- 多种 prompt 模板
- 不同风险主题组合
- 不同 problem service 组合
- 不同密钥/secret 字段与附加敏感字段

组合空间远大于 50 个任务，批量生成 50 个没有问题。