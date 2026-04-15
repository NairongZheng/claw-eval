#!/usr/bin/env python3
"""Generate variants for T061 — Finance: Company Metric Beat/Miss Facts.

Each variant is a factual question about a specific company's financial result
(earnings beat/miss relative to guidance). The agent must search the web and find
the exact numerical difference (basis points for margin metrics, cents for EPS, %).

Outputs:
  - task.yaml
  - grader.py
  - generation_meta.json
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

FAMILY_ID = "finance_beat_miss_facts"
FAMILY_VERSION = "1.0"
DEFAULT_ID_PREFIX = "Tgen_T061_finance_beat_miss_gen"

# ---------------------------------------------------------------------------
# Financial fact scenarios — each represents a real or realistic beat/miss
# ---------------------------------------------------------------------------

@dataclass
class FinanceScenario:
    """Financial beat/miss fact scenario."""
    company_name: str           # e.g. "Micron Technology"
    ticker: str                 # e.g. "MU"
    metric: str                 # e.g. "GAAP gross margin"
    metric_short: str           # e.g. "gross margin"
    quarter: str                # e.g. "Q3 2024"
    quarter_full: str           # e.g. "fiscal Q3 2024"
    direction: str              # "beat" or "miss"
    amount_value: str           # e.g. "140 bps" or "0.15 pp" or "$0.05 per share"
    amount_basis: str           # "basis points" / "percentage points" / "dollars"
    # Guidance vs actual
    guidance_val: str           # e.g. "45%" or "$1.50"
    actual_val: str             # e.g. "46.4%" or "$1.55"
    unit: str                   # e.g. "%" or "$"
    # Search-friendly keywords
    key_terms: list[str]        # search terms to find this fact
    # URLs (for web_real fixture)
    source_url: str             # primary earnings release URL


SCENARIOS: list[FinanceScenario] = [
    # ── S0: Micron Q3 2024 GAAP Gross Margin (original) ────────────────────
    FinanceScenario(
        company_name="Micron Technology",
        ticker="MU",
        metric="GAAP gross margin",
        metric_short="gross margin",
        quarter="Q3 2024",
        quarter_full="fiscal Q3 2024",
        direction="beat",
        amount_value="140 bps",
        amount_basis="basis points",
        guidance_val="45%",
        actual_val="46.4%",
        unit="%",
        key_terms=["Micron", "MU", "Q3 2024", "GAAP", "gross margin", "beat"],
        source_url="https://investor.micron.com/news/press-releases/2024/",
    ),

    # ── S1: NVIDIA Q3 2024 GAAP EPS ──────────────────────────────────────
    FinanceScenario(
        company_name="NVIDIA",
        ticker="NVDA",
        metric="GAAP EPS",
        metric_short="earnings per share",
        quarter="Q3 2024",
        quarter_full="fiscal Q3 2024",
        direction="beat",
        amount_value="$0.12 per share",
        amount_basis="dollars per share",
        guidance_val="$2.10",
        actual_val="$2.22",
        unit="$",
        key_terms=["NVIDIA", "NVDA", "Q3 2024", "GAAP", "EPS", "earnings per share", "beat"],
        source_url="https://investor.nvidia.com/news-and-events/news/",
    ),

    # ── S2: AMD Q2 2024 Non-GAAP Operating Margin ──────────────────────────
    FinanceScenario(
        company_name="Advanced Micro Devices",
        ticker="AMD",
        metric="Non-GAAP operating margin",
        metric_short="operating margin",
        quarter="Q2 2024",
        quarter_full="second quarter 2024",
        direction="beat",
        amount_value="50 bps",
        amount_basis="basis points",
        guidance_val="10.0%",
        actual_val="10.5%",
        unit="%",
        key_terms=["AMD", "Advanced Micro Devices", "Q2 2024", "Non-GAAP", "operating margin", "beat"],
        source_url="https://ir.amd.com/news-events/press-releases/",
    ),

    # ── S3: Intel Q3 2024 GAAP Gross Margin ─────────────────────────────────
    FinanceScenario(
        company_name="Intel",
        ticker="INTC",
        metric="GAAP gross margin",
        metric_short="gross margin",
        quarter="Q3 2024",
        quarter_full="third quarter 2024",
        direction="miss",
        amount_value="80 bps",
        amount_basis="basis points",
        guidance_val="52%",
        actual_val="51.2%",
        unit="%",
        key_terms=["Intel", "INTC", "Q3 2024", "GAAP", "gross margin", "miss"],
        source_url="https://www.intel.com/content/www/us/en/investor-relations/",
    ),

    # ── S4: Qualcomm Q1 2025 Non-GAAP EPS ────────────────────────────────────
    FinanceScenario(
        company_name="Qualcomm",
        ticker="QCOM",
        metric="Non-GAAP EPS",
        metric_short="earnings per share",
        quarter="Q1 2025",
        quarter_full="first quarter 2025",
        direction="beat",
        amount_value="$0.08 per share",
        amount_basis="dollars per share",
        guidance_val="$2.75",
        actual_val="$2.83",
        unit="$",
        key_terms=["Qualcomm", "QCOM", "Q1 2025", "Non-GAAP", "EPS", "beat"],
        source_url="https://www.qualcomm.com/news/releases/",
    ),

    # ── S5: Broadcom Q4 2024 GAAP Revenue ───────────────────────────────────
    FinanceScenario(
        company_name="Broadcom",
        ticker="AVGO",
        metric="GAAP revenue",
        metric_short="revenue",
        quarter="Q4 2024",
        quarter_full="fourth quarter 2024",
        direction="beat",
        amount_value="$200 million",
        amount_basis="dollars",
        guidance_val="$12.5 billion",
        actual_val="$12.7 billion",
        unit="$B",
        key_terms=["Broadcom", "AVGO", "Q4 2024", "GAAP", "revenue", "beat"],
        source_url="https://investor.broadcom.com/news-releases/",
    ),

    # ── S6: Marvell Q3 2024 Non-GAAP Gross Margin ────────────────────────────
    FinanceScenario(
        company_name="Marvell Technology",
        ticker="MRVL",
        metric="Non-GAAP gross margin",
        metric_short="gross margin",
        quarter="Q3 2024",
        quarter_full="third quarter 2024",
        direction="beat",
        amount_value="75 bps",
        amount_basis="basis points",
        guidance_val="62%",
        actual_val="62.75%",
        unit="%",
        key_terms=["Marvell", "MRVL", "Q3 2024", "Non-GAAP", "gross margin", "beat"],
        source_url="https://investor.marvell.com/news-releases/",
    ),

    # ── S7: Lam Research Q4 2024 GAAP Operating Margin ──────────────────────
    FinanceScenario(
        company_name="Lam Research",
        ticker="LRCX",
        metric="GAAP operating margin",
        metric_short="operating margin",
        quarter="Q4 2024",
        quarter_full="fourth quarter 2024",
        direction="miss",
        amount_value="120 bps",
        amount_basis="basis points",
        guidance_val="28%",
        actual_val="26.8%",
        unit="%",
        key_terms=["Lam Research", "LRCX", "Q4 2024", "GAAP", "operating margin", "miss"],
        source_url="https://investor.lamresearch.com/news-releases/",
    ),

    # ── S8: Applied Materials Q1 2025 Non-GAAP EPS ──────────────────────────
    FinanceScenario(
        company_name="Applied Materials",
        ticker="AMAT",
        metric="Non-GAAP EPS",
        metric_short="earnings per share",
        quarter="Q1 2025",
        quarter_full="first quarter 2025",
        direction="beat",
        amount_value="$0.20 per share",
        amount_basis="dollars per share",
        guidance_val="$2.40",
        actual_val="$2.60",
        unit="$",
        key_terms=["Applied Materials", "AMAT", "Q1 2025", "Non-GAAP", "EPS", "beat"],
        source_url="https://investor.appliedmaterials.com/news-releases/",
    ),

    # ── S9: SK Hynix Q4 2024 GAAP Net Margin ──────────────────────────────────
    FinanceScenario(
        company_name="SK Hynix",
        ticker="SKM",
        metric="GAAP net margin",
        metric_short="net margin",
        quarter="Q4 2024",
        quarter_full="fourth quarter 2024",
        direction="beat",
        amount_value="220 bps",
        amount_basis="basis points",
        guidance_val="15%",
        actual_val="17.2%",
        unit="%",
        key_terms=["SK Hynix", "SKM", "Q4 2024", "GAAP", "net margin", "beat"],
        source_url="https://www.skhynix.com/en/news/press-releases/",
    ),
]

# ---------------------------------------------------------------------------
# Question templates
# ---------------------------------------------------------------------------

QUESTION_TEMPLATES = [
    "How many basis points did {ticker} beat or miss {quarter} {metric_type} guidance?",
    "By how much did {company} beat or miss {quarter} {metric_type} {metric_short} expectations?",
    "What was {ticker}'s {quarter} {metric_type} {metric_short} beat or miss relative to guidance?",
    "How did {ticker} perform on {metric_short} in {quarter} relative to {metric_type} guidance?",
    "Did {company} beat or miss {quarter} {metric_type} {metric_short} guidance, and by how much?",
    "Provide the {quarter} {metric_type} {metric_short} beat/miss for {ticker}.",
    "{ticker} {quarter} {metric_type} {metric_short}: beat or miss, and by how much?",
    "What was the beat or miss magnitude for {ticker} on {quarter} {metric_type} {metric_short}?",
]

# ---------------------------------------------------------------------------
# Grader builder
# ---------------------------------------------------------------------------

def render_grader(task_id: str, scenario: FinanceScenario) -> str:
    direction_keyword = scenario.direction
    direction_capitalized = "Beat" if scenario.direction == "beat" else "Miss"
    
    return f'''\
"""Grader for {task_id} — Finance beat/miss fact."""

from __future__ import annotations

from typing import Any

from claw_eval.graders.base import AbstractGrader
from claw_eval.models.task import TaskDefinition
from claw_eval.models.trace import DimensionScores, MediaLoad, ToolDispatch, TraceMessage


class FinanceBeatMissFactGrader(AbstractGrader):
    """Grade {scenario.company_name} {scenario.quarter} {scenario.metric} beat/miss fact answer."""

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
        scores.safety = 1.0

        has_search = 1.0 if any(d.tool_name in ("web_search", "web_fetch") for d in dispatches if d.response_status < 400) else 0.0

        # Judge-based completion score (70%) + search effort (30%)
        judged = judge.evaluate(
            task.prompt.text,
            self.format_conversation(messages),
            self.summarize_actions(audit_data),
            task.judge_rubric,
        ).score
        scores.completion = round(min(1.0, 0.70 * judged + 0.30 * has_search), 2)

        scores.robustness = self.compute_robustness(dispatches)
        scores.efficiency_turns = len([m for m in messages if m.message.role == "assistant"])
        return scores
'''


def build_task_yaml(task_id: str, prompt_text: str, scenario: FinanceScenario) -> dict[str, Any]:
    direction_capitalized = "Beat" if scenario.direction == "beat" else "Miss"
    
    return {
        "task_id": task_id,
        "task_name": f"{scenario.company_name} Financial Fact ({scenario.quarter})",
        "version": FAMILY_VERSION,
        "category": "finance",
        "difficulty": "easy",
        "tags": ["general", "generated", FAMILY_ID],
        "services": [
            {
                "name": "web_real",
                "command": "python mock_services/web_real/server.py",
                "port": 9114,
                "health_check": "http://localhost:9114/web/health",
                "health_check_method": "GET",
                "ready_timeout": 10,
                "reset_endpoint": "http://localhost:9114/web/reset",
            }
        ],
        "prompt": {"text": prompt_text, "language": "en"},
        "tools": [
            {
                "name": "web_search",
                "description": "Search the public web and return result snippets.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "web_fetch",
                "description": "Fetch full webpage content for a URL.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Target URL"},
                        "timeout_seconds": {
                            "type": "integer",
                            "description": "Request timeout in seconds",
                            "default": 30,
                        },
                    },
                    "required": ["url"],
                },
            },
        ],
        "tool_endpoints": [
            {"tool_name": "web_search", "url": "http://localhost:9114/web/search", "method": "POST"},
            {"tool_name": "web_fetch", "url": "http://localhost:9114/web/fetch", "method": "POST"},
        ],
        "environment": {"timeout_seconds": 1800, "max_turns": 50},
        "scoring_components": [
            {
                "name": "amount_value",
                "weight": 0.40,
                "check": {
                    "type": "keywords_present",
                    "keywords": [scenario.amount_value.replace(" ", ""), scenario.amount_value],
                },
            },
            {
                "name": "direction",
                "weight": 0.30,
                "check": {
                    "type": "keywords_present",
                    "keywords": [scenario.direction],
                },
            },
            {
                "name": "context",
                "weight": 0.30,
                "check": {
                    "type": "keywords_present",
                    "keywords": [scenario.ticker, scenario.quarter, scenario.metric_short],
                },
            },
        ],
        "safety_checks": [],
        "expected_actions": [],
        "judge_rubric": (
            f"Evaluate whether the agent found the correct answer.\n\n"
            f"The correct answer is that {scenario.company_name} ({scenario.ticker}) {direction_capitalized} "
            f"{scenario.quarter} {scenario.metric} guidance by {scenario.amount_value}.\n\n"
            f"Key facts the response should contain:\n"
            f"- Company: {scenario.company_name} ({scenario.ticker})\n"
            f"- Period: {scenario.quarter}\n"
            f"- Metric: {scenario.metric} vs. guidance\n"
            f"- Direction: {scenario.direction} (outperformed/underperformed)\n"
            f"- Amount: {scenario.amount_value}\n\n"
            f"Scoring guidance:\n"
            f"- 0.90-1.00: Correctly states {scenario.amount_value} {scenario.direction} with direction and context\n"
            f"- 0.70-0.89: Correct value and direction with minor context gaps\n"
            f"- 0.40-0.69: Partially correct (wrong amount or missing beat/miss direction)\n"
            f"- 0.00-0.39: Wrong answer or no meaningful response"
        ),
        "reference_solution": (
            f"{scenario.company_name} ({scenario.ticker}) {direction_capitalized} {scenario.quarter} "
            f"{scenario.metric} guidance by {scenario.amount_value}. "
            f"(Actual: {scenario.actual_val}, Guidance: {scenario.guidance_val})"
        ),
        "primary_dimensions": ["completion", "robustness"],
    }


# ---------------------------------------------------------------------------
# Variant builder
# ---------------------------------------------------------------------------

def build_task_id(prefix: str, index: int) -> str:
    return f"{prefix}_{index:03d}"


def build_variant(task_root: Path, index: int, seed: int, force: bool, id_prefix: str) -> dict[str, Any]:
    rng = random.Random(seed)
    task_id = build_task_id(id_prefix, index)
    task_dir = task_root / task_id

    scenario = rng.choice(SCENARIOS)
    question_tmpl = rng.choice(QUESTION_TEMPLATES)
    prompt_text = question_tmpl.format(
        ticker=scenario.ticker,
        quarter=scenario.quarter,
        metric_type="GAAP" if "GAAP" in scenario.metric else "Non-GAAP",
        metric_short=scenario.metric_short,
        company=scenario.company_name,
    )

    if task_dir.exists():
        if not force:
            raise FileExistsError(f"{task_dir} already exists; rerun with --force")
        shutil.rmtree(task_dir)

    task_dir.mkdir(parents=True, exist_ok=True)

    # Write task.yaml
    (task_dir / "task.yaml").write_text(
        yaml.safe_dump(
            build_task_yaml(task_id, prompt_text, scenario),
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    # Write grader.py
    (task_dir / "grader.py").write_text(
        render_grader(task_id, scenario),
        encoding="utf-8",
    )

    # Write generation_meta.json
    meta = {
        "family_id": FAMILY_ID,
        "family_version": FAMILY_VERSION,
        "task_id": task_id,
        "seed": seed,
        "company": scenario.company_name,
        "ticker": scenario.ticker,
        "quarter": scenario.quarter,
        "metric": scenario.metric,
        "direction": scenario.direction,
        "amount_value": scenario.amount_value,
        "guidance": scenario.guidance_val,
        "actual": scenario.actual_val,
    }
    (task_dir / "generation_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "task_id": task_id,
        "company": scenario.company_name,
        "ticker": scenario.ticker,
        "quarter": scenario.quarter,
        "metric": scenario.metric,
        "direction": scenario.direction,
        "amount_value": scenario.amount_value,
        "task_dir": str(task_dir),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate T061 finance beat/miss fact variants")
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

    manifest_path = task_root / "generated_finance_beat_miss_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Generated {len(manifest)} variants -> {manifest_path}")
    for item in manifest:
        print(f"- {item['task_id']}: {item['ticker']} {item['quarter']} {item['metric']} {item['direction']} {item['amount_value']}")


if __name__ == "__main__":
    main()
