# cpp-xer-parser

[![license: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![status: stable](https://img.shields.io/badge/status-stable-brightgreen.svg)](CHANGELOG.md)

A standalone parser and generator for Primavera P6 XER files. Pure Python 3.10+, MIT-licensed, no third-party runtime dependencies.

Maintained by [Critical Path Partners](https://criticalpathpartners.ca) — a forensic-scheduling consultancy.

Companion to [`cpp-cpm-engine`](https://github.com/danafitkowski/cpp-cpm-engine).

---

## Scope: what this is, and what it is not

**What this is.** A complete XER reader and writer. It parses every table in an export into structured Python data, builds the cross-reference maps (WBS, resources, logic, activity codes, user-defined fields), decodes calendars, and writes XER files back out in P6 24.12 table order. Every function in the feature table below is implemented in this repository. None of them is a shim that calls out to something private. Vendor it, fork it, or import it.

**What this is not.** It is not the whole toolchain Critical Path Partners runs. CPP's forensic deliverables are produced with additional validation that is kept private and is not part of this package. Named in capability terms, this package does not include:

- **A date-field validation gate.** Date fields are parsed as they appear. There is no pass that flags unparseable or implausible date values before downstream math consumes them.
- **A calendar-decode warning channel.** `parse_calendar_data` decodes the standard P6 encoding and then falls through two legacy patterns. When all of them fail it returns an empty work week rather than raising or warning, and a corrupt calendar record is not reported to the caller. Code that needs that signal has to inspect the returned structure itself.
- **Working-day arithmetic beyond `get_work_days_between` and `duration_hours_to_days`.** The additional working-day delta helper in CPP's internal parser is not included here.

None of that makes this parser wrong. It makes it smaller. If you are comparing output from this package against a report CPP produced, the difference in validation surface is the thing to ask about, and the answer is in this section rather than in a footnote.

---

## Why this parser

The XER format is fragile. Field counts shift between P6 versions. Calendar data ships inside a nested-paren mini-language. BOMs come and go without warning. Real-world exports from large programs use formats that simple split-on-tab parsers silently mangle.

It comes out of forensic schedule analysis, where a silently mangled field becomes a wrong number in a report that someone has to defend. The design goals follow from that: fields round-trip through parse and generate, the calendar encodings real exports actually use are decoded rather than guessed at, and generated files carry the field counts P6 expects on import. `tests/` is what backs those goals. Read it before relying on them.

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
| Structural validation report         | `validate_schedule(data, profile='commercial')`                       |
| Schedule structure score             | `aace_31r_compliance(data, profile='commercial')`                     |
| Schedule integrity manifest †        | `generate_xer_manifest(data, xer_path=None, **manifest_kwargs)`       |
| Schema drift between two XERs        | `schema_diff(data_a, data_b)`                                         |
| Half-step XER generator (SmartPM-equivalent) | `compute_half_step_xer(base_path, updated_path, output_path)`         |

† `validate_schedule` and `aace_31r_compliance` run from a plain clone: they use the bundled `scripts/validation.py` and `scripts/config_profiles.py`. `generate_xer_manifest` also needs CPP's internal audit-trail module, which is **not** bundled here. Without it the call raises `RuntimeError` rather than returning a manifest with missing provenance. Everything else in the table needs nothing but the standard library.

---

## Half-step XER (vendor-equivalent: SmartPM/Plannex)

The most analytically interesting feature in the repo. The `compute_half_step_xer` function implements the bifurcation procedure of AACE 29R-03 §2.3.D.2 ("Bifurcation: Creating a Progress-Only Half-Step Update" — the RP itself names the procedure "half-stepping or two-stepping"), which is how MIP 3.4 (Observational / Dynamic / Contemporaneous Split) splits each update. Vendor half-step tools (SmartPM, Plannex) are equivalents of this procedure. It takes a period-start schedule plus the next period's update, and produces a schedule that has **only the progress fields** copied from the updated schedule onto the base structure.

The forensic value: anything that moves in the half-step moved because work didn't happen as planned. Anything that moves between the half-step and the full update moved because the contractor revised logic or scope.

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

   **Open question, disclosed rather than resolved.** The parser's own version-aware validation constant (`TABLE_FIELD_COUNTS_BY_VERSION`) holds one fewer for every table in that list: PROJECT 71, SCHEDOPTIONS 25, PROJWBS 26, TASK 61, TASKPRED 11. A file matching the numbers above therefore draws an `XER-FIELD-COUNT` warning from `validate_schedule`. The code carries a standing `TODO(schema-truth)` saying the same thing. Both sets have plausible lineage, neither has been re-checked against a fresh P6 24.12 export, and guessing would silently change validation behaviour for every consumer, so both are left as they stand and the conflict is stated here instead. If a field count matters to your work, verify it against your own export.
5. **Encoding**: ASCII with CRLF line endings by default. Pass `encoding='cp1252'` for strict legacy P6 compatibility with non-ASCII text.
6. **Calendar data**: when generating from scratch, copy the `clndr_data` field verbatim from a working reference XER. Re-encoding is brittle.

See `references/table-reference.md` for the table reference: 40 XER tables, 27 of them with a field-by-field list, and 13 less common ones (documents, roles, shifts, resource codes, risk) described at table level rather than field level.

---

## Running the tests

```bash
python tests/test_xer_parser.py               # core parser + generator smoke test
python tests/test_half_step.py                # half-step generator (SmartPM-equivalent)
python tests/test_bundled_validation_runs.py  # bundled validation stubs bind on a plain clone
```

Or with pytest:

```bash
pip install pytest
pytest tests/
```

`pytest tests/` runs 22 tests across 4 files and they all pass. CI runs the same suite on Linux, macOS and Windows against Python 3.10, 3.11 and 3.12.

All tests build their XER fixtures synthetically in memory; no real client XER files ship with the repo.

---

## Relationship to CPP's internal toolchain

Critical Path Partners keeps a larger internal parser that this package was cut from. What is published here is the parsing and generation core. What is not published is the extra validation surface listed under [Scope](#scope-what-this-is-and-what-it-is-not): the date-field gate, the calendar-decode warning channel, and the additional working-day arithmetic. Reports CPP issues are produced with the internal toolchain, not with this package on its own.

Two consequences worth being explicit about:

1. **Nothing here is a stub.** The functions in the feature table are the working implementations, and the test suite exercises them. This is a smaller parser, not a demonstration copy.
2. **If you are auditing a CPP deliverable**, this repository shows you the parsing and generation logic behind it, and the Scope section tells you what else ran that you cannot see here. Ask about the difference rather than inferring it.

`scripts/validation.py` and `scripts/config_profiles.py` are minimal standalone subsets of the same-named modules in the larger internal suite: enough for `validate_schedule` and `aace_31r_compliance` to run end-to-end from a plain clone. `generate_xer_manifest` additionally needs the internal audit-trail module, which is not bundled; see the note under the feature table.

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
