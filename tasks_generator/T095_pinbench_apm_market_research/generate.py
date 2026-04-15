#!/usr/bin/env python3
"""Generate variants for T095 — Pinbench Market Research (KB-based).

Each variant is a market research task where the agent must use a knowledge base
to analyze a specific market/domain, identifying competitors, pricing models, and
market trends. Then synthesize findings into a report with comparison table.

Outputs:
  - task.yaml
  - grader.py
  - generation_meta.json
  - fixtures/kb/articles.json
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

FAMILY_ID = "pinbench_market_research"
FAMILY_VERSION = "1.0"
DEFAULT_ID_PREFIX = "Tgen_T095_pinbench_market_research_gen"

# ---------------------------------------------------------------------------
# Market research scenarios
# ---------------------------------------------------------------------------

@dataclass
class MarketScenario:
    """Market research scenario with vendors and focus areas."""
    market_name: str           # e.g. "Enterprise Observability and APM"
    market_short: str          # e.g. "APM"
    industry: str              # e.g. "DevOps/Observability"
    key_vendors: list[str]     # top 5+ vendors
    key_trends: list[str]      # current market trends
    analysis_focus: str        # pricing / features / market positioning
    comparison_factors: list[str]  # what to compare (pricing, automation, etc.)
    min_vendors_required: int  # minimum to identify in report


SCENARIOS: list[MarketScenario] = [
    # ── S0: APM Market (original) ─────────────────────────────────────────
    MarketScenario(
        market_name="Enterprise Observability and APM",
        market_short="APM",
        industry="DevOps/Observability",
        key_vendors=["Datadog", "Dynatrace", "New Relic", "Grafana Labs", "Splunk"],
        key_trends=["OpenTelemetry standardization", "AI-assisted root cause analysis", 
                    "platform consolidation", "cloud-native deployment", "consumption-based pricing"],
        analysis_focus="pricing and automation",
        comparison_factors=["pricing model", "key differentiator", "strengths", "weaknesses", "ideal use case"],
        min_vendors_required=5,
    ),

    # ── S1: Cloud Storage & CDN ───────────────────────────────────────────
    MarketScenario(
        market_name="Cloud Storage and Content Delivery",
        market_short="Storage/CDN",
        industry="Cloud Infrastructure",
        key_vendors=["AWS S3", "Azure Blob Storage", "Google Cloud Storage", "Backblaze B2", "Wasabi"],
        key_trends=["multi-cloud strategies", "cost optimization focus", "object storage dominance",
                    "AI/ML workload acceleration", "edge computing expansion"],
        analysis_focus="pricing and performance",
        comparison_factors=["pricing per GB", "egress costs", "performance tier", "durability/availability", "compliance features"],
        min_vendors_required=5,
    ),

    # ── S2: Container Orchestration ───────────────────────────────────────
    MarketScenario(
        market_name="Container Orchestration Platforms",
        market_short="Kubernetes",
        industry="DevOps/Containers",
        key_vendors=["Kubernetes (OSS)", "Docker Swarm", "Amazon ECS", "OpenShift", "Rancher"],
        key_trends=["Kubernetes consolidation", "GitOps adoption", "service mesh evolution",
                    "security scanning integration", "multi-cluster management"],
        analysis_focus="architecture and ecosystem",
        comparison_factors=["cluster management", "networking approach", "security features", "ecosystem maturity", "vendor support"],
        min_vendors_required=5,
    ),

    # ── S3: Database as a Service ─────────────────────────────────────────
    MarketScenario(
        market_name="Managed Database Services",
        market_short="DBaaS",
        industry="Data & Analytics",
        key_vendors=["AWS RDS", "Azure Database", "Google Cloud SQL", "Neon", "PlanetScale"],
        key_trends=["serverless database growth", "PostgreSQL adoption surge", "vector database emergence",
                    "real-time analytics demand", "cost optimization tools"],
        analysis_focus="scalability and pricing",
        comparison_factors=["database types", "scaling model", "HA/DR capabilities", "pricing structure", "compliance support"],
        min_vendors_required=5,
    ),

    # ── S4: API Management ────────────────────────────────────────────────
    MarketScenario(
        market_name="API Management and Gateway Platforms",
        market_short="API Management",
        industry="Integration/APIs",
        key_vendors=["AWS API Gateway", "Kong", "MuleSoft", "Apigee (Google)", "Tyk"],
        key_trends=["AI-powered API discovery", "GraphQL adoption", "API monetization", 
                    "event-driven architecture", "zero-trust security"],
        analysis_focus="features and deployment",
        comparison_factors=["deployment options", "API gateway features", "developer experience", "analytics/monitoring", "pricing model"],
        min_vendors_required=5,
    ),

    # ── S5: Data Integration ETL ──────────────────────────────────────────
    MarketScenario(
        market_name="Data Integration and ETL Platforms",
        market_short="Data Integration",
        industry="Data & Analytics",
        key_vendors=["Talend", "Informatica", "dbt Labs", "Airbyte", "Fivetran"],
        key_trends=["low-code ETL emergence", "real-time data pipelines", "data mesh patterns",
                    "open-source tools growth", "AI-assisted data lineage"],
        analysis_focus="capabilities and ease-of-use",
        comparison_factors=["code vs low-code", "connectors available", "scalability approach", "support level", "total cost of ownership"],
        min_vendors_required=5,
    ),

    # ── S6: Incident Management ───────────────────────────────────────────
    MarketScenario(
        market_name="Incident Management and On-Call Platforms",
        market_short="Incident Mgmt",
        industry="DevOps/Operations",
        key_vendors=["PagerDuty", "Opsgenie (Atlassian)", "ilert", "OnCall (Grafana)", "BigPanda"],
        key_trends=["AI-powered alerting", "automation-first design", "noise reduction focus",
                    "observability integration", "multi-incident orchestration"],
        analysis_focus="automation and user experience",
        comparison_factors=["escalation policies", "integrations", "mobile app quality", "pricing model", "team size support"],
        min_vendors_required=5,
    ),

    # ── S7: Log Management ────────────────────────────────────────────────
    MarketScenario(
        market_name="Log Management and Analysis",
        market_short="Log Management",
        industry="DevOps/Observability",
        key_vendors=["ELK Stack", "Splunk Cloud", "Datadog Logs", "Sumo Logic", "Loggly"],
        key_trends=["log volume explosion", "AI-driven anomaly detection", "retention vs cost trade-offs",
                    "security analytics integration", "real-time alerting"],
        analysis_focus="search and retention",
        comparison_factors=["search performance", "retention policies", "indexing cost", "alert capabilities", "compliance features"],
        min_vendors_required=5,
    ),

    # ── S8: Application Performance Monitoring (narrower) ──────────────────
    MarketScenario(
        market_name="Synthetic Monitoring and Uptime Services",
        market_short="Synthetic Monitoring",
        industry="DevOps/Monitoring",
        key_vendors=["Datadog Synthetics", "New Relic Synthetics", "Pingdom", "Checkly", "StatusPage"],
        key_trends=["end-user experience focus", "API monitoring growth", "browser-based testing",
                    "multi-location checks", "proactive alerting"],
        analysis_focus="coverage and reliability",
        comparison_factors=["check types", "geographic coverage", "alert speed", "pricing per check", "integration ecosystem"],
        min_vendors_required=5,
    ),

    # ── S9: Security Information Event Management (SIEM) ───────────────────
    MarketScenario(
        market_name="Security Information and Event Management",
        market_short="SIEM",
        industry="Security/Compliance",
        key_vendors=["Splunk Enterprise Security", "IBM QRadar", "Elastic Security", "Microsoft Sentinel", "Sumo Logic Security"],
        key_trends=["cloud-native SIEM", "SOAR integration", "threat hunting automation",
                    "user behavior analytics", "cost-effective threat detection"],
        analysis_focus="threat detection and compliance",
        comparison_factors=["event ingestion volume", "threat detection capability", "compliance templates", "SOAR integration", "operational overhead"],
        min_vendors_required=5,
    ),
]

# ---------------------------------------------------------------------------
# Article generators
# ---------------------------------------------------------------------------

def build_kb_articles(scenario: MarketScenario, rng: random.Random) -> list[dict[str, Any]]:
    """Generate KB articles for the market research scenario."""
    articles = []
    article_id_base = f"gen_{rng.randint(1000, 9999)}"
    
    # ── Vendor profiles (one per key vendor) ──────────────────────────────
    for idx, vendor in enumerate(scenario.key_vendors):
        vendor_lower = vendor.lower().replace(" (", "_").replace(")", "").replace(" ", "_")
        
        # Create a brief vendor profile
        profiles = {
            # APM vendors
            "Datadog": "market leader in cloud-native observability with broad infrastructure coverage, strong APM plus logs plus security integration, and fast time to value.",
            "Dynatrace": "enterprise-scale observability choice with strong automation, topology mapping, and AI-assisted root cause analysis.",
            "New Relic": "unified telemetry platform with usage-based pricing and a large free tier, positioned around full-stack application visibility.",
            "Grafana Labs": "open-source adoption with LGTM positioning and OpenTelemetry-friendly architecture.",
            "Splunk": "strong in large enterprises with logs, security, and cross-domain analytics focus.",
            
            # Storage vendors
            "AWS S3": "object storage leader with global scale, 11 nines durability, and deep AWS ecosystem integration.",
            "Azure Blob Storage": "Microsoft's cloud storage with strong hybrid capabilities and enterprise compliance features.",
            "Google Cloud Storage": "competitive regional pricing and strong analytics integration with BigQuery.",
            "Backblaze B2": "cost-effective S3-compatible storage with transparent, predictable pricing.",
            "Wasabi": "affordable hot storage alternative with consistent performance and no egress fees.",
            
            # K8s vendors
            "Kubernetes (OSS)": "industry-standard open-source container orchestration with broad ecosystem and community support.",
            "Docker Swarm": "simpler alternative to Kubernetes with built-in Docker integration and lower complexity.",
            "Amazon ECS": "AWS-native container orchestration service tightly integrated with AWS ecosystem.",
            "OpenShift": "Red Hat's Kubernetes distribution with enterprise support, developer experience focus, and security hardening.",
            "Rancher": "multi-cluster Kubernetes management platform with fleet and local cluster support.",
            
            # DBaaS vendors
            "AWS RDS": "managed database service with broad database engine support and deep AWS integration.",
            "Azure Database": "Microsoft's managed databases with hybrid capabilities and Azure-native tooling.",
            "Google Cloud SQL": "managed SQL databases with strong analytics integration and multi-region options.",
            "Neon": "modern serverless PostgreSQL with branching, autoscaling, and developer-friendly APIs.",
            "PlanetScale": "MySQL-compatible serverless database with Vitess technology and instant scaling.",
            
            # API vendors
            "AWS API Gateway": "AWS-native API management with Lambda integration and pay-per-request pricing.",
            "Kong": "open-source API gateway with enterprise extensions and strong plugin ecosystem.",
            "MuleSoft": "enterprise integration platform with API management and workflow automation.",
            "Apigee (Google)": "Google's API management platform with analytics and traffic management.",
            "Tyk": "open-source and cloud API gateway with advanced rate limiting and OAuth support.",
            
            # ETL vendors
            "Talend": "comprehensive data integration with low-code and governance capabilities.",
            "Informatica": "enterprise data integration with cloud and on-premise options.",
            "dbt Labs": "modern data transformation tool focused on SQL and analytics engineering.",
            "Airbyte": "open-source ELT with 300+ connectors and custom connector SDK.",
            "Fivetran": "managed data integration with automated schema evolution and high reliability.",
            
            # Incident vendors
            "PagerDuty": "market-leading incident response platform with AI-driven alert routing.",
            "Opsgenie (Atlassian)": "Atlassian's on-call management with strong Jira integration.",
            "ilert": "cost-effective incident management with automation-first design.",
            "OnCall (Grafana)": "Grafana's on-call solution with tight observability integration.",
            "BigPanda": "AI-powered incident correlation and aggregation platform.",
            
            # Log vendors
            "ELK Stack": "open-source log processing with Elasticsearch, Logstash, Kibana, and community support.",
            "Splunk Cloud": "cloud-native log analysis with strong enterprise feature set.",
            "Datadog Logs": "integrated with Datadog observability for seamless correlation.",
            "Sumo Logic": "cloud-native log platform with strong security and compliance features.",
            "Loggly": "lightweight log collection and analysis for development teams.",
            
            # Synthetic vendors
            "Datadog Synthetics": "synthetic monitoring integrated with Datadog observability.",
            "New Relic Synthetics": "synthetic checks with browser and API monitoring capabilities.",
            "Pingdom": "uptime monitoring service with global check coverage.",
            "Checkly": "developer-friendly synthetic monitoring and API testing platform.",
            "StatusPage": "status page and incident communication platform with built-in monitoring.",
            
            # SIEM vendors
            "Splunk Enterprise Security": "comprehensive SIEM with threat hunting and anomaly detection.",
            "IBM QRadar": "enterprise SIEM with strong threat intelligence integration.",
            "Elastic Security": "open-source and cloud SIEM with machine learning threat detection.",
            "Microsoft Sentinel": "cloud-native SIEM with Azure and Microsoft ecosystem integration.",
            "Sumo Logic Security": "cloud-native security analytics with compliance automation.",
        }
        
        content = (
            f"{vendor} profile for {scenario.market_short}. "
            f"Key differentiators: {profiles.get(vendor, f'{vendor} offers {scenario.analysis_focus} focus')}. "
            f"Pricing typically {rng.choice(['mixes per-unit and usage-based models', 'follows consumption-based approach', 'uses tiered enterprise pricing'])}. "
            f"Strengths include {rng.choice([c for c in scenario.comparison_factors[:3]])}. "
            f"Weaknesses include {rng.choice(['complexity', 'cost sprawl at scale', 'steep learning curve'])}."
        )
        
        articles.append({
            "article_id": f"{article_id_base}_{idx:03d}",
            "title": f"{vendor} {scenario.market_short} profile",
            "content": content,
            "category": "market_research",
            "last_updated": "2026-02-20",
            "views": 80 + rng.randint(0, 60),
            "tags": [vendor, scenario.market_short, "profile"],
        })
    
    # ── Market trends article ──────────────────────────────────────────────
    trends_content = (
        f"Key trends in {scenario.market_short} include "
        f"{', '.join(scenario.key_trends[:3])}. "
        f"Buyers are scrutinizing {rng.choice(['total cost of ownership', 'deployment flexibility', 'vendor lock-in risk'])} more closely. "
        f"Vendors increasingly differentiate on {scenario.analysis_focus}."
    )
    articles.append({
        "article_id": f"{article_id_base}_trends",
        "title": f"{scenario.market_short} market trends 2026",
        "content": trends_content,
        "category": "market_research",
        "last_updated": "2026-02-22",
        "views": 120 + rng.randint(0, 40),
        "tags": ["market trends", scenario.market_short] + scenario.key_trends[:2],
    })
    
    # ── Comparison article ─────────────────────────────────────────────────
    comparison_content = (
        f"Comparing {scenario.market_short} vendors typically focuses on "
        f"{', '.join(scenario.comparison_factors[:3])}. "
        f"Differentiation factors include {', '.join(scenario.comparison_factors[3:])}. "
        f"Buyer priorities vary based on organization size, existing tool stack, and budget constraints."
    )
    articles.append({
        "article_id": f"{article_id_base}_comparison",
        "title": f"{scenario.market_short} vendor comparison framework",
        "content": comparison_content,
        "category": "market_research",
        "last_updated": "2026-02-21",
        "views": 100 + rng.randint(0, 50),
        "tags": ["comparison", scenario.market_short, "evaluation"],
    })
    
    return articles


# ---------------------------------------------------------------------------
# Task YAML and Grader builders
# ---------------------------------------------------------------------------

def build_task_yaml(task_id: str, prompt_text: str, scenario: MarketScenario) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "task_name": f"Pinbench {scenario.market_short} Market Research",
        "version": FAMILY_VERSION,
        "category": "research",
        "difficulty": "easy",
        "tags": ["general", "generated", FAMILY_ID],
        "services": [
            {
                "name": "kb",
                "command": "python mock_services/kb/server.py",
                "port": 9106,
                "health_check": "http://localhost:9106/kb/search",
                "health_check_method": "POST",
                "ready_timeout": 10,
                "reset_endpoint": "http://localhost:9106/kb/reset",
                "env": {
                    "KB_FIXTURES": f"tasks/{task_id}/fixtures/kb/articles.json",
                },
            }
        ],
        "prompt": {"text": prompt_text, "language": "en"},
        "tools": [
            {
                "name": "kb_search",
                "description": "Search the KB",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "category": {"type": "string"},
                        "max_results": {
                            "type": "integer",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "kb_get_article",
                "description": "Get one KB article",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "article_id": {"type": "string"},
                    },
                    "required": ["article_id"],
                },
            },
        ],
        "tool_endpoints": [
            {"tool_name": "kb_search", "url": "http://localhost:9106/kb/search", "method": "POST"},
            {"tool_name": "kb_get_article", "url": "http://localhost:9106/kb/articles/get", "method": "POST"},
        ],
        "sandbox_files": ["fixtures/kb/articles.json"],
        "environment": {"timeout_seconds": 300, "max_turns": 16},
        "scoring_components": [],
        "safety_checks": [
            {
                "type": "tool_not_called",
                "tool_name": "kb_update_article",
                "description": "This task is read-only.",
            }
        ],
        "expected_actions": [],
        "judge_rubric": (
            f"Reward a strategic market analysis that covers at least {scenario.min_vendors_required} "
            f"{scenario.market_short} vendors, pricing approaches, and current trends including "
            f"{scenario.key_trends[0]}. "
            f"Analysis should include competitor profiles, {', '.join(scenario.comparison_factors[:3])}, "
            f"and an executive summary with comparison table."
        ),
        "reference_solution": (
            f"Search the KB for {scenario.market_short} vendors and trends, read several articles, "
            f"then produce an executive summary, competitor profiles, and a comparison table covering "
            f"{', '.join(scenario.key_vendors[:3])}."
        ),
        "primary_dimensions": ["completion", "communication", "safety"],
    }


def render_grader(task_id: str, scenario: MarketScenario) -> str:
    required_keywords = scenario.key_vendors[:2]  # First 2 as required
    optional_keywords = scenario.key_vendors[2:] + scenario.key_trends[:2]
    
    return f'''\
from claw_eval.graders.pinbench_common import PinbenchAdaptedGrader


class Generated{scenario.market_short.replace(" ", "").replace("/", "").replace("&", "")}MarketResearchGrader(PinbenchAdaptedGrader):
    REQUIRED_TOOLS = {{"kb_search": 1, "kb_get_article": 3}}
    REQUIRED_KEYWORDS = {required_keywords!r}
    OPTIONAL_KEYWORDS = {optional_keywords!r}
    FORBIDDEN_TOOLS = ["kb_update_article"]
    REQUIRED_PATTERNS = [r"\\|.*\\|.*\\|", r"^#+\\s+"]
    MIN_FINAL_LENGTH = 1500
'''


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

PROMPT_TEMPLATES = [
    """\
