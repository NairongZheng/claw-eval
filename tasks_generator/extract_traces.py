#!/usr/bin/env python3

"""
python extract_traces.py -i <traces_dir> -o <save_jsonl_path> --tasks-root <tasks_root_dir>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Warning: failed to parse line in {path}: {line[:100]}... ({e})")
    return items


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_trial_index(batch_results_path: Path | None) -> dict[str, dict[str, Any]]:
    if not batch_results_path or not batch_results_path.exists():
        return {}

    raw = load_json(batch_results_path)
    index: dict[str, dict[str, Any]] = {}
    for task_item in raw:
        task_id = task_item.get("task_id")
        for trial in task_item.get("trials", []):
            trace_rel = trial.get("trace")
            if trace_rel:
                index[Path(trace_rel).name] = {
                    "task_id": task_id,
                    "task_name": task_item.get("task_name"),
                    "difficulty": task_item.get("difficulty"),
                    "trial": trial,
                    "task_result": {
                        "error": task_item.get("error"),
                        "avg_score": task_item.get("avg_score"),
                        "pass_at_1": task_item.get("pass_at_1"),
                        "pass_hat_k": task_item.get("pass_hat_k"),
                        "avg_passed": task_item.get("avg_passed"),
                    },
                }
    return index


def resolve_task_yaml(task_id: str, tasks_roots: list[Path]) -> Path | None:
    for root in tasks_roots:
        candidate = root / task_id / "task.yaml"
        if candidate.exists():
            return candidate
    return None


def convert_task_tools(task_yaml: dict[str, Any]) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for tool in task_yaml.get("tools", []):
        converted.append(
            {
                "type": "function",
                "function": {
                    "name": tool.get("name"),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
                },
            }
        )
    return converted


def tool_call_from_block(block: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": block.get("id"),
        "type": "function",
        "function": {
            "name": block.get("name"),
            "arguments": block.get("input", {}),
        },
    }


def normalize_text_content(content_blocks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for block in content_blocks:
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)


def convert_trace_messages(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    messages: list[dict[str, Any]] = []
    enable_thinking = False

    for event in events:
        if event.get("type") != "message":
            continue

        msg = event.get("message", {})
        role = msg.get("role")
        content_blocks = msg.get("content", []) or []
        reasoning = msg.get("reasoning_content")
        if reasoning:
            enable_thinking = True

        text_content = normalize_text_content(content_blocks)
        tool_use_blocks = [block for block in content_blocks if block.get("type") == "tool_use"]
        tool_result_blocks = [block for block in content_blocks if block.get("type") == "tool_result"]

        if role == "assistant":
            out: dict[str, Any] = {
                "role": "assistant",
                "content": text_content,
            }
            if tool_use_blocks:
                out["tool_calls"] = [tool_call_from_block(block) for block in tool_use_blocks]
            if reasoning is not None:
                out["reasoning_content"] = reasoning
            messages.append(out)
            continue

        if role == "user" and tool_result_blocks:
            for block in tool_result_blocks:
                tool_text_parts: list[str] = []
                for sub in block.get("content", []) or []:
                    if sub.get("type") == "text":
                        tool_text_parts.append(sub.get("text", ""))
                messages.append(
                    {
                        "role": "tool",
                        "name": _infer_tool_name_from_id(block.get("tool_use_id"), messages),
                        "tool_call_id": block.get("tool_use_id"),
                        "content": "".join(tool_text_parts),
                        "success": not bool(block.get("is_error", False)),
                    }
                )
            continue

        out_user: dict[str, Any] = {
            "role": role,
            "content": text_content,
        }
        if reasoning is not None:
            out_user["reasoning_content"] = reasoning
        messages.append(out_user)

    return messages, enable_thinking


def _infer_tool_name_from_id(tool_call_id: str | None, messages: list[dict[str, Any]]) -> str | None:
    if not tool_call_id:
        return None
    for message in reversed(messages):
        if message.get("role") != "assistant":
            continue
        for tool_call in message.get("tool_calls", []) or []:
            if tool_call.get("id") == tool_call_id:
                return ((tool_call.get("function") or {}).get("name"))
    return None


def extract_trace_metadata(events: list[dict[str, Any]]) -> dict[str, Any]:
    trace_start = next((event for event in events if event.get("type") == "trace_start"), {})
    trace_end = next((event for event in events if event.get("type") == "trace_end"), {})
    grading_result = next((event for event in reversed(events) if event.get("type") == "grading_result"), {})
    audits = [event for event in events if event.get("type") == "audit_snapshot"]

    return {
        "trace_start": trace_start,
        "trace_end": trace_end,
        "grading_result": grading_result,
        # "audit_snapshots": audits,
    }


def build_output_record(
    trace_path: Path,
    events: list[dict[str, Any]],
    task_yaml: dict[str, Any] | None,
    batch_trial_info: dict[str, Any] | None,
    batch_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    messages, enable_thinking = convert_trace_messages(events)
    meta = extract_trace_metadata(events)
    trace_start = meta["trace_start"]
    trace_end = meta["trace_end"]
    grading_result = meta["grading_result"]

    task_id = trace_start.get("task_id") or (batch_trial_info or {}).get("task_id")
    task_tools = convert_task_tools(task_yaml or {})
    total_steps = len(messages)

    trial = (batch_trial_info or {}).get("trial", {})
    task_result = (batch_trial_info or {}).get("task_result", {})

    metadata = {
        "source_trace": str(trace_path),
        "trace_file": trace_path.name,
        "task_id": task_id,
        "task_name": (task_yaml or {}).get("task_name") or (batch_trial_info or {}).get("task_name"),
        "model": trace_start.get("model"),
        "persona": trace_start.get("persona"),
        "trace_id": trace_start.get("trace_id"),
        "timestamps": {
            "started_at": trace_start.get("timestamp"),
            "ended_at": trace_end.get("timestamp"),
        },
        "score": {
            "task_score": _first_non_none(grading_result.get("task_score"), trace_end.get("task_score"), trial.get("task_score"), task_result.get("avg_score")),
            "passed": _first_non_none(grading_result.get("passed"), trace_end.get("passed"), trial.get("passed"), task_result.get("avg_passed")),
            "scores": _first_non_none(grading_result.get("scores"), trace_end.get("scores"), {
                "completion": trial.get("completion"),
                "robustness": trial.get("robustness"),
                "communication": trial.get("communication"),
                "safety": trial.get("safety"),
            }),
        },
        "usage": {
            "model_input_tokens": _first_non_none(trace_end.get("model_input_tokens"), trial.get("model_input_tokens")),
            "model_output_tokens": _first_non_none(trace_end.get("model_output_tokens"), trial.get("model_output_tokens")),
            "input_tokens": _first_non_none(trace_end.get("input_tokens"), trial.get("input_tokens")),
            "output_tokens": _first_non_none(trace_end.get("output_tokens"), trial.get("output_tokens")),
            "total_tokens": _first_non_none(trace_end.get("total_tokens"), trial.get("tokens")),
        },
        "timing": {
            "model_time_s": _first_non_none(trace_end.get("model_time_s"), trial.get("model_time_s")),
            "tool_time_s": _first_non_none(trace_end.get("tool_time_s"), trial.get("tool_time_s")),
            "other_time_s": _first_non_none(trace_end.get("other_time_s"), trial.get("other_time_s")),
            "wall_time_s": _first_non_none(trace_end.get("wall_time_s"), trial.get("wall_time_s")),
        },
        "task": {
            "difficulty": (task_yaml or {}).get("difficulty") or (batch_trial_info or {}).get("difficulty"),
            "category": (task_yaml or {}).get("category"),
            "tags": (task_yaml or {}).get("tags", []),
            "prompt": (task_yaml or {}).get("prompt", {}),
            "services": (task_yaml or {}).get("services", []),
            "tool_endpoints": (task_yaml or {}).get("tool_endpoints", []),
            "environment": (task_yaml or {}).get("environment", {}),
        },
        # "batch": {
        #     "summary": batch_summary or {},
        #     "trial": trial,
        #     "task_result": task_result,
        # },
        "raw": {
            "trace_start": trace_start,
            "trace_end": trace_end,
            "grading_result": grading_result,
            # "audit_snapshots": meta["audit_snapshots"],
        },
    }

    return {
        "status": "completed" if not task_result.get("error") else "error",
        "total_steps": total_steps,
        "enable_thinking": enable_thinking,
        "messages": messages,
        "tools": task_tools,
        "metadata": metadata,
    }


def _first_non_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def collect_trace_files(trace_dir: Path) -> list[Path]:
    return sorted(path for path in trace_dir.glob("*.jsonl") if path.is_file())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract benchmark traces into unified JSON/JSONL records")
    parser.add_argument("-i", "--trace_dir", help="Directory containing trace .jsonl files and optional batch_results.json")
    parser.add_argument("-o", "--output", help="Output file path. Defaults to <trace_dir>/extracted_traces.jsonl")
    parser.add_argument("--format", choices=["jsonl", "json"], default="jsonl")
    parser.add_argument(
        "--tasks-root",
        action="append",
        default=[],
        help="Task root to search for task.yaml. Can be specified multiple times. Defaults to ./tasks and ./tasks_test",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    trace_dir = Path(args.trace_dir).resolve()
    if not trace_dir.exists():
        raise SystemExit(f"Trace dir not found: {trace_dir}")

    default_tasks_roots = [Path("tasks").resolve(), Path("tasks_test").resolve()]
    tasks_roots = [Path(path).resolve() for path in args.tasks_root] if args.tasks_root else default_tasks_roots

    batch_results_path = trace_dir / "batch_results.json"
    batch_summary_path = trace_dir / "batch_summary.json"
    batch_trial_index = build_trial_index(batch_results_path)
    batch_summary = load_json(batch_summary_path) if batch_summary_path.exists() else None

    records: list[dict[str, Any]] = []
    missing_task_yaml: list[str] = []

    for trace_path in collect_trace_files(trace_dir):
        events = load_jsonl(trace_path)
        trace_start = next((event for event in events if event.get("type") == "trace_start"), {})
        task_id = trace_start.get("task_id") or (batch_trial_index.get(trace_path.name, {}).get("task_id"))
        task_yaml_path = resolve_task_yaml(task_id, tasks_roots) if task_id else None
        task_yaml = load_yaml(task_yaml_path) if task_yaml_path else None
        if task_id and task_yaml_path is None:
            missing_task_yaml.append(task_id)

        records.append(
            build_output_record(
                trace_path=trace_path,
                events=events,
                task_yaml=task_yaml,
                batch_trial_info=batch_trial_index.get(trace_path.name),
                batch_summary=batch_summary,
            )
        )

    output_path = Path(args.output).resolve() if args.output else trace_dir / f"extracted_traces.{args.format}"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "jsonl":
        with output_path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    else:
        output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Extracted {len(records)} traces -> {output_path}")
    if missing_task_yaml:
        unique_missing = sorted(set(missing_task_yaml))
        print(f"Warning: missing task.yaml for {len(unique_missing)} task(s): {', '.join(unique_missing)}")


if __name__ == "__main__":
    main()
