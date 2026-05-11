# cpp-xer-parser

[![license: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![status: stable](https://img.shields.io/badge/status-stable-brightgreen.svg)](CHANGELOG.md)

The canonical Primavera P6 XER file parser and generator used by every Critical Path Partners forensic deliverable.

Maintained by [Critical Path Partners](https://criticalpathpartners.ca) — a forensic-scheduling consultancy.

Companion to [`cpp-cpm-engine`](https://github.com/danafitkowski/cpp-cpm-engine).

---

## Why this parser

The XER format is fragile. Field counts shift between P6 versions. Calendar data ships inside a nested-paren mini-language. BOMs come and go without warning. Real-world exports from large programs use formats that simple split-on-tab parsers silently mangle.

This parser was built to drive court-filed forensic schedule analysis, so the bar is high: every field round-trips, calendars decode correctly, and the generator produces P6-importable output that P6 itself accepts without complaint.

---

## Install

```bash
git clone https://github.com/danafitkowski/cpp-xer-parser
cd cpp-xer-parser
# No external dependencies. Just put scripts/ on your sys.path.
```

The parser is pure Python 3.10+ with no third-party runtime dependencies.

---

## Quick start

```python
import sys
sys.path.insert(0, 'scripts')

from xer_parser import parse_xer, print_summary, get_table, build_wbs_map

# Parse
data = parse_xer('path/to/your.xer')

# Print a one-shot summary
print_summary(data)

# Drill into tables
tasks = get_table(data, 'TASK')
print(f'{len(tasks)} activities')

# Cross-reference maps
wbs = build_wbs_map(data)
for t in tasks[:3]:
    print(t['task_code'], '→', wbs[t['wbs_id']]['_full_path'])
```

---

## What it does

| Feature                              | Function                                                              |
|--------------------------------------|-----------------------------------------------------------------------|
| Parse XER to structured dict         | `parse_xer(path)`                                                     |
| Generate XER from dict               | `generate_xer(data, path, p6_version='24.12', currency='CAD', ...)`   |
| Table accessor                       | `get_table(data, 'TASK')`                                             |
| Calendar map (with holidays)         | `get_calendar_map(data)`                                              |
| WBS hierarchy with full paths        | `build_wbs_map(data)`                                                 |
| Resource assignments per task        | `build_resource_map(data)`                                            |
| Predecessor / successor maps         | `build_predecessor_map(data)`                                         |
| Activity code map                    | `build_activity_code_map(data)`                                       |
| User-defined field map               | `build_udf_map(data)`                                                 |
| Work-day count between two dates     | `get_work_days_between(start, end, calendar)`                         |
| Duration hours-to-days conversion    | `duration_hours_to_days(hours, calendar)`                             |
| Schedule integrity manifest          | `generate_xer_manifest(data, xer_path, operator)`                     |
| Schema drift between two XERs        | `schema_diff(data_a, data_b)`                                         |
| MIP 3.4 half-step XER generator      | `compute_half_step_xer(base_path, updated_path, output_path)`         |

---

## MIP 3.4 half-step XER

The most analytically interesting feature in the repo. The `compute_half_step_xer` function implements AACE 29R-03 MIP 3.4 ("Modelled / Additive / Multiple Base — Contemporaneous Split"): it takes a period-start schedule plus the next period's update, and produces a schedule that has **only the progress fields** copied from the updated schedule onto the base structure.

The forensic value: anything that moves in the half-step moved because work didn't happen as planned. Anything that moves between the half-step and the full update moved because the contractor revised logic or scope.

This closes the flagship gap in the commercial forensic-scheduling tooling market.

```python
from xer_parser import compute_half_step_xer

result = compute_half_step_xer(
    base_xer_path='period_start.xer',
    updated_xer_path='period_end.xer',
    output_xer_path='half_step.xer',
)

print(f"Matched: {result['matched_count']}")
print(f"Progressed: {result['progressed_count']}")
print(f"Activities added in updated (NOT copied): {result['unmatched_in_updated']}")
print(f"Activities removed in updated (preserved in output): {result['unmatched_in_base']}")
```

`unmatched_in_updated` is forensically significant: these are activities the contractor added between period boundaries, and they belong to the logic-revision layer, not the progress layer.

---

## XER generation rules (P6 24.12)

The generator emits P6-importable XER files following these rules:

1. **Table order**: CURRTYPE, FINTMPL, OBS, PROJECT, CALENDAR, SCHEDOPTIONS, PROJWBS, TASK, TASKPRED, then remaining tables. See the `TABLE_ORDER` constant.
2. **ERMHDR line**: `ERMHDR\t24.12\t<export_date>\tProject Management\tCAD` (or supplied currency).
3. **Field counts**: every `%R` row must have exactly the same number of fields as the `%F` definition that precedes it. The generator enforces this.
4. **Known field counts for P6 24.12**:
   - PROJECT: 72 fields
   - SCHEDOPTIONS: 26 fields
   - PROJWBS: 27 fields
   - TASK: 62 fields (includes `crt_path_num`)
   - TASKPRED: 12 fields (includes `comments`, `aref`, `arls`)
5. **Encoding**: ASCII with CRLF line endings by default. Pass `encoding='cp1252'` for strict legacy P6 compatibility with non-ASCII text.
6. **Calendar data**: when generating from scratch, copy the `clndr_data` field verbatim from a working reference XER. Re-encoding is brittle.

See `references/table-reference.md` for the complete field-by-field reference for all 40+ XER tables.

---

## Running the tests

```bash
python tests/test_xer_parser.py     # core parser + generator smoke test
python tests/test_half_step.py      # MIP 3.4 half-step generator
```

Or with pytest:

```bash
pip install pytest
pytest tests/
```

All tests build their XER fixtures synthetically in memory; no real client XER files ship with the repo.

---

## Integration with the CPP forensic suite

Inside the Critical Path Partners internal forensic suite this parser is the single source of truth for every XER operation: forensic windows analysis, monthly progress reports, 3-week field lookaheads, schedule risk Monte Carlo, time impact analysis, schedule health (DCMA-14), and claims preparation all consume `parse_xer` output. Downstream skills should:

1. Import the parser rather than writing their own XER reader.
2. Use the structured data object returned by `parse_xer()`.
3. Use the helper functions (`get_table`, `get_calendar_map`, `build_wbs_map`, etc.) rather than re-implementing cross-references.
4. Call `print_summary()` or `generate_summary()` to give the user context before diving into analysis.

`scripts/validation.py` and `scripts/config_profiles.py` are minimal standalone subsets of the same-named modules in the larger CPP internal suite — sufficient for `generate_xer_manifest`, `validate_schedule`, and `aace_31r_compliance` to run end-to-end without the full suite installed.

---

## License

MIT — see [LICENSE](LICENSE).

You may use this parser in commercial forensic consulting, in academic research, in your own scheduling product, in court-filed expert reports. Just keep the copyright notice.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports and pull requests are welcome.

---

## Companion repositories

- **[cpp-cpm-engine](https://github.com/danafitkowski/cpp-cpm-engine)** — The forensically-defensible CPM engine.
- **[cpp-critical-path-validator](https://github.com/danafitkowski/cpp-critical-path-validator)** — Critical path validation, DCMA-14 assessment, and logic health review.

---

## Strategic note

Critical Path Partners is a forensic-scheduling consultancy. We open-source the foundational tooling because every academic, every solo forensic, every contractor's internal scheduler now has a reason to install CPP and a citation pathway. The math is a commodity; the workflow and discipline are not.

If you ship something built on this parser, we'd like to hear about it: [criticalpathpartners.ca](https://criticalpathpartners.ca).
