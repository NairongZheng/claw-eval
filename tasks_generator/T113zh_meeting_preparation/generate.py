#!/usr/bin/env python3
"""Generate structurally diverse variants for T113zh_meeting_preparation."""

from __future__ import annotations

import argparse
import json
import random
import shutil
import uuid
import textwrap
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

FAMILY_ID = "meeting_preparation_zh"
FAMILY_VERSION = "1.0"
DEFAULT_ID_PREFIX = "Tgen_T113zh_meeting_preparation_gen"
DATE_START = date(2026, 3, 27)
TZ = "+08:00"
WEEKDAY_ZH = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# 人名池
FIRST_NAMES = ["王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴", "徐", "孙", "马", "朱", "胡", "郭", "何", "高", "林", "罗"]
GIVEN_NAMES = ["明", "华", "伟", "芳", "娜", "强", "磊", "军", "洋", "勇", "艳", "杰", "涛", "敏", "静", "丽", "超", "斌", "鹏", "慧"]
EXTERNAL_TITLES = ["陈总", "王总", "李董", "张董", "刘总", "赵总", "外部:周总", "外部:吴总", "客户:郑总", "合作方:孙总"]

# 部门池
DEPARTMENTS = ["产品部", "研发部", "销售部", "市场部", "运营部", "安全部", "运维部", "财务部", "人力部", "法务部"]

# 职位池
TITLES = [
    ("技术总监", "负责整体技术方向和产品规划"),
    ("高级架构师", "主导技术架构设计,微服务和云原生专家"),
    ("客户经理", "负责大客户关系维护和商务谈判"),
    ("安全经理", "负责信息安全和合规审查"),
    ("运维主管", "负责生产环境稳定性和基础设施"),
    ("前端组长", "前端技术栈负责人,React/Vue 专家"),
    ("后端组长", "后端服务负责人,Java/Go 专家"),
    ("测试主管", "负责质量保障和自动化测试"),
    ("产品经理", "负责产品规划和需求管理"),
    ("项目经理", "负责项目交付和进度跟踪"),
    ("数据分析师", "负责数据分析和业务洞察"),
    ("UI 设计师", "负责用户体验和界面设计"),
]

# 会议类型池
MEETING_TYPES = [
    ("产品方案评审", "讨论产品方案,请提前准备相关材料"),
    ("客户演示", "为客户演示新功能,重要客户务必准备充分"),
    ("技术选型讨论", "讨论技术框架选型,请准备候选方案对比"),
    ("全员周会", "本周工作总结与下周计划"),
    ("需求评审会", "评审新需求可行性和排期"),
    ("项目复盘会", "复盘项目经验教训,总结改进点"),
    ("预算规划会", "讨论下季度预算分配"),
    ("跨部门对齐会", "跨部门协作事项对齐"),
    ("里程碑评审", "项目里程碑达成情况评审"),
    ("风险评估会", "识别和讨论项目风险"),
    ("架构评审会", "系统架构设计方案评审"),
    ("上线评审会", "上线前最后评审和确认"),
    ("培训分享会", "内部技术培训和经验分享"),
    ("面试协调会", "讨论候选人面试安排"),
    ("供应商评估", "评估候选供应商方案"),
]

# 会议室池
LOCATIONS = ["会议室 A", "会议室 B", "会议室 C", "大会议室", "小会议室", "技术区开放空间", "线上会议", "腾讯会议", "飞书会议", "Zoom"]

# Prompt 模板组件 - 通过组合生成更多变化
PROMPT_OPENINGS = [
    "请帮我准备{date_text}的会议材料:",
    "{date_text}有很多会议,请帮我整理会议准备材料:",
    "我需要为{date_text}的会议做准备,请协助:",
    "麻烦帮我准备一下{date_text}的会议资料:",
    "你好,请帮我梳理{date_text}的会议安排:",
    "助理你好,{date_text}的会议请帮我准备以下材料:",
    "{date_text}会议较多,请帮我做一份准备清单:",
    "请协助准备{date_text}的会议相关资料:",
    "{date_text}的会议请帮我整理一下:",
    "你好,{date_text}要开好几个会,请帮我准备:",
]

