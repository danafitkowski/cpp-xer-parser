# Changelog

All notable changes to `cpp-xer-parser` are documented here. Versioning follows [Semantic Versioning](https://semver.org).

---

## Unreleased

### Added

- **A blank activity calendar id is read as the project calendar.** MPXJ, converting an MS Project file, writes `TASK.clndr_id` empty for every task without a task-level calendar, and MS Project schedules such a task on the project calendar. A lookup on the blank id found no calendar. `generate_summary` then converted those activities' float at a flat 8 h/day, and `cpp-cpm-engine`, handed the rows without a project calendar, scheduled them on a continuous seven-day week. Three functions are new:
  - `resolve_task_calendars(data)` gives the calendar every TASK row is scheduled on, through the chain `TASK.clndr_id` → `PROJECT.clndr_id` of the row's project → the `default_flag = 'Y'` calendar. It lists every row left with no usable calendar: blank with nothing to fall back on, or naming a calendar the file does not declare. A named calendar is never replaced.
  - `with_resolved_calendars(tasks, resolution)` returns the rows carrying the resolved id. Filled rows are copies, and the parsed data is untouched.
  - `calendar_resolution_block(resolution, keep=None)` builds the disclosure block, limited to the rows a consumer works on.
- **`validate_schedule` reports activity calendars.** It raises BLOCK `XER-TASK-CALENDAR-UNRESOLVED` for TASK rows with no usable calendar, and INFO `XER-TASK-CALENDAR-FALLBACK` when blank ids resolved. A file whose TASK rows carry no calendar, and which names no project or default calendar, now draws the BLOCK, and `aace_31r_compliance` scores it accordingly.
- `generate_summary` converts float on each activity's resolved calendar.
- `get_calendar_map` entries carry the row's `default_flag`.

### Fixed

- **Calendar time slots decode in either field order.** P6 writes a slot as `(s|08:00|f|16:00)` or as `(f|16:00|s|08:00)`, and the order belongs to the calendar, not to the file or the P6 version: one genuine P6 24.12 export carries a start-first five-day calendar beside a finish-first six-day calendar. `parse_calendar_data` accepted only start-first at all three places it looks for a slot. A finish-first calendar therefore decoded to no working days, which `get_work_days_between`, `add_work_days` and `subtract_work_days` then counted as Mon-Fri, and every finish-first exception body was filed as a holiday. A finish-first seven-day calendar now counts seven days a week, and its worked exceptions are `special_workdays`. This changes output for any file carrying a finish-first calendar, from wrong to right. Three neighbouring defects in the exception decoder are fixed with it:
  - The fallback classifier looked for a time slot immediately after the serial. P6 puts line markers and whitespace between the two, so on a continuous calendar every worked exception became a holiday. It now reads each serial's own segment, up to the next serial.
  - Exception dates outside 1990-2050 were dropped. The window is now 1970-2099.
  - A date that two parse paths classified differently landed in both `holidays` and `special_workdays`. A day carrying work hours is now a working day only.

  `references/table-reference.md` documents the second slot order again (Time slots, and point 3 of the decoder notes). What this package still leaves out is unchanged and stated in the README's Scope section: there is no decode warning, and no corrupt-record screen. `tests/test_calendar_slot_order_2026_09_29.py` (14 tests, synthetic calendars) fails 10 of its 14 against the previous code; the other four pin behaviour that must not move.
- **Working-day arithmetic honours worked exception days and reads dates on their calendar day.** Five defects in `get_work_days_between`, `add_work_days` and `subtract_work_days`, each an output change:
  - `parse_calendar_data` files a worked Saturday under `special_workdays`, and all three helpers ignored it, so the day dropped out of every count and every step. They now honour it, and a holiday still wins when a date is listed as both.
  - `get_work_days_between` stripped the clock time from string inputs only. A datetime whose time of day was earlier than the start's was never reached, so Friday 17:00 to Monday 08:00 counted Friday alone, and a `date` against a `datetime` raised `TypeError`. Both dates are now read on their calendar day: Friday to Monday counts both days whatever the times.
  - A span of more than 100 years (a sentinel finish such as 9999-12-31) now returns `None`, as an unreadable date does, instead of walking millions of days to a plausible-looking count.
  - Fractional working days rounded half-to-even (0.5 to 0, 2.5 to 2). They now round half-up (0.5 to 1, 2.5 to 3), as `cpp-cpm-engine` does.
  - `add_work_days(d, 0)` returned `d` unchanged. A non-working anchor now snaps forward to the next working day, and `subtract_work_days(d, 0)` snaps backward, as the engine does.

  The docstrings of `add_work_days` and `subtract_work_days` said the opposite of what the functions do: they walk N gaps, so a task of D working days starting on ES finishes on `add_work_days(ES, D - 1)`, not `add_work_days(ES, D)`. The docstrings now say so. `get_work_days_between`, `_is_work_day`, `add_work_days` and `subtract_work_days`, and the two new helpers `_calendar_day` and `_round_half_up`, are ported from the internal parser and are AST-identical to it without docstrings and comments. The internal parser's `work_day_delta` is still not included (README, Scope). `tests/test_workday_arithmetic_2026_09_29.py` has 30 tests. The previous code cannot import `_round_half_up`; with that one name shimmed to the old rounding, 18 of the 29 tests that run without the engine fail against it. The engine-parity test runs when `cpp-cpm-engine`'s `python_reference` directory is on `sys.path` and skips otherwise.
- **`generate_xer` can no longer write a row that reads back shifted or split.** XER is tab-delimited and newline-terminated, and the writer emitted a value containing a tab or a line break as it stood: a `task_name` of `Pour<TAB>slab` read back as `task_name` `Pour` with `status_code` `slab`, and a line break split the row in two. Every emitted token (ERMHDR parts, table names, field names, cell values) now has each run of tab, CR and LF collapsed to one space by the new `_sanitize_cell`. Genuine P6 data never carries those characters, so this is a no-op on real exports; it matters for data built in code.
- **`parse_xer` keeps cells beyond the header.** A `%R` row with more cells than its `%F` line lost the extra cells without a trace. They are now kept on the record under `__extra_<column>` keys (for example `__extra_8`), as strings. Only a malformed or hand-edited row has them, and `generate_xer` writes only the declared fields.
- **`TABLE_ORDER` names the resource-code assignment table as P6 writes it.** It spelled the table `RSRCCAT`, a header no measured export writes (`references/table-reference.md` already said `RSRCRCAT`), so an `RSRCRCAT` table fell to the end of a generated file. It is now written in its slot between `RCATVAL` and `MEMOTYPE`. A phantom `RISKTYPES` entry, which duplicated `RISKTYPE` and matches no P6 table, is removed. The comment above the constant now says what the order is: a generation order P6 imports cleanly, not a canonical export order, which does not exist.
- **The summary counts LOE and WBS summary rows separately, and lists every critical activity.** Two output changes for callers of `generate_summary`: `schedule_metrics['loe_count']` now counts `TT_LOE` rows only (it counted WBS summary rows as LOE, and `print_summary` labelled the total "LOE"), and `critical_path['critical_activities']` is the complete list, where it stopped at 50 and carried a `note` key saying so; the `note` key is gone. New keys: `wbs_count`, and a work-only completion (`work_task_count`, `complete_work`, `percent_complete_work`) beside `percent_complete`, which counts milestones in both numerator and denominator and so overstates progress on a milestone-heavy schedule. `print_summary` prints both figures, names the WBS summary rows, and lists every field-count issue rather than the first ten.

  These four fixes are ported from the internal parser. `generate_xer`, `_write_table`, `_sanitize_cell` and `TABLE_ORDER` are AST-identical to it without docstrings and comments. `parse_xer`, `generate_summary` and `print_summary` differ from it only where the README's Scope section says they do (no date-field gate, no calendar-decode warnings), and by a data-date check that needs a module this repository does not ship. `tests/test_writer_and_summary_2026_09_29.py` (14 tests, synthetic) fails 13 of its 14 against the previous code.
- **`validate_schedule` and `aace_31r_compliance` now run from a plain clone**, which is what the README has always said they do. Two defects stopped them. First, the optional-import stanza pulled `audit_trail` (which does not ship in this repository) in the same `try` block as `validation` and `config_profiles` (which do), so one missing module discarded the two that were present, and both functions raised `RuntimeError` with their dependencies sitting next to them in `scripts/`. The two import groups are now separate. Second, the bundled `ValidationReport` subset carried `counts()` but not `count(severity)`, which `aace_31r_compliance` calls to score a schedule; `count()` has been added to the subset, which leaves `xer_parser.py` unchanged for the repositories that vendor it. `tests/test_bundled_validation_runs.py` pins both halves and fails against the previous code.
- **`config_profiles.py` says how a profile is passed.** Its module docstring said a caller could clone a profile dict, change it and pass it directly, through the `profile` parameter on `dcma_14_assess`. `get_profile` looks a profile up by name, so a dict raises `TypeError`. The docstring now says a profile is passed by name, and how to add one: an entry in `_PROFILES` with every key the bundled profiles carry. It also said the threshold keys are documented in the dcma14.py header, which names none of them; they are commented in this file. Three of those comments used an old DCMA numbering (Missed Tasks #13, CPLI #14, BEI an "extension") and now follow the published one (#11, #13, #14). Docstring and comments only; nothing reads them. The copy `cpp-critical-path-validator` bundles gets the same text, so the two files are identical again.

### Changed

- Seven `validate_schedule` finding messages are worded as sentences, where they used a dash (for example "No PROJECT records found in the XER. File is not a valid schedule."), matching CPP's internal parser. Check ids, severities, evidence and references are unchanged.
- **README positioning corrected.** The repository previously described itself as "the canonical Primavera P6 XER file parser and generator used by every Critical Path Partners forensic deliverable". It is not: CPP's deliverables are produced with a larger internal parser that adds validation not published here. The README now opens with a Scope section stating plainly what this package is (a standalone parser and generator, complete rather than a demonstration copy) and what it is not, naming the absent capabilities in capability terms: a date-field validation gate, a calendar-decode warning channel, and working-day arithmetic beyond `get_work_days_between` / `duration_hours_to_days`.
- `SECURITY.md` no longer claims this package "is used in production forensic delay analyses, EOT submissions, and expert-witness reports". It now describes what the package is and records that CPP's own deliverables run additional private validation.
- Table-reference claim corrected. `references/table-reference.md` documents 40 XER tables, 27 with a field-by-field list and 13 at table level. It previously read "the complete field-by-field reference for all 40+ XER tables".
- Feature table now shows the real `generate_xer_manifest(data, xer_path=None, **manifest_kwargs)` signature rather than a three-positional-argument form that raises `TypeError`, and records that the manifest needs the unbundled internal audit-trail module while the two validation entry points do not. `validate_schedule` and `aace_31r_compliance` appear in the table for the first time.
- **README field counts corrected to the measured ones.** The README's "XER generation rules" gave PROJECT 72, SCHEDOPTIONS 26, PROJWBS 27, TASK 62 and TASKPRED 12 for P6 24.12, one more than `TABLE_FIELD_COUNTS_BY_VERSION` holds for each, and an earlier unreleased edit published the disagreement as an open question. The 163 genuine exports at 23.10, 23.12 and 24.12 measured for `references/table-reference.md` settle it: 71, 25, 26, 61 and 11, as the constant already held, with `crt_path_num` the 61st TASK field at 24.12 as at 23.x. The README now gives those numbers, and the comment above the constant records the measurement in place of the `TODO(schema-truth)`. The v0.1.0 notes below carry the old figures and are left as released. The same section now also shows all nine ERMHDR fields, says the default encoding is UTF-8 (it said ASCII), calls `TABLE_ORDER` a generation order rather than an export order, and lists the `%E` marker and the cell-value rule.
- Removed the unverifiable marketing line "This closes the flagship gap in the commercial forensic-scheduling tooling market."
- The module docstring of `scripts/xer_parser.py` no longer calls the file the "Canonical Primavera P6 XER Engine" and the "single source of truth for all XER file operations across all skills".

### Testing

- `pytest tests/` is 100 tests across 10 files: the existing parser, half-step and citation-guard files, `test_bundled_validation_runs.py`, three activity-calendar files (`test_task_calendar_resolution_2026_09_18.py`, `test_calendar_resolution_block_2026_09_19.py`, `test_calendar_map_default_flag_2026_09_19.py`), and three files for the ports above (`test_calendar_slot_order_2026_09_29.py`, `test_workday_arithmetic_2026_09_29.py`, `test_writer_and_summary_2026_09_29.py`). All fixtures are synthetic. 99 pass and one skips: the engine-parity test, which runs and passes when `cpp-cpm-engine`'s `python_reference` directory is on `sys.path`. The CI workflow's direct-invocation step runs `test_bundled_validation_runs.py` as well.

### Changed (earlier, unreleased)

- Validation findings repointed to the correct AACE documents: file-validity and baseline-quality checks now cite AACE 29R-03 §2.1; profile-range checks (WBS depth, activity count) cite the CPP profile with AACE 38R-06 §3.5 (Planning Basis); missing-logic cites AACE 29R-03 §2.1.B.5 / DCMA 14-Point #1. Citations to AACE 31R-03 (a cost-estimate RP, the wrong document for these checks) and 53R-06 pinpoints (that RP has no numbered sections) were removed.
- Finding `check_id` values renamed from `AACE-31R-03-*` to `XER-*` (`XER-PROJECT-MISSING`, `XER-CALENDAR-MISSING`, `XER-WBS-DEPTH-LOW`, `XER-WBS-DEPTH-HIGH`, `XER-ACTIVITY-COUNT-LOW`, `XER-ACTIVITY-COUNT-HIGH`, `XER-NO-TASKPRED`).

---

## v0.1.0 — 2026-05-10

Initial public release. Companion to [`cpp-cpm-engine`](https://github.com/danafitkowski/cpp-cpm-engine).

### Features

- **Parse any Primavera P6 XER file** into a structured Python dict with all tables, fields, and records preserved.
- **Generate valid P6 24.12 XER files** from parsed or hand-built data. Field counts match P6 import expectations (PROJECT: 72, SCHEDOPTIONS: 26, PROJWBS: 27, TASK: 62, TASKPRED: 12).
- **Calendar decoding** including full work-week patterns, special workdays, and holidays. Handles the nested-paren and regex-fallback `clndr_data` formats that real-world P6 exports use.
- **Cross-reference maps** for WBS hierarchy (`build_wbs_map`), resource assignments (`build_resource_map`), predecessors and successors (`build_predecessor_map`), activity codes (`build_activity_code_map`), and user-defined fields (`build_udf_map`).
- **Schedule summary report** generation (`print_summary` / `generate_summary`) covering file info, project metrics, schedule metrics, critical path, relationships, calendars, resources, and data quality.
- **Half-step XER generator** (`compute_half_step_xer`) — implements the bifurcation procedure of AACE 29R-03 §2.3.D.2 ("Bifurcation: Creating a Progress-Only Half-Step Update", the RP's own name for half-stepping) as used by MIP 3.4 (Observational / Dynamic / Contemporaneous Split). Vendor half-step tools (SmartPM, Plannex) are equivalents of this procedure. Isolates progress impact from logic-revision impact across consecutive schedule updates.
- **BOM-aware encoding detection** (UTF-8 BOM / UTF-16 LE/BE BOM) — handles real-world P6 exports without manual encoding fiddling.
- **Schedule integrity manifest** (`generate_xer_manifest`) — SHA-256 source hash, parse metadata, schedule structure scoring via `aace_31r_compliance` (legacy name; the underlying checks cite AACE 29R-03, AACE 38R-06, and DCMA 14-Point). Requires the bundled `validation.py` + `config_profiles.py` stubs (included).
- **UDF type classification** (`get_udf_types`) — distinguishes text / numeric / date / start-date / finish-date UDFs.
- **Schema drift detection** (`schema_diff`) — compares two parsed XERs for added / removed / changed tables and fields.
- **Calendar exception classification** — separates `special_workdays` (Saturday work, etc.) from `holidays` so MIP 3.6 and TIA workflows can treat them correctly.
- **Unified validation report** (`validate_schedule`) producing the same `Finding` / `ValidationReport` types used throughout the CPP forensic suite.

### Testing

- 2 test files cover the parser core (`test_xer_parser.py`) and the half-step generator (`test_half_step.py`).
- All test fixtures are fully synthetic — every XER referenced in the test suite is built in-memory at test time. No real client data ships with the repo.

### Engine compatibility

Tested against `cpp-cpm-engine` v2.9.x (current as of 2026-05-16: v2.9.11+). The parse output is consumed by `cpm-engine.parseXER()` and is independent of the engine math; any `cpp-cpm-engine` 2.9.x version is compatible. Forward compatibility with future 2.x lines is intended but not guaranteed; the parse-output schema is the canonical interface contract.

### Companion repos

- **[cpp-cpm-engine](https://github.com/danafitkowski/cpp-cpm-engine)** — The CPM engine that consumes data from this parser.
- **[cpp-critical-path-validator](https://github.com/danafitkowski/cpp-critical-path-validator)** — Critical path validation built on top of this parser.
