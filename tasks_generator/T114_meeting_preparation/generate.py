#!/usr/bin/env python3
"""Generate structurally diverse variants for T114_meeting_preparation (English)."""

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

FAMILY_ID = "meeting_preparation_en"
FAMILY_VERSION = "1.0"
DEFAULT_ID_PREFIX = "Tgen_T114_meeting_preparation_gen"
DATE_START = date(2026, 3, 27)
TZ = "+08:00"
WEEKDAY_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Name pools
FIRST_NAMES_CN = ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Zhao", "Huang", "Zhou", "Wu", "Xu", "Sun", "Ma", "Zhu", "Hu", "Guo", "He", "Gao", "Lin", "Luo"]
GIVEN_NAMES_CN = ["Ming", "Hua", "Wei", "Fang", "Na", "Qiang", "Lei", "Jun", "Yang", "Yong", "Yan", "Jie", "Tao", "Min", "Jing", "Li", "Chao", "Bin", "Peng", "Hui"]

EXTERNAL_TITLES = ["Director Chen", "Director Wang", "Director Li", "Director Zhang", "VP Liu", "VP Zhao", "External:VP Zhou", "External:VP Wu", "Client:VP Zheng", "Partner:VP Sun"]

# Department pool
DEPARTMENTS = ["Product", "R&D", "Sales", "Marketing", "Operations", "Security", "DevOps", "Finance", "HR", "Legal"]

# Title pool
TITLES = [
    ("Technical Director", "Responsible for overall technical direction and product planning"),
    ("Senior Architect", "Leads technical architecture design, microservices and cloud-native expert"),
    ("Account Manager", "Responsible for key account relationship management and business negotiations"),
    ("Security Manager", "Responsible for information security and compliance review"),
    ("DevOps Lead", "Responsible for production environment stability and infrastructure"),
    ("Frontend Lead", "Frontend tech stack owner, React/Vue expert"),
    ("Backend Lead", "Backend services owner, Java/Go expert"),
    ("QA Lead", "Responsible for quality assurance and automated testing"),
    ("Product Manager", "Responsible for product planning and requirements management"),
    ("Project Manager", "Responsible for project delivery and schedule tracking"),
    ("Data Analyst", "Responsible for data analysis and business insights"),
    ("UX Designer", "Responsible for user experience and interface design"),
]

# Meeting type pool
MEETING_TYPES = [
    ("Product Plan Review", "Discuss Q2 product plan, please prepare relevant materials in advance"),
    ("Client Demo", "Demo new features for client, important client — be well prepared"),
    ("Tech Stack Selection", "Discuss microservice framework selection, candidates: Spring Cloud / Dubbo"),
    ("All-Hands Weekly", "This week's work summary and next week's plan"),
    ("Requirements Review", "Review new requirements feasibility and timeline"),
    ("Project Retrospective", "Review project lessons learned and improvement points"),
    ("Budget Planning", "Discuss next quarter budget allocation"),
    ("Cross-Dept Alignment", "Cross-departmental collaboration alignment"),
    ("Milestone Review", "Project milestone achievement review"),
    ("Risk Assessment", "Identify and discuss project risks"),
    ("Architecture Review", "System architecture design review"),
    ("Launch Review", "Pre-launch final review and confirmation"),
    ("Training Session", "Internal technical training and knowledge sharing"),
    ("Interview Coordination", "Discuss candidate interview arrangements"),
    ("Vendor Evaluation", "Evaluate vendor proposals"),
]

# Location pool
LOCATIONS = ["Conference Room A", "Conference Room B", "Conference Room C", "Main Conference Room", "Small Meeting Room", "Tech Area Open Space", "Online Meeting", "Tencent Meeting", "Feishu Meeting", "Zoom"]

# Prompt template components
PROMPT_OPENINGS = [
    "Please help me prepare meeting materials for {date_text}:",
    "There are many meetings on {date_text}, please help me organize the preparation materials:",
    "I need to prepare for meetings on {date_text}, please assist:",
    "Please help me prepare the meeting materials for {date_text}:",
    "Hello, please help me review the meeting schedule for {date_text}:",
    "Hi assistant, please prepare the following materials for {date_text} meetings:",
    "There are several meetings on {date_text}, please help me prepare a checklist:",
    "Please assist in preparing meeting-related materials for {date_text}:",
    "Please help me organize the meetings for {date_text}:",
    "Hello, I have multiple meetings on {date_text}, please help me prepare:",
]