PROMPT_TASKS = [
    # 任务表述方式 1 - 编号列表式
    [
        "1. 查看所有会议的安排",
        "2. 汇总每个会议的参会者清单",
        "3. 在通讯录中查找每位参会者的联系方式和职位",
        "4. 输出一份会议准备材料,包含:每个会议的时间/地点/参会者详情",
        "5. 特别标注外部参会者(不在通讯录中的人)和最忙的同事",
    ],
    # 任务表述方式 2 - 短横线列表式
    [
        "- 列出全部会议的时间、地点和主题",
        "- 整理每场会议的参会人员名单",
        "- 查询内部参会者的职位和联系方式",
        "- 指出哪些是外部人员",
        "- 统计谁参加的会议最多(最忙的人)",
    ],
    # 任务表述方式 3 - 动词开头式
    [
        "获取日历事件列表",
        "提取每场会议的详细信息(时间/地点/参会者)",
        "搜索每位内部参会者的资料",
        "生成会议准备清单",
        "标注外部参会者和参会次数最多的同事",
    ],
    # 任务表述方式 4 - 问句引导式
    [
        "明天都有哪些会议?",
        "每个会议分别有哪些人参加?",
        "内部人员的职位和联系方式是什么?",
        "有没有外部人员参加?",
        "哪位同事明天最忙(参会场次最多)?",
    ],
    # 任务表述方式 5 - 场景化描述
    [
        "先查一下日历上所有会议",
        "然后把每场会议的参会人都列出来",
        "再去通讯录里找这些人的联系方式和职位",
        "最后整理成一份材料,记得标出外部人员和最忙的那位",
    ],
    # 任务表述方式 6 - 简洁指令式
    [
        "查日历 → 列会议",
        "整参会者 → 查联系方式",
        "标外部人员",
        "找最忙同事",
        "输出准备材料",
    ],
    # 任务表述方式 7 - 详细步骤式
    [
        "第一步:读取{date_text}的日历,获取所有会议事件",
        "第二步:逐个查看会议详情,记录时间、地点、主题和参会者",
        "第三步:在通讯录中搜索每位内部参会者,获取其部门、职位、邮箱、电话",
        "第四步:识别外部参会者(通讯录中找不到的人)",
        "第五步:统计每人参会次数,找出最忙的同事",
        "第六步:输出结构化的会议准备材料",
    ],
    # 任务表述方式 8 - 目标导向式
    [
        "目标:为{date_text}的所有会议做好准备",
        "需要确认:每场会议的时间地点、所有参会者信息",
        "需要识别:外部人员(不在内部通讯录)",
        "需要分析:哪位同事参会最多(最忙)",
        "产出:一份完整的会议准备清单",
    ],
]

PROMPT_CLOSINGS = [
    "",
    "\n谢谢!",
    "\n请尽快整理好发给我。",
    "\n这份材料很重要,请仔细核对。",
    "\n整理好后请直接输出,不需要额外解释。",
    "\n如有外部人员请特别标注,方便我提前准备接待。",
    "\n注意:最忙的同事可能需要我单独协调时间。",
    "\n请确保信息准确完整,我会在会议上用到。",
]

# 额外上下文场景(可选添加)
EXTRA_CONTEXTS = [
    "",
    "明天我要出差,今天需要提前了解所有会议信息。",
    "老板临时要求我汇报明天的会议安排。",
    "这是本周最重要的一天,会议特别多。",
    "有几位外部客户要来,需要特别关注。",
    "我需要提前准备会议室和设备,请帮我梳理清楚。",
    "团队新人明天入职,请帮我整理会议资料方便 ta 熟悉。",
    "明天下午我有事可能早退,需要先了解会议安排。",
]


def generate_name(rng: random.Random) -> str:
    """生成随机中文姓名。"""
    return rng.choice(FIRST_NAMES) + rng.choice(GIVEN_NAMES)


def slug_from_name(name: str) -> str:
    """从姓名生成 slug。"""
    # 简单处理:移除"外部:"和"客户:"前缀
    clean_name = name.replace("外部:", "").replace("客户:", "").replace("合作方:", "")
    return clean_name.lower().replace(" ", "")


def dt_iso(target: date, h: int, m: int) -> str:
    return f"{target.isoformat()}T{h:02d}:{m:02d}:00{TZ}"


def hm(h: int, m: int) -> str:
    return f"{h:02d}:{m:02d}"


def build_task_id(id_prefix: str, task_index: int) -> str:
    short_hash = uuid.uuid4().hex[:8]
    return f"{id_prefix}_{task_index:03d}_{short_hash}"


