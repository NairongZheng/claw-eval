# T114 Meeting Preparation Generator (English)

用于批量生成 `T114_meeting_preparation` 英文变体任务。

## 用法

在仓库根目录执行：

```bash
python tasks_generator/T114_meeting_preparation/generate.py --output-dir tasks --count 10 --force

python tasks_generator/T114_meeting_preparation/generate.py --output-dir tasks_gen/T114_meeting_preparation --count 50 --force
```

## 常用参数

- `--count`：生成数量（默认 6）
- `--start-index`：起始编号（默认 1）
- `--seed`：随机种子（默认 20260424）
- `--output-dir`：输出目录（默认 `tasks`）
- `--id-prefix`：任务前缀（默认 `Tgen_T114_meeting_preparation_gen`）
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
- 内部人员：5-8 人（随机生成拼音姓名，如 "Wang Ming", "Li Hua"）
- 外部人员：0 / 1 / 2 个（如 "Director Chen", "Director Wang", "Client:VP Zheng" 等）

### 会议类型
从以下类型中随机选择（不重复）：
- Product Plan Review, Client Demo, Tech Stack Selection, All-Hands Weekly
- Requirements Review, Project Retrospective, Budget Planning, Cross-Dept Alignment
- Milestone Review, Risk Assessment, Architecture Review, Launch Review
- Training Session, Interview Coordination, Vendor Evaluation

### 时间分布
- 上午场：9:00-10:30, 10:30-12:00, 11:00-12:00
- 下午场：14:00-15:30, 15:30-17:00, 16:00-17:00, 17:00-18:00

### 地点变化
- Conference Room A/B/C, Main Conference Room, Small Meeting Room
- Tech Area Open Space
- Online Meeting, Tencent Meeting, Feishu Meeting, Zoom

### 最忙同事
- 自动计算参会次数最多的同事
- 确保有明确的"最忙"人员（参会场次最多）

### Prompt 变化（高多样性组合）

采用**组件化组合**方式生成 prompt，理论组合数 **5000+** 种：

### 开头方式（10 种）
- "Please help me prepare meeting materials for {date_text}:"
- "There are many meetings on {date_text}, please help me organize:"
- "I need to prepare for meetings on {date_text}, please assist:"
- "Hello, please help me review the meeting schedule for {date_text}:"
- 等等...

### 任务列表格式（8 种）
- **Numbered list**: 1. 2. 3. 4. 5.
- **Bullet points**: - List... - Compile... - Look up...
- **Verb-first**: Get... Extract... Search...
- **Question format**: What meetings are scheduled? Who is attending?
- **Scenario description**: First, check... Then list... Next, find...
- **Concise commands**: Check calendar → List meetings, Get attendees → Look up contacts
- **Detailed steps**: Step 1... Step 2... Step 3...
- **Goal-oriented**: Goal:... Need to confirm:... Need to identify:...

### 额外上下文（8 种）
- （无额外上下文）
- "I'm traveling tomorrow and need to understand all meeting information in advance."
- "My boss just asked me to report on tomorrow's meeting schedule."
- "This is the most important day of the week with many meetings."
- "Several external clients are coming, need to pay special attention."
- "A new team member is joining tomorrow, please help me prepare meeting materials."
- 等等...

### 结尾方式（8 种）
- （无结尾）
- "\nThank you!"
- "\nPlease prepare this as soon as possible."
- "\nThis material is important, please verify carefully."
- "\nIf there are external attendees, please flag them so I can prepare in advance."
- 等等...

**组合数 = 10 × 8 × 8 × 8 = 5,120 种**，确保大量生成时仍有高多样性。

## 评分维度

- **attendee_coverage (35%)**: 是否完整列出所有参会者并找到其联系方式
- **schedule_analysis (35%)**: 是否正确标注外部人员和最忙同事
- **material_quality (30%)**: 会议材料的结构是否清晰、信息是否完整

## 示例输出

```
Generated 6 variants -> tasks/generated_meeting_preparation_en_manifest.json
- Tgen_T114_meeting_preparation_gen_001_a1b2c3d4: 2026-03-27 | 4 meetings | 6 internal | 1 external | busiest: Wang Ming (3)
- Tgen_T114_meeting_preparation_gen_002_e5f6g7h8: 2026-03-28 | 5 meetings | 7 internal | 0 external | busiest: Li Hua (4)
- Tgen_T114_meeting_preparation_gen_003_i9j0k1l2: 2026-03-29 | 3 meetings | 5 internal | 2 external | busiest: Zhang Wei (2)
...
```

## 注意事项

> 注意：`task.yaml` 默认按 benchmark 约定引用 `tasks/<task_id>/fixtures/...`。如果先输出到其他目录，评测前请放回 `tasks/<task_id>/`。

## 与 T113zh 的区别

| 维度 | T113zh | T114 |
|------|--------|------|
| 语言 | 中文 | 英文 |
| 姓名 | 中文名（王明、李华） | 拼音名（Wang Ming, Li Hua） |
| 部门 | 产品部、研发部 | Product, R&D |
| 职位 | 技术总监、高级架构师 | Technical Director, Senior Architect |
| 会议标题 | 产品方案评审、客户演示 | Product Plan Review, Client Demo |
| 地点 | 会议室 A、技术区开放空间 | Conference Room A, Tech Area Open Space |
| Prompt 组件 | 中文模板 | 英文模板 |
