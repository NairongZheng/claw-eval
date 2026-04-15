#!/usr/bin/env python3
"""Generate variants for T091_pinbench_humanize_blog.

Outputs standalone tasks containing:
- task.yaml
- grader.py
- generation_meta.json
- fixtures/docs/ai_blog.txt
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import textwrap
from pathlib import Path
from typing import Any

import yaml

FAMILY_ID = "pinbench_humanize_blog"
FAMILY_VERSION = "1.0"
DEFAULT_ID_PREFIX = "Tgen_T091_pinbench_humanize_blog_gen"

BAD_PHRASE_POOL = [
    "Furthermore",
    "Moreover",
    "Additionally",
    "It is important to note",
    "It is worth mentioning",
    "In today's fast-paced world",
    "In conclusion",
    "It is essential",
]

CONTEXT_POOL = [
    "a remote software team shipping weekly releases",
    "a startup support team handling urgent customer tickets",
    "a marketing team balancing campaign work and analytics",
    "an operations team coordinating cross-functional launches",
    "an individual contributor juggling deep work and meetings",
    "a product team preparing a quarterly roadmap review",
    "a data team maintaining dashboards while handling ad-hoc requests",
    "a customer success team balancing renewals and proactive outreach",
    "a design team splitting time between execution and stakeholder reviews",
    "an engineering manager coordinating delivery and people development",
]

VOICE_HINTS = [
    "Use a conversational voice with varied sentence lengths.",
    "Make it sound like practical advice from a colleague.",
    "Keep it human and direct, avoiding stiff transition words.",
    "Prefer natural flow and concrete examples over generic filler.",
    "Use plain language and avoid over-explaining obvious points.",
    "Keep the tone warm, practical, and a little opinionated.",
    "Write like a mentor giving real-world productivity advice.",
    "Favor clarity and rhythm over formal-sounding wording.",
    "Make it feel grounded in day-to-day work, not abstract theory.",
    "Use confident but friendly phrasing throughout.",
]

PROMPT_OPENERS = [
    "You are editing a draft that currently sounds AI-written.",
    "Please humanize the attached post without changing its core recommendations.",
    "Treat the attachment as a rough machine-style draft and rewrite it for real readers.",
    "Rewrite this article so it reads like a person wrote it, not a template engine.",
    "Take this stiff draft and make it sound natural, credible, and human.",
    "The attached blog is informative but robotic; rewrite it for readability.",
    "Refine this draft into a human-sounding post with better flow.",
    "Convert this mechanical write-up into an engaging, practical article.",
    "Edit the attachment as if preparing it for publication on a team blog.",
    "Improve voice and naturalness while preserving the original guidance.",
]

PROMPT_AUDIENCES = [
    "Target audience: early-career professionals.",
    "Target audience: team leads managing mixed strategic and operational work.",
    "Target audience: busy knowledge workers who want practical advice.",
    "Target audience: startup teams under constant context switching.",
    "Target audience: project managers balancing delivery and communication overhead.",
    "Target audience: remote-first teams struggling with fragmented attention.",
    "Target audience: cross-functional contributors with heavy meeting calendars.",
    "Target audience: founders and operators with limited time and high ambiguity.",
    "Target audience: individual contributors aiming to reduce burnout risk.",
    "Target audience: managers coaching teams on sustainable productivity habits.",
]

PROMPT_FORMATS = [
    "Output format: 5 short sections plus a brief concluding paragraph.",
    "Output format: headline + bullet-friendly paragraphs with clear transitions.",
    "Output format: concise blog style, skimmable and practical.",
    "Output format: plain-language article with no fluff and no numbered list overload.",
    "Output format: intro, five themed sections, and a concise takeaway.",
    "Output format: reader-friendly blog with short paragraphs and clear signposting.",
    "Output format: practical guide style with smooth transitions between sections.",
    "Output format: editorial blog tone, tight structure, minimal repetition.",
    "Output format: compact playbook style with one key point per section.",
    "Output format: modern online article style, scannable and concrete.",
]

PROMPT_STYLE_GUARDS = [
    "Avoid repetitive sentence openings and avoid overusing connector adverbs.",
    "Keep sentence rhythm varied (mix short and medium sentences).",
    "Prefer concrete wording over generic motivational phrasing.",
    "Use natural transitions; avoid textbook-style discourse markers.",
    "Avoid corporate jargon and avoid sounding like a template.",
    "Cut filler phrases and keep each paragraph purposeful.",
    "Vary paragraph openings so the text does not feel formulaic.",
    "Favor active voice unless passive is clearly better.",
    "Use specific, practical phrasing instead of abstract claims.",
    "Keep momentum: each paragraph should naturally lead to the next.",
]

PROMPT_PRESERVE_RULES = [
    "Do not drop any of these themes: prioritization, reducing distractions, time blocking, breaks, work-life balance.",
    "Retain all five core advice pillars while improving readability and tone.",
    "Keep the same ideas intact; only improve voice, flow, and naturalness.",
    "Preserve meaning and practical guidance, but remove robotic phrasing.",
    "Do not change the core message; rewrite for clarity and human tone only.",
    "Maintain all original recommendations while improving coherence and style.",
    "Preserve the original intent and advice sequence, but make language natural.",
    "Keep informational content stable; focus edits on voice and readability.",
    "Do not add new frameworks; keep the same five-topic scope.",
    "Retain the practical guidance exactly in spirit, with better phrasing.",
]

SECTION_TITLES = [
    "Prioritization",
    "Reducing Distractions",
    "Time Blocking",
    "Taking Breaks",
    "Work-Life Balance",
]


def build_task_id(prefix: str, index: int) -> str:
    return f"{prefix}_{index:03d}"


def build_robotic_blog(rng: random.Random, context: str) -> str:
    bad = rng.sample(BAD_PHRASE_POOL, k=6)
    intro = (
        f"{bad[0]}, productivity is a foundational requirement for modern professionals, especially in {context}. "
        f"{bad[1]}, teams and individuals often underestimate the cumulative impact of small planning decisions. "
        f"{bad[2]}, by adopting structured habits, one may improve consistency and reduce stress over time."
    )

    sec_prioritization = (
        f"{bad[3]}, prioritization should be performed at the beginning of each day and revisited as needed. "
        "Tasks should be ranked by impact and urgency, and low-value activities should be deferred or removed. "
        "A concise list of 3 to 5 critical outcomes helps preserve focus when interruptions appear. "
        "Without this discipline, effort is frequently spent on visible but non-essential work."
    )

    sec_distractions = (
        "Distraction management is another significant factor. "
        "Notifications, ad-hoc messages, and unnecessary context switching consume attention and lower cognitive quality. "
        "Teams can designate response windows, mute non-critical channels, and batch shallow communication. "
        "Environmental cues such as a clean workspace and clear boundaries also improve attention quality."
    )

    sec_time_block = (
        f"{bad[4]}, time blocking is a practical method to protect high-value tasks. "
        "Individuals may reserve dedicated blocks for deep work, collaboration, administrative tasks, and planning. "
        "When blocks are explicit, calendars become realistic, and overcommitment becomes easier to detect. "
        "This approach improves predictability and helps align personal priorities with team commitments."
    )

    sec_breaks = (
        "Breaks should not be interpreted as unproductive time. "
        "Short pauses restore attention, reduce decision fatigue, and improve quality in later sessions. "
        "A brief walk, hydration, or stepping away from a screen can reset mental energy. "
        "Consistent recovery behavior is often correlated with fewer avoidable mistakes."
    )

    sec_balance = (
        f"{bad[5]}, work-life balance supports sustainable performance across longer cycles. "
        "If people are always available, boundaries erode and burnout risk increases. "
        "Reasonable working hours, intentional shutdown routines, and clear handoffs preserve long-term effectiveness. "
        "Sustainable output is more valuable than temporary overextension."
    )

    ending = (
        "In summary, productive routines become reliable when they are simple and repeated. "
        "Prioritization, distraction reduction, time blocking, regular breaks, and work-life balance should operate as a connected system. "
        "Organizations and individuals can make steady progress by applying these principles consistently."
    )

    sections = [
        intro,
        f"\n\n## {SECTION_TITLES[0]}\n{sec_prioritization}",
        f"\n\n## {SECTION_TITLES[1]}\n{sec_distractions}",
        f"\n\n## {SECTION_TITLES[2]}\n{sec_time_block}",
        f"\n\n## {SECTION_TITLES[3]}\n{sec_breaks}",
        f"\n\n## {SECTION_TITLES[4]}\n{sec_balance}",
        f"\n\n{ending}",
    ]
    return "".join(sections)


def build_prompt(voice_hint: str) -> str:
    return (
        "Rewrite the attached blog post so it sounds natural and human-written while "
        "keeping the same core advice. Reduce robotic transitions such as 'Furthermore' "
        "or 'It is important to note'. Preserve guidance about prioritization, reducing "
        "distractions, time blocking, breaks, and work-life balance. "
        f"{voice_hint}"
    )


def build_prompt_variant(rng: random.Random, context: str, voice_hint: str) -> tuple[str, dict[str, str]]:
    opener = rng.choice(PROMPT_OPENERS)
    audience = rng.choice(PROMPT_AUDIENCES)
    fmt = rng.choice(PROMPT_FORMATS)
    style_guard = rng.choice(PROMPT_STYLE_GUARDS)
    preserve = rng.choice(PROMPT_PRESERVE_RULES)
    prompt = textwrap.dedent(
        f"""\
        {opener}
        Context of the draft: {context}.
        {audience}
        {preserve}
        Reduce robotic transitions like "Furthermore" and "It is important to note".
        {style_guard}
        {fmt}
        {voice_hint}
        """
    ).strip()
    profile = {
        "opener": opener,
        "audience": audience,
        "format": fmt,
        "style_guard": style_guard,
        "preserve_rule": preserve,
    }
    return prompt, profile


def build_task_yaml(task_id: str, prompt_text: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "task_name": "Pinbench Humanize Blog Variant",
        "version": FAMILY_VERSION,
        "category": "rewriting",
        "difficulty": "easy",
        "tags": ["general", "generated", "en", FAMILY_ID],
        "prompt": {
            "text": prompt_text,
            "language": "en",
            "attachments": ["fixtures/docs/ai_blog.txt"],
        },
        "tools": [],
        "tool_endpoints": [],
        "sandbox_files": ["fixtures/docs/ai_blog.txt"],
        "environment": {"timeout_seconds": 180, "max_turns": 8},
        "scoring_components": [],
        "safety_checks": [],
        "expected_actions": [],
        "judge_rubric": "Reward rewrites that preserve all five advice pillars while sounding conversational and less robotic.",
        "reference_solution": "A natural rewrite keeping the same ideas with reduced AI-style transitions.",
        "primary_dimensions": ["completion", "communication", "safety"],
    }


def render_grader(task_id: str, bad_phrases: list[str], min_length: int) -> str:
    bad_phrase_list_literal = repr([p.lower() for p in bad_phrases])
    return f'''\
"""Standalone grader for {task_id}."""

from __future__ import annotations

from typing import Any

from claw_eval.graders.base import AbstractGrader
from claw_eval.models.task import TaskDefinition
from claw_eval.models.trace import DimensionScores, MediaLoad, ToolDispatch, TraceMessage


class GeneratedPinbenchHumanizeBlogGrader(AbstractGrader):
    BAD_PHRASES = {bad_phrase_list_literal}
    TOPIC_KEYWORDS = ["priorit", "distraction", "time block", "break", "work-life"]
    CONTRACTIONS = ["don't", "can't", "it's", "you'll", "we're", "isn't", "won't", "they're", "I've", "you're"]
    MIN_LENGTH = {min_length}

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
        scores = DimensionScores(safety=1.0)
        final_text = self._get_final_assistant_text(messages)
        lower = final_text.lower()

        topic_score = sum(1 for t in self.TOPIC_KEYWORDS if t in lower) / len(self.TOPIC_KEYWORDS)
        bad_count = sum(1 for p in self.BAD_PHRASES if p in lower)
        robotic_score = 1.0 if bad_count == 0 else 0.6 if bad_count <= 1 else 0.2

        contraction_hits = sum(1 for c in self.CONTRACTIONS if c.lower() in lower)
        conversational_score = 1.0 if contraction_hits >= 3 else 0.6 if contraction_hits >= 1 else 0.2

        length_score = 1.0 if len(final_text) >= self.MIN_LENGTH else 0.5 if len(final_text) >= int(self.MIN_LENGTH * 0.7) else 0.2
        structure_score = 1.0 if final_text.count("\\n") >= 6 else 0.6

        scores.completion = round(
            0.30 * topic_score
            + 0.30 * ((robotic_score + conversational_score) / 2)
            + 0.25 * length_score
            + 0.15 * structure_score,
            2,
        )
        scores.robustness = 1.0
        scores.efficiency_turns = len([m for m in messages if m.message.role == "assistant"])
        return scores
'''


def build_generation_meta(
    task_id: str,
    seed: int,
    context: str,
    voice_hint: str,
    bad_phrases: list[str],
    prompt_profile: dict[str, str],
) -> dict[str, Any]:
    return {
        "family_id": FAMILY_ID,
        "family_version": FAMILY_VERSION,
        "task_id": task_id,
        "seed": seed,
        "context": context,
        "voice_hint": voice_hint,
        "bad_phrases": bad_phrases,
        "prompt_profile": prompt_profile,
    }


def build_variant(task_root: Path, index: int, seed: int, force: bool, id_prefix: str) -> dict[str, Any]:
    rng = random.Random(seed)
    task_id = build_task_id(id_prefix, index)
    task_dir = task_root / task_id

    context = rng.choice(CONTEXT_POOL)
    voice_hint = rng.choice(VOICE_HINTS)
    bad_for_grader = rng.sample(BAD_PHRASE_POOL, k=4)
    min_length = rng.choice([850, 900, 950])
    blog_text = build_robotic_blog(rng, context)
    prompt_text, prompt_profile = build_prompt_variant(rng, context, voice_hint)

    if task_dir.exists():
        if not force:
            raise FileExistsError(f"{task_dir} already exists; rerun with --force")
        shutil.rmtree(task_dir)

    (task_dir / "fixtures" / "docs").mkdir(parents=True, exist_ok=True)
    (task_dir / "fixtures" / "docs" / "ai_blog.txt").write_text(blog_text + "\n", encoding="utf-8")

    (task_dir / "task.yaml").write_text(
        yaml.safe_dump(build_task_yaml(task_id, prompt_text), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (task_dir / "grader.py").write_text(render_grader(task_id, bad_for_grader, min_length), encoding="utf-8")
    (task_dir / "generation_meta.json").write_text(
        json.dumps(
            build_generation_meta(task_id, seed, context, voice_hint, bad_for_grader, prompt_profile),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "task_id": task_id,
        "context": context,
        "prompt_opener": prompt_profile["opener"],
        "prompt_format": prompt_profile["format"],
        "min_length": min_length,
        "bad_phrases": bad_for_grader,
        "task_dir": str(task_dir),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate T091 humanize-blog variants")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260415)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--tasks-root", default=None, help="Deprecated alias of --output-dir")
    parser.add_argument("--id-prefix", default=DEFAULT_ID_PREFIX)
    parser.add_argument("--force", action="store_true")
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

    manifest_path = task_root / "generated_pinbench_humanize_blog_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Generated {len(manifest)} variants -> {manifest_path}")
    for item in manifest:
        print(f"- {item['task_id']}: {item['context']} | min_len={item['min_length']}")


if __name__ == "__main__":
    main()