def generate_contacts(rng: random.Random, internal_names: list[str]) -> list[dict[str, Any]]:
    """生成通讯录数据。"""
    contacts = []
    used_titles = set()

    for i, name in enumerate(internal_names):
        # 避免重复职位
        available_titles = [t for t in TITLES if t[0] not in used_titles]
        if not available_titles:
            available_titles = TITLES
        title, notes = rng.choice(available_titles)
        used_titles.add(title)

        contacts.append({
            "contact_id": f"CT-{300 + i:03d}",
            "name": name,
            "department": rng.choice(DEPARTMENTS),
            "title": title,
            "email": f"{slug_from_name(name)}@company.com",
            "phone": f"1380030{i:02d}{rng.randint(0, 9):d}",
            "location": rng.choice(["上海总部", "北京分部", "深圳分部", "广州分部"]),
            "notes": notes,
        })
    return contacts


def generate_meetings(rng: random.Random, target_date: date, internal_names: list[str], external_names: list[str], num_meetings: int) -> list[dict[str, Any]]:
    """生成会议数据。"""
    meetings = []

    # 为每个内部人员分配参会次数,确保有一个人最忙
    attendance_count = {name: 0 for name in internal_names}

    # 选择会议类型(不重复)
    available_types = random.sample(MEETING_TYPES, min(num_meetings, len(MEETING_TYPES)))

    # 生成时间段(避免重叠)
    time_slots = [
        (9, 0, 10, 30),   # 上午第一场
        (10, 30, 12, 0),  # 上午第二场
        (11, 0, 12, 0),   # 上午短会
        (14, 0, 15, 30),  # 下午第一场
        (15, 30, 17, 0),  # 下午第二场
        (16, 0, 17, 0),   # 下午短会
        (17, 0, 18, 0),   # 傍晚
    ]
    used_slots = []

    for i in range(num_meetings):
        meeting_type, description = available_types[i % len(available_types)]

        # 选择时间段
        available_slots = [s for s in time_slots if s not in used_slots]
        if not available_slots:
            available_slots = time_slots
        sh, sm, eh, em = rng.choice(available_slots)
        used_slots.append((sh, sm, eh, em))

        # 选择参会者(至少 2 人,最多 6 人)
        num_internal = rng.randint(2, min(5, len(internal_names)))
        attendees = rng.sample(internal_names, num_internal)

        # 更新参会计数
        for name in attendees:
            attendance_count[name] += 1

        # 可能添加外部人员
        if external_names and rng.random() < 0.6:
            ext = rng.choice(external_names)
            if ext not in attendees:
                attendees.append(ext)

        # 选择地点
        location = rng.choice(LOCATIONS)

        # 选择组织者(从参会者中选)
        organizer = rng.choice([a for a in attendees if not a.startswith("外部:") and not a.startswith("客户:") and not a.startswith("合作方:")])

        meetings.append({
            "event_id": f"evt_{500 + i:03d}",
            "title": meeting_type,
            "start_time": dt_iso(target_date, sh, sm),
            "end_time": dt_iso(target_date, eh, em),
            "location": location,
            "organizer": organizer,
            "attendees": attendees,
            "description": description,
            "status": "confirmed",
        })

    return meetings, attendance_count


def build_scenario(rng: random.Random, target_date: date) -> dict[str, Any]:
    """生成场景配置。"""
    # 决定会议数量(3-6 个)
    num_meetings = rng.randint(3, 6)

    # 决定内部人员数量(5-8 人)
    num_internal = rng.randint(5, 8)

    # 决定外部人员数量(0-2 个)
    num_external = rng.randint(0, 2)

    # 生成人员
    internal_names = []
    while len(internal_names) < num_internal:
        name = generate_name(rng)
        if name not in internal_names:
            internal_names.append(name)

    external_names = rng.sample(EXTERNAL_TITLES, num_external) if num_external > 0 else []

    # 生成会议
    meetings, attendance_count = generate_meetings(rng, target_date, internal_names, external_names, num_meetings)

    # 找出最忙的人
    busiest_person = max(attendance_count.keys(), key=lambda x: attendance_count[x])
    busiest_count = attendance_count[busiest_person]

    return {
        "num_meetings": num_meetings,
        "num_internal": num_internal,
        "num_external": num_external,
        "internal_names": internal_names,
        "external_names": external_names,
        "meetings": meetings,
        "attendance_count": attendance_count,
        "busiest_person": busiest_person,
        "busiest_count": busiest_count,
    }


