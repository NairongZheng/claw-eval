# T004 Calendar Scheduling Generator

This directory contains the full generation entrypoint for the `T004_calendar_scheduling` task family.

## Files

- `generate.py`: variant generator script
- `README.md`: usage guide

## Usage

Run from the repository root:

```bash
/Users/zhengnairong/miniconda3/envs/dev/bin/python tasks_generator/T004_calendar_scheduling/generate.py --output-dir tasks --count 6 --force
```

This is the recommended mode. Generated `task.yaml` files assume tasks will finally be placed at `tasks/<task_id>/` and use `python tasks/<task_id>/local_calendar_server.py`.

You can also output elsewhere:

```bash
/Users/zhengnairong/miniconda3/envs/dev/bin/python tasks_generator/T004_calendar_scheduling/generate.py --output-dir /tmp/calendar_tasks_en --count 20
```

If you generate outside `tasks/`, move folders into `tasks/<task_id>/` before benchmark runs.

## Common arguments

- `--output-dir`: output directory for generated tasks
- `--count`: number of variants
- `--start-index`: starting task index
- `--seed`: base random seed
- `--id-prefix`: task ID prefix (default: `Tgen_T004_calendar_scheduling_gen`)
- `--force`: overwrite existing task directories

## Generated structure

Each generated task folder contains:

- `task.yaml`
- `grader.py`
- `generation_meta.json`
- `local_calendar_server.py`
- `fixtures/calendar/events.json`

## Notes

- Each generated task is standalone.
- No benchmark source modification is required.
- This mirrors the T003 generator architecture for consistent maintenance.