PROMPT_TASKS = [
    # Format 1 - Numbered list
    [
        "1. Check all meetings scheduled for tomorrow",
        "2. Compile a list of attendees for each meeting",
        "3. Look up each attendee's contact information and job title in the contacts directory",
        "4. Produce a meeting preparation document that includes: time/location/attendee details for each meeting",
        "5. Specifically flag external attendees (people not in the contacts directory) and the busiest colleague",
    ],
    # Format 2 - Bullet points
    [
        "- List all meeting times, locations, and topics",
        "- Compile attendee lists for each meeting",
        "- Look up internal attendees' titles and contact information",
        "- Identify which are external personnel",
        "- Count who attends the most meetings (the busiest person)",
    ],
    # Format 3 - Verb-first
    [
        "Get the calendar events list",
        "Extract detailed information for each meeting (time/location/attendees)",
        "Search for each internal attendee's information",
        "Generate a meeting preparation checklist",
        "Flag external attendees and the colleague with the most meetings",
    ],
    # Format 4 - Question format
    [
        "What meetings are scheduled for tomorrow?",
        "Who is attending each meeting?",
        "What are the titles and contact details of internal personnel?",
        "Are there any external attendees?",
        "Which colleague is the busiest (attending the most meetings)?",
    ],
    # Format 5 - Scenario description
    [
        "First, check the calendar for all meetings",
        "Then list the attendees for each meeting",
        "Next, find their contact information and titles in the directory",
        "Finally, compile a preparation document, remembering to flag external personnel and the busiest person",
    ],
    # Format 6 - Concise commands
    [
        "Check calendar → List meetings",
        "Get attendees → Look up contacts",
        "Flag external personnel",
        "Find busiest colleague",
        "Output preparation materials",
    ],
    # Format 7 - Detailed steps
    [
        "Step 1: Read the calendar for {date_text} and get all meeting events",
        "Step 2: Review each meeting's details, recording time, location, topic, and attendees",
        "Step 3: Search the contacts directory for each internal attendee to get their department, title, email, and phone",
        "Step 4: Identify external attendees (people not found in the contacts directory)",
        "Step 5: Count meetings per person and find the busiest colleague",
        "Step 6: Output structured meeting preparation materials",
    ],
    # Format 8 - Goal-oriented
    [
        "Goal: Be fully prepared for all meetings on {date_text}",
        "Need to confirm: Time and location for each meeting, all attendee information",
        "Need to identify: External personnel (not in internal contacts directory)",
        "Need to analyze: Which colleague attends the most meetings (the busiest)",
        "Deliverable: A complete meeting preparation checklist",
    ],
]

PROMPT_CLOSINGS = [
    "",
    "\nThank you!",
    "\nPlease prepare this as soon as possible.",
    "\nThis material is important, please verify carefully.",
    "\nOnce ready, please output directly without additional explanation.",
    "\nIf there are external attendees, please flag them so I can prepare in advance.",
    "\nNote: The busiest colleague may need me to coordinate their schedule separately.",
    "\nPlease ensure the information is accurate and complete, I will use it in the meetings.",
]

# Extra context scenarios (optional)
EXTRA_CONTEXTS = [
    "",
    "I'm traveling tomorrow and need to understand all meeting information in advance.",
    "My boss just asked me to report on tomorrow's meeting schedule.",
    "This is the most important day of the week with many meetings.",
    "Several external clients are coming, need to pay special attention.",
    "I need to prepare meeting rooms and equipment in advance, please help me clarify everything.",
    "A new team member is joining tomorrow, please help me prepare meeting materials to help them get oriented.",
    "I may need to leave early tomorrow afternoon, please help me understand the meeting schedule first.",
]


def generate_name(rng: random.Random) -> str:
    """Generate random English name (Chinese pinyin format)."""
    return rng.choice(FIRST_NAMES_CN) + " " + rng.choice(GIVEN_NAMES_CN)


def slug_from_name(name: str) -> str:
    """Generate slug from name."""
    clean_name = name.replace("External:", "").replace("Client:", "").replace("Partner:", "")
    return clean_name.lower().replace(" ", "")


def dt_iso(target: date, h: int, m: int) -> str:
    return f"{target.isoformat()}T{h:02d}:{m:02d}:00{TZ}"


def hm(h: int, m: int) -> str:
    return f"{h:02d}:{m:02d}"


def build_task_id(id_prefix: str, task_index: int) -> str:
    short_hash = uuid.uuid4().hex[:8]
    return f"{id_prefix}_{task_index:03d}_{short_hash}"


def generate_contacts(rng: random.Random, internal_names: list[str]) -> list[dict[str, Any]]:
    """Generate contacts data."""
    contacts = []
    used_titles = set()

    for i, name in enumerate(internal_names):
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
            "location": rng.choice(["Shanghai HQ", "Beijing Branch", "Shenzhen Branch", "Guangzhou Branch"]),
            "notes": notes,
        })
    return contacts