def build_contacts_fixture(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    """生成通讯录 fixture。"""
    return generate_contacts(random.Random(hash(str(scenario["internal_names"]))), scenario["internal_names"])


def build_calendar_fixture(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    """生成日历 fixture。"""
    return scenario["meetings"]


def build_prompt(scenario: dict[str, Any], target_date: date, rng: random.Random) -> str:
    """生成 prompt - 通过组合多个组件产生高多样性。"""
    date_text = f"{target_date.year}年{target_date.month}月{target_date.day}日（{WEEKDAY_ZH[target_date.weekday()]}）"
    
    # 随机选择各组件
    opening = rng.choice(PROMPT_OPENINGS).format(date_text=date_text)
    tasks_list = rng.choice(PROMPT_TASKS)
    closing = rng.choice(PROMPT_CLOSINGS)
    extra_context = rng.choice(EXTRA_CONTEXTS)
    
    # 处理任务列表的格式
    if isinstance(tasks_list[0], str):
        # 已经是字符串列表
        tasks_text = "\n".join(tasks_list)
    else:
        # 需要进一步处理
        tasks_text = "\n".join(tasks_list)
    
    # 组合 prompt
    parts = [opening, tasks_text]
    if extra_context:
        parts.insert(1, extra_context)  # 上下文放在开头和任务之间
    if closing:
        parts.append(closing)
    
    return "\n".join(parts)


def build_task_yaml(task_id: str, target_date: date, scenario: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    """生成 task.yaml。"""
    service_base = f"tasks/{task_id}/fixtures"

    # 构建预期信息用于评分
    external_names = scenario["external_names"]
    busiest_person = scenario["busiest_person"]
    busiest_count = scenario["busiest_count"]

    context_keywords = [busiest_person, str(busiest_count)] + external_names

    reference_solution = textwrap.dedent(
        f"""\
        1. calendar_list_events(start_date="{target_date.isoformat()}") → 获取{scenario["num_meetings"]}个会议
        2. 逐个查看会议详情和参会者
        3. contacts_search 查找{scenario["num_internal"]}位内部人员
        4. 外部人员{external_names if external_names else "无"}搜索无结果 → 标注为外部人员
        5. 统计每人参会次数:{busiest_person}最多 ({busiest_count}场)
        6. 输出结构化会议准备材料
        """
    ).strip()

    return {
        "task_id": task_id,
        "task_name": "Meeting Preparation Materials (ZH)",
        "version": FAMILY_VERSION,
        "category": "workflow",
        "difficulty": "medium",
        "tags": ["general", "generated", FAMILY_ID, "structural-diversity"],
        "services": [
            {
                "name": "calendar",
                "command": "python mock_services/calendar/server.py",
                "port": 9101,
                "health_check": "http://localhost:9101/calendar/events",
                "health_check_method": "POST",
                "ready_timeout": 10,
                "reset_endpoint": "http://localhost:9101/calendar/reset",
                "env": {"CALENDAR_FIXTURES": f"{service_base}/calendar/events.json"},
            },
            {
                "name": "contacts",
                "command": "python mock_services/contacts/server.py",
                "port": 9103,
                "health_check": "http://localhost:9103/contacts/search",
                "health_check_method": "POST",
                "ready_timeout": 10,
                "reset_endpoint": "http://localhost:9103/contacts/reset",
                "env": {"CONTACTS_FIXTURES": f"{service_base}/contacts/contacts.json"},
            },
        ],
        "prompt": {"text": build_prompt(scenario, target_date, rng), "language": "zh"},
        "tools": [
            {
                "name": "calendar_list_events",
                "description": "查看日历事件",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "起始日期 (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "截止日期 (YYYY-MM-DD)"},
                    },
                    "required": [],
                },
            },
            {
                "name": "calendar_get_event",
                "description": "获取事件详情",
                "input_schema": {
                    "type": "object",
                    "properties": {"event_id": {"type": "string", "description": "事件 ID"}},
                    "required": ["event_id"],
                },
            },
            {
                "name": "contacts_search",
                "description": "搜索内部通讯录",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索关键词"},
                        "department": {"type": "string", "description": "按部门筛选"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "contacts_get",
                "description": "获取联系人详情",
                "input_schema": {
                    "type": "object",
                    "properties": {"contact_id": {"type": "string", "description": "联系人 ID"}},
                    "required": ["contact_id"],
                },
            },
        ],
        "tool_endpoints": [
            {"tool_name": "calendar_list_events", "url": "http://localhost:9101/calendar/events", "method": "POST"},
            {"tool_name": "calendar_get_event", "url": "http://localhost:9101/calendar/events/get", "method": "POST"},
            {"tool_name": "contacts_search", "url": "http://localhost:9103/contacts/search", "method": "POST"},
            {"tool_name": "contacts_get", "url": "http://localhost:9103/contacts/get", "method": "POST"},
        ],
        "sandbox_files": ["fixtures/calendar/events.json", "fixtures/contacts/contacts.json"],
        "environment": {"timeout_seconds": 300, "max_turns": 20},
        "scoring_components": [
            {
                "name": "attendee_coverage",
                "weight": 0.35,
                "check": {"type": "llm_judge", "description": "是否完整列出所有参会者并找到其联系方式"},
            },
            {
                "name": "schedule_analysis",
                "weight": 0.35,
                "check": {"type": "llm_judge", "description": f"是否正确标注外部人员 ({external_names if external_names else '无'}) 和最忙同事 ({busiest_person} 共{busiest_count}场)"},
            },
            {
                "name": "material_quality",
                "weight": 0.30,
                "check": {"type": "llm_judge", "description": "会议材料的结构是否清晰、信息是否完整"},
            },
        ],
        "safety_checks": [],
        "expected_actions": [],
        "judge_rubric": f"""评估助手的会议准备材料质量。

## 正确信息
1. 明天{scenario["num_meetings"]}个会议
2. 参会者:{scenario["num_internal"]}个内部人员 + {scenario["num_external"]}个外部人员
3. 最忙同事:{busiest_person}({busiest_count}场会议)
4. 外部人员:{external_names if external_names else "无"}

评分:
- 0.8-1.0: 覆盖全部会议和参会者,正确标注外部人员和最忙同事
- 0.5-0.7: 大部分会议覆盖,遗漏部分细节
- 0.2-0.4: 仅列出部分会议
- 0.0-0.1: 未完成会议材料
""",
        "reference_solution": reference_solution,
        "primary_dimensions": ["completion", "robustness", "communication"],
    }


def render_grader(task_id: str, target_date: date, scenario: dict[str, Any]) -> str:
    """生成 grader.py。"""
    external_names = json.dumps(scenario["external_names"], ensure_ascii=False)
    busiest_person = scenario["busiest_person"]
    busiest_count = scenario["busiest_count"]
    num_meetings = scenario["num_meetings"]

    return f'''\
"""Standalone grader for {task_id}."""

from __future__ import annotations

import json
import logging
from typing import Any

from claw_eval.graders.base import AbstractGrader
from claw_eval.models.task import TaskDefinition
from claw_eval.models.trace import DimensionScores, MediaLoad, ToolDispatch, TraceMessage

log = logging.getLogger(__name__)


class GeneratedMeetingPreparationGraderZh(AbstractGrader):
    EXTERNAL_NAMES = {external_names}
    BUSIEST_PERSON = "{busiest_person}"
    BUSIEST_COUNT = {busiest_count}
    NUM_MEETINGS = {num_meetings}

    def grade(
        self,
        messages: list[TraceMessage],
        dispatches: list[ToolDispatch],
        task: TaskDefinition,
        audit_data: dict[str, dict] | None = None,
        judge: Any | None = None,
        media_events: list[MediaLoad] | None = None,
        env_snapshot: dict | None = None,
    ) -> DimensionScores:
        scores = DimensionScores()

        completion = 0.0

        # 检查是否调用了 calendar_list_events
        calendar_calls = [d for d in dispatches if d.tool_name == "calendar_list_events" and d.response_status < 400]
        if calendar_calls:
            completion += 0.15

        # 检查是否获取了会议详情
        get_event_calls = [d for d in dispatches if d.tool_name == "calendar_get_event" and d.response_status < 400]
        if len(get_event_calls) >= self.NUM_MEETINGS:
            completion += 0.20
        elif get_event_calls:
            completion += 0.10

        # 检查是否搜索了联系人
        search_calls = [d for d in dispatches if d.tool_name == "contacts_search" and d.response_status < 400]
        if len(search_calls) >= 3:
            completion += 0.20
        elif search_calls:
            completion += 0.10

        # 检查输出质量(通过 LLM judge 或关键词)
        assistant_text = self._get_all_assistant_text(messages)

        # 检查是否提到最忙的人
        if self.BUSIEST_PERSON in assistant_text:
            completion += 0.15
            # 检查是否提到参会次数
            if str(self.BUSIEST_COUNT) in assistant_text or "最忙" in assistant_text or "最多" in assistant_text:
                completion += 0.10

        # 检查是否标注了外部人员
        external_found = any(ext in assistant_text for ext in self.EXTERNAL_NAMES)
        if self.EXTERNAL_NAMES:
            if external_found and ("外部" in assistant_text or "不在通讯录" in assistant_text):
                completion += 0.20
            elif external_found:
                completion += 0.10
        else:
            # 没有外部人员的情况下,不扣分
            completion += 0.20

        scores.completion = min(completion, 1.0)
        scores.robustness = self.compute_robustness(dispatches)
        scores.efficiency_turns = len([m for m in messages if m.message.role == "assistant"])
        return scores
'''


def build_generation_meta(task_id: str, seed: int, target_date: date, scenario: dict[str, Any]) -> dict[str, Any]:
    """生成 generation_meta.json。"""
    return {
        "family_id": FAMILY_ID,
        "family_version": FAMILY_VERSION,
        "task_id": task_id,
        "seed": seed,
        "target_date": target_date.isoformat(),
        "scenario_summary": {
            "num_meetings": scenario["num_meetings"],
            "num_internal": scenario["num_internal"],
            "num_external": scenario["num_external"],
            "busiest_person": scenario["busiest_person"],
            "busiest_count": scenario["busiest_count"],
        },
    }


def build_variant(task_root: Path, index: int, seed: int, force: bool, id_prefix: str) -> dict[str, Any]:
    """构建单个 variant。"""
    rng = random.Random(seed)
    task_id = build_task_id(id_prefix, index)
    task_dir = task_root / task_id

    target_date = DATE_START + timedelta(days=index - 1)
    scenario = build_scenario(rng, target_date)

    if task_dir.exists():
        if not force:
            raise FileExistsError(f"{task_dir} already exists; rerun with --force")
        shutil.rmtree(task_dir)

    # 创建目录结构
    (task_dir / "fixtures" / "calendar").mkdir(parents=True, exist_ok=True)
    (task_dir / "fixtures" / "contacts").mkdir(parents=True, exist_ok=True)

    # 写入 fixtures
    contacts_data = build_contacts_fixture(scenario)
    (task_dir / "fixtures" / "contacts" / "contacts.json").write_text(
        json.dumps(contacts_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    meetings_data = build_calendar_fixture(scenario)
    (task_dir / "fixtures" / "calendar" / "events.json").write_text(
        json.dumps(meetings_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # 写入 task.yaml
    (task_dir / "task.yaml").write_text(
        yaml.safe_dump(build_task_yaml(task_id, target_date, scenario, rng), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    # 写入 grader.py
    (task_dir / "grader.py").write_text(render_grader(task_id, target_date, scenario), encoding="utf-8")

    # 写入 generation_meta.json
    (task_dir / "generation_meta.json").write_text(
        json.dumps(build_generation_meta(task_id, seed, target_date, scenario), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "task_id": task_id,
        "target_date": target_date.isoformat(),
        "num_meetings": scenario["num_meetings"],
        "num_internal": scenario["num_internal"],
        "num_external": scenario["num_external"],
        "busiest_person": scenario["busiest_person"],
        "busiest_count": scenario["busiest_count"],
        "task_dir": str(task_dir),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate T113zh meeting preparation variants")
    parser.add_argument("--count", type=int, default=6, help="Number of variants to generate")
    parser.add_argument("--start-index", type=int, default=1, help="Starting index")
    parser.add_argument("--seed", type=int, default=20260424, help="Random seed")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: tasks)")
    parser.add_argument("--tasks-root", default=None, help="Deprecated alias of --output-dir")
    parser.add_argument("--id-prefix", default=DEFAULT_ID_PREFIX, help="Task ID prefix")
    parser.add_argument("--force", action="store_true", help="Overwrite existing directories")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir or args.tasks_root or "tasks"
    task_root = Path(output_dir).resolve()
    task_root.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, Any]] = []
    for offset in range(args.count):
        idx = args.start_index + offset
        manifest.append(build_variant(task_root, idx, args.seed + idx, args.force, args.id_prefix))

    manifest_path = task_root / "generated_meeting_preparation_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Generated {len(manifest)} variants -> {manifest_path}")
    for item in manifest:
        print(
            f"- {item['task_id']}: {item['target_date']} | "
            f"{item['num_meetings']} meetings | "
            f"{item['num_internal']} internal | "
            f"{item['num_external']} external | "
            f"busiest: {item['busiest_person']}({item['busiest_count']})"
        )


if __name__ == "__main__":
    main()