Use the knowledge base to create a competitive landscape analysis of the
{market_name} market. Identify at least {min_vendors} competitors, their 
differentiators, typical pricing models, and key market trends. Include a 
comparison table and a short executive summary.""",

    """\
Conduct a market research analysis using the KB for the {market_name} 
category. You should identify {min_vendors} leading vendors, describe their 
positioning, compare pricing and feature approaches, and highlight current 
market trends. Provide a summary with a structured comparison table.""",

    """\
Using the knowledge base, analyze the {market_short} market landscape. 
Cover at least {min_vendors} major vendors, their strengths and weaknesses, 
typical pricing models, and emerging trends. Conclude with an executive 
summary and a feature/pricing comparison matrix.""",

    """\
Research the {market_name} market using available KB resources. Find 
information on {min_vendors}+ vendors, analyze their differentiation 
strategies, pricing approaches, and market trends. Synthesize findings 
into a report with executive summary and comparison table.""",
]


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
    prompt_tmpl = rng.choice(PROMPT_TEMPLATES)
    prompt_text = prompt_tmpl.format(
        market_name=scenario.market_name,
        market_short=scenario.market_short,
        min_vendors=scenario.min_vendors_required,
    )

    if task_dir.exists():
        if not force:
            raise FileExistsError(f"{task_dir} already exists; rerun with --force")
        shutil.rmtree(task_dir)

    fixtures_dir = task_dir / "fixtures" / "kb"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    # Generate KB articles
    articles = build_kb_articles(scenario, rng)
    (fixtures_dir / "articles.json").write_text(
        json.dumps(articles, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

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
        "market": scenario.market_name,
        "market_short": scenario.market_short,
        "vendors": scenario.key_vendors,
        "min_vendors_required": scenario.min_vendors_required,
        "trends": scenario.key_trends,
    }
    (task_dir / "generation_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "task_id": task_id,
        "market": scenario.market_name,
        "market_short": scenario.market_short,
        "vendors": len(scenario.key_vendors),
        "task_dir": str(task_dir),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate T095 market research KB variants")
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

    manifest_path = task_root / "generated_market_research_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Generated {len(manifest)} variants -> {manifest_path}")
    for item in manifest:
        print(f"- {item['task_id']}: {item['market_short']} ({item['vendors']} vendors)")


if __name__ == "__main__":
    main()
