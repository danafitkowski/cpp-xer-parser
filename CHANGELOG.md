# Changelog

All notable changes to `cpp-xer-parser` are documented here. Versioning follows [Semantic Versioning](https://semver.org).

---

## v0.1.0 — 2026-05-10

Initial public release. Companion to [`cpp-cpm-engine`](https://github.com/danafitkowski/cpp-cpm-engine).

### Features

- **Parse any Primavera P6 XER file** into a structured Python dict with all tables, fields, and records preserved.
- **Generate valid P6 24.12 XER files** from parsed or hand-built data. Field counts match P6 import expectations (PROJECT: 72, SCHEDOPTIONS: 26, PROJWBS: 27, TASK: 62, TASKPRED: 12).
- **Calendar decoding** including full work-week patterns, special workdays, and holidays. Handles the nested-paren and regex-fallback `clndr_data` formats that real-world P6 exports use.
- **Cross-reference maps** for WBS hierarchy (`build_wbs_map`), resource assignments (`build_resource_map`), predecessors and successors (`build_predecessor_map`), activity codes (`build_activity_code_map`), and user-defined fields (`build_udf_map`).
- **Schedule summary report** generation (`print_summary` / `generate_summary`) covering file info, project metrics, schedule metrics, critical path, relationships, calendars, resources, and data quality.
- **MIP 3.4 half-step XER generator** (`compute_half_step_xer`) — AACE 29R-03 MIP 3.4 ("Modelled / Additive / Multiple Base — Contemporaneous Split"). Isolates progress impact from logic-revision impact across consecutive schedule updates.
- **BOM-aware encoding detection** (UTF-8 BOM / UTF-16 LE/BE BOM) — handles real-world P6 exports without manual encoding fiddling.
- **Schedule integrity manifest** (`generate_xer_manifest`) — SHA-256 source hash, parse metadata, AACE 31R-03 compliance scoring. Requires the bundled `validation.py` + `config_profiles.py` stubs (included).
- **UDF type classification** (`get_udf_types`) — distinguishes text / numeric / date / start-date / finish-date UDFs.
- **Schema drift detection** (`schema_diff`) — compares two parsed XERs for added / removed / changed tables and fields.
- **Calendar exception classification** — separates `special_workdays` (Saturday work, etc.) from `holidays` so MIP 3.6 and TIA workflows can treat them correctly.
- **Unified validation report** (`validate_schedule`) producing the same `Finding` / `ValidationReport` types used throughout the CPP forensic suite.

### Testing

- 2 test files cover the parser core (`test_xer_parser.py`) and the MIP 3.4 half-step generator (`test_half_step.py`).
- All test fixtures are fully synthetic — every XER referenced in the test suite is built in-memory at test time. No real client data ships with the repo.

### Companion repos

- **[cpp-cpm-engine](https://github.com/danafitkowski/cpp-cpm-engine)** — The CPM engine that consumes data from this parser.
- **[cpp-critical-path-validator](https://github.com/danafitkowski/cpp-critical-path-validator)** — Critical path validation built on top of this parser.
