# T030 Cross-Service Meeting Generator

用于批量生成 `T030_cross_service_meeting` 英文变体任务。

## Usage

Run from repo root:

```bash
/Users/zhengnairong/miniconda3/envs/dev/bin/python tasks_generator/T030_cross_service_meeting/generate.py --output-dir tasks --count 10 --force
```

## Common flags

- `--output-dir`: output directory (default: `tasks`)
- `--count`: number of variants
- `--start-index`: starting index
- `--seed`: random seed
- `--id-prefix`: task prefix (default: `Tgen_T030_cross_service_meeting_gen`)
- `--force`: overwrite existing folders

## Outputs

Each generated task contains:

- `task.yaml`
- `grader.py` (standalone)
- `generation_meta.json`
- `fixtures/gmail/inbox.json`
- `fixtures/contacts/contacts.json`
- `fixtures/calendar/events.json`

## Diversity model (structural, not cosmetic)

The generator varies constraint structure across scenarios:

- Meeting duration: 60 / 90 / 120 minutes
- Time granularity: supports minute-level slots (e.g., 13:30-15:00)
- Conflict topology: different engineering/product busy windows
- Location constraints: room vs online requirements
- Reply obligations: some scenarios require an explicit fallback slot in email reply

> Note: `task.yaml` references `tasks/<task_id>/fixtures/...` by benchmark convention. If generated elsewhere first, move tasks under `tasks/<task_id>/` before evaluation.