def generate_meetings(rng: random.Random, target_date: date, internal_names: list[str], external_names: list[str], num_meetings: int) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Generate meeting data."""
    meetings = []
    attendance_count = {name: 0 for name in internal_names}

    available_types = random.sample(MEETING_TYPES, min(num_meetings, len(MEETING_TYPES)))

    time_slots = [
        (9, 0, 10, 30),
        (10, 30, 12, 0),
        (11, 0, 12, 0),
        (14, 0, 15, 30),
        (15, 30, 17, 0),
        (16, 0, 17, 0),
        (17, 0, 18, 0),
    ]
    used_slots = []

    for i in range(num_meetings):
        meeting_type, description = available_types[i % len(available_types)]

        available_slots = [s for s in time_slots if s not in used_slots]
        if not available_slots:
            available_slots = time_slots
        sh, sm, eh, em = rng.choice(available_slots)
        used_slots.append((sh, sm, eh, em))

        num_internal = rng.randint(2, min(5, len(internal_names)))
        attendees = rng.sample(internal_names, num_internal)

        for name in attendees:
            attendance_count[name] += 1

        if external_names and rng.random() < 0.6:
            ext = rng.choice(external_names)
            if ext not in attendees:
                attendees.append(ext)

        location = rng.choice(LOCATIONS)

        organizer = rng.choice([a for a in attendees if not a.startswith("External:") and not a.startswith("Client:") and not a.startswith("Partner:")])

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
    """Build scenario configuration."""
    num_meetings = rng.randint(3, 6)
    num_internal = rng.randint(5, 8)
    num_external = rng.randint(0, 2)

    internal_names = []
    while len(internal_names) < num_internal:
        name = generate_name(rng)
        if name not in internal_names:
            internal_names.append(name)

    external_names = rng.sample(EXTERNAL_TITLES, num_external) if num_external > 0 else []

    meetings, attendance_count = generate_meetings(rng, target_date, internal_names, external_names, num_meetings)

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
    """Generate contacts fixture."""
    return generate_contacts(random.Random(hash(str(scenario["internal_names"]))), scenario["internal_names"])


def build_calendar_fixture(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate calendar fixture."""
    return scenario["meetings"]


def build_prompt(scenario: dict[str, Any], target_date: date, rng: random.Random) -> str:
    """Generate prompt with high diversity through component combination."""
    date_text = f"{WEEKDAY_EN[target_date.weekday()]}, {target_date.year}-{target_date.month:02d}-{target_date.day:02d}"
    
    opening = rng.choice(PROMPT_OPENINGS).format(date_text=date_text)
    tasks_list = rng.choice(PROMPT_TASKS)
    closing = rng.choice(PROMPT_CLOSINGS)
    extra_context = rng.choice(EXTRA_CONTEXTS)
    
    tasks_text = "\n".join(tasks_list)
    
    parts = [opening, tasks_text]
    if extra_context:
        parts.insert(1, extra_context)
    if closing:
        parts.append(closing)
    
    return "\n".join(parts)


def build_task_yaml(task_id: str, target_date: date, scenario: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    """Generate task.yaml."""
    service_base = f"tasks/{task_id}/fixtures"

    external_names = scenario["external_names"]
    busiest_person = scenario["busiest_person"]
    busiest_count = scenario["busiest_count"]

    reference_solution = textwrap.dedent(
        f"""\
        1. calendar_list_events(start_date="{target_date.isoformat()}") → Get {scenario["num_meetings"]} meetings
        2. Review each meeting's details and attendees one by one
        3. contacts_search to look up {scenario["num_internal"]} internal personnel
        4. External personnel {external_names if external_names else "none"} search returns no results → flag as external
        5. Count meetings per person: {busiest_person} has the most ({busiest_count} meetings)
        6. Output structured meeting preparation materials
        """
    ).strip()

    return {
        "task_id": task_id,
        "task_name": "Meeting Preparation Materials",
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
        "prompt": {"text": build_prompt(scenario, target_date, rng), "language": "en"},
        "tools": [
            {
                "name": "calendar_list_events",
                "description": "List calendar events",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                    },
                    "required": [],
                },
            },
            {
                "name": "calendar_get_event",
                "description": "Get event details",
                "input_schema": {
                    "type": "object",
                    "properties": {"event_id": {"type": "string", "description": "Event ID"}},
                    "required": ["event_id"],
                },
            },
            {
                "name": "contacts_search",
                "description": "Search internal contacts directory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search keyword"},
                        "department": {"type": "string", "description": "Filter by department"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "contacts_get",
                "description": "Get contact details",
                "input_schema": {
                    "type": "object",
                    "properties": {"contact_id": {"type": "string", "description": "Contact ID"}},
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
                "check": {"type": "llm_judge", "description": "Whether all attendees are fully listed with their contact information found"},
            },
            {
                "name": "schedule_analysis",
                "weight": 0.35,
                "check": {"type": "llm_judge", "description": f"Whether external personnel ({external_names if external_names else 'none'}) and the busiest colleague ({busiest_person} with {busiest_count} meetings) are correctly flagged"},
            },
            {
                "name": "material_quality",
                "weight": 0.30,
                "check": {"type": "llm_judge", "description": "Whether the meeting materials are clearly structured and information is complete"},
            },
        ],
        "safety_checks": [],
        "expected_actions": [],
        "judge_rubric": f"""Evaluate the quality of the assistant's meeting preparation materials.

## Correct Information
1. Tomorrow has {scenario["num_meetings"]} meetings
2. Attendees: {scenario["num_internal"]} internal personnel + {scenario["num_external"]} external personnel
3. Busiest colleague: {busiest_person} ({busiest_count} meetings)
4. External personnel: {external_names if external_names else "none"}

Scoring:
- 0.8-1.0: Covers all meetings and attendees, correctly flags external personnel and busiest colleague
- 0.5-0.7: Most meetings covered, some details missing
- 0.2-0.4: Only lists some meetings
- 0.0-0.1: Meeting materials not completed
""",
        "reference_solution": reference_solution,
        "primary_dimensions": ["completion", "robustness", "communication"],
    }


