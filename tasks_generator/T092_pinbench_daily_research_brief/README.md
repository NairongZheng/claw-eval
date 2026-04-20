# T092 Pinbench Daily Research Brief Generator

这个 family 用来生成 **自包含** 的 `daily research brief` 任务变体，用于 hack / 训练 `T092_pinbench_daily_research_brief` 类型能力。

## 为什么要本地隔离 server

原始 `T092` 有两个耦合点：

- `task.yaml` 直接引用了其他 task 的 RSS fixture
- `mock_services/rss/server.py` 自身也 hardcode 到 `T021zh_newsletter_curation`

这个 generator 通过给每个生成任务写入自己的 `local_rss_server.py` 来隔离服务逻辑，避免共享默认路径干扰。

## 每个生成任务包含

- `task.yaml`
- `grader.py`
- `generation_meta.json`
- `fixtures/rss/articles.json`
- `local_rss_server.py`

## 生成方式

在仓库根目录执行：

```bash
python3 tasks_generator/T092_pinbench_daily_research_brief/generate.py --output-dir tasks --count 50 --force
```

抽样验证也可以输出到临时目录：

```bash
python3 tasks_generator/T092_pinbench_daily_research_brief/generate.py --output-dir tasks_gen/T092_pinbench_daily_research_brief --count 50 --force
```

## 多样性来源

- 多种 engineering leadership audience
- 多组 AI / cloud / governance / developer tooling topic clusters
- 不同 prompt 模板与 briefing goal
- 不同 focus article 组合 + distractor article 组合
- 本地 server + 本地 fixture，互不污染

组合空间远大于 50 个任务，可以稳定生成 50+ 个变体。
