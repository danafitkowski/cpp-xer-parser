# Changelog

All notable changes to `cpp-xer-parser` are documented here. Versioning follows [Semantic Versioning](https://semver.org).

---

## Unreleased

### Changed

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
