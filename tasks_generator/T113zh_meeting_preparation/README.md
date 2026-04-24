# T113zh Meeting Preparation Generator

用于批量生成 `T113zh_meeting_preparation` 变体任务。

## 用法

在仓库根目录执行：

```bash
python tasks_generator/T113zh_meeting_preparation/generate.py --output-dir tasks --count 10 --force

python tasks_generator/T113zh_meeting_preparation/generate.py --output-dir tasks_gen/T113zh_meeting_preparation --count 50 --force
```

## 常用参数

- `--count`：生成数量（默认 6）
- `--start-index`：起始编号（默认 1）
- `--seed`：随机种子（默认 20260424）
- `--output-dir`：输出目录（默认 `tasks`）
- `--id-prefix`：任务前缀（默认 `Tgen_T113zh_meeting_preparation_gen`）
- `--force`：覆盖已存在目录

## 输出内容

每个任务包含：

- `task.yaml`
- `grader.py`（standalone）
- `generation_meta.json`
- `fixtures/calendar/events.json`
- `fixtures/contacts/contacts.json`

## 多样性说明（结构性，不是仅改名字）

生成器会在不同 scenario 下变化以下维度：

### 会议数量
- 3 / 4 / 5 / 6 个会议

### 参会人员
- 内部人员：5-8 人（随机生成中文姓名）
- 外部人员：0 / 1 / 2 个（如"陈总"、"王总"、"客户:郑总"等）

### 会议类型
从以下类型中随机选择（不重复）：
- 产品方案评审、客户演示、技术选型讨论、全员周会
- 需求评审会、项目复盘会、预算规划会、跨部门对齐会
- 里程碑评审、风险评估会、架构评审会、上线评审会
- 培训分享会、面试协调会、供应商评估

### 时间分布
- 上午场：9:00-10:30, 10:30-12:00, 11:00-12:00
- 下午场：14:00-15:30, 15:30-17:00, 16:00-17:00, 17:00-18:00

### 地点变化
- 会议室 A/B/C、大会议室、小会议室
- 技术区开放空间
- 线上会议、腾讯会议、飞书会议、Zoom

### 最忙同事
- 自动计算参会次数最多的同事
- 确保有明确的"最忙"人员（参会场次最多）

### Prompt 变化（高多样性组合）

采用**组件化组合**方式生成 prompt，理论组合数 **5000+** 种：

### 开头方式（10 种）
- 「请帮我准备{date}的会议材料：」
- 「{date}有很多会议，请帮我整理会议准备材料：」
- 「我需要为{date}的会议做准备，请协助：」
- 「麻烦帮我准备一下{date}的会议资料：」
- 「你好，请帮我梳理{date}的会议安排：」
- 「助理你好，{date}的会议请帮我准备以下材料：」
- 等等...

### 任务列表格式（8 种）
- **编号列表式**：1. 2. 3. 4. 5.
- **短横线式**：- 列出... - 整理... - 查询...
- **动词开头式**：获取... 提取... 搜索...
- **问句引导式**：明天都有哪些会议？每个会议分别有哪些人参加？
- **场景化描述**：先查一下... 然后把... 再去...
- **简洁指令式**：查日历 → 列会议，整参会者 → 查联系方式
- **详细步骤式**：第一步... 第二步... 第三步...
- **目标导向式**：目标：... 需要确认：... 需要识别：...

### 额外上下文（8 种）
- （无额外上下文）
- 「明天我要出差，今天需要提前了解所有会议信息。」
- 「老板临时要求我汇报明天的会议安排。」
- 「这是本周最重要的一天，会议特别多。」
- 「有几位外部客户要来，需要特别关注。」
- 「团队新人明天入职，请帮我整理会议资料方便 ta 熟悉。」
- 等等...

### 结尾方式（8 种）
- （无结尾）
- 「谢谢！」
- 「请尽快整理好发给我。」
- 「这份材料很重要，请仔细核对。」
- 「整理好后请直接输出，不需要额外解释。」
- 「注意：最忙的同事可能需要我单独协调时间。」
- 等等...

**组合数 = 10 × 8 × 8 × 8 = 5,120 种**，确保大量生成时仍有高多样性。

## 评分维度

- **attendee_coverage (35%)**: 是否完整列出所有参会者并找到其联系方式
- **schedule_analysis (35%)**: 是否正确标注外部人员和最忙同事
- **material_quality (30%)**: 会议材料的结构是否清晰、信息是否完整

## 示例输出

```
Generated 6 variants -> tasks/generated_meeting_preparation_manifest.json
- Tgen_T113zh_meeting_preparation_gen_001_a1b2c3d4: 2026-03-27 | 4 meetings | 6 internal | 1 external | busiest: 李华 (3)
- Tgen_T113zh_meeting_preparation_gen_002_e5f6g7h8: 2026-03-28 | 5 meetings | 7 internal | 0 external | busiest: 王明 (4)
- Tgen_T113zh_meeting_preparation_gen_003_i9j0k1l2: 2026-03-29 | 3 meetings | 5 internal | 2 external | busiest: 张伟 (2)
...
```

## 注意事项

> 注意：`task.yaml` 默认按 benchmark 约定引用 `tasks/<task_id>/fixtures/...`。如果先输出到其他目录，评测前请放回 `tasks/<task_id>/`。