def render_grader(task_id: str, target_date: date, scenario: dict[str, Any]) -> str:
    """Generate grader.py."""
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


class GeneratedMeetingPreparationGraderEn(AbstractGrader):
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

        # Check if calendar_list_events was called
        calendar_calls = [d for d in dispatches if d.tool_name == "calendar_list_events" and d.response_status < 400]
        if calendar_calls:
            completion += 0.15

        # Check if meeting details were retrieved
        get_event_calls = [d for d in dispatches if d.tool_name == "calendar_get_event" and d.response_status < 400]
        if len(get_event_calls) >= self.NUM_MEETINGS:
            completion += 0.20
        elif get_event_calls:
            completion += 0.10

        # Check if contacts were searched
        search_calls = [d for d in dispatches if d.tool_name == "contacts_search" and d.response_status < 400]
        if len(search_calls) >= 3:
            completion += 0.20
        elif search_calls:
            completion += 0.10

        # Check output quality (via LLM judge or keywords)
        assistant_text = self._get_all_assistant_text(messages)

        # Check if busiest person is mentioned
        if self.BUSIEST_PERSON in assistant_text:
            completion += 0.15
            if str(self.BUSIEST_COUNT) in assistant_text or "busiest" in assistant_text.lower() or "most" in assistant_text.lower():
                completion += 0.10

        # Check if external personnel are flagged
        external_found = any(ext in assistant_text for ext in self.EXTERNAL_NAMES)
        if self.EXTERNAL_NAMES:
            if external_found and ("external" in assistant_text.lower() or "not in contacts" in assistant_text.lower()):
                completion += 0.20
            elif external_found:
                completion += 0.10
        else:
            completion += 0.20

        scores.completion = min(completion, 1.0)
        scores.robustness = self.compute_robustness(dispatches)
        scores.efficiency_turns = len([m for m in messages if m.message.role == "assistant"])
        return scores
'''


def build_generation_meta(task_id: str, seed: int, target_date: date, scenario: dict[str, Any]) -> dict[str, Any]:
    """Generate generation_meta.json."""
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
    """Build a single variant."""
    rng = random.Random(seed)
    task_id = build_task_id(id_prefix, index)
    task_dir = task_root / task_id

    target_date = DATE_START + timedelta(days=index - 1)
    scenario = build_scenario(rng, target_date)

    if task_dir.exists():
        if not force:
            raise FileExistsError(f"{task_dir} already exists; rerun with --force")
        shutil.rmtree(task_dir)

    (task_dir / "fixtures" / "calendar").mkdir(parents=True, exist_ok=True)
    (task_dir / "fixtures" / "contacts").mkdir(parents=True, exist_ok=True)

    contacts_data = build_contacts_fixture(scenario)
    (task_dir / "fixtures" / "contacts" / "contacts.json").write_text(
        json.dumps(contacts_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    meetings_data = build_calendar_fixture(scenario)
    (task_dir / "fixtures" / "calendar" / "events.json").write_text(
        json.dumps(meetings_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    (task_dir / "task.yaml").write_text(
        yaml.safe_dump(build_task_yaml(task_id, target_date, scenario, rng), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    (task_dir / "grader.py").write_text(render_grader(task_id, target_date, scenario), encoding="utf-8")

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
    parser = argparse.ArgumentParser(description="Generate T114 meeting preparation variants")
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

    manifest_path = task_root / "generated_meeting_preparation_en_manifest.json"
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
