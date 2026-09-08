# P6 XER Table and Field Reference

Every field list, field count, table name and code value in this file was read out of
real Primavera P6 exports. Nothing here is transcribed from a schema document or
reconstructed from memory.

## Measurement basis

| Item | Measured |
|------|----------|
| XER files scanned | 199 |
| Files with a full-size Oracle field layout (TASK 61 or 66 fields, PROJECT 71 or 82) | 174 |
| Files kept as ground truth | 166 |
| ERMHDR versions in the ground-truth set | 19.12 (3 files), 23.10 (4), 23.12 (109), 24.12 (50) |
| Distinct tables observed | 32 |
| Distinct field names observed | 367 |
| CALENDAR records, all with a populated `clndr_data` | 523 |
| TASKPRED rows | 148,946 |

A file is kept as ground truth when all four hold:

1. ERMHDR names an Oracle database and module: `dbxDatabaseNoName` and
   `Project Management`.
2. The exporting user is a real person, not a synthetic or demo identity.
3. TASK and PROJECT carry a full-size Oracle row shape.
4. The file looks written by P6 rather than by a tool: ERMHDR carries a bare
   `YYYY-MM-DD` export date, and the file emits a CURRTYPE table. Every P6 export
   does both. Two files in the scanned set pass the first three tests and fail
   this one, timestamping the header and omitting CURRTYPE, and both are import
   files built by a generator. They are excluded.

Field lists are the exact `%F` header lines from those files, in the exact order P6
writes them. Where a table's layout differs by version, the difference is stated in
that table's section.

The 24.12 layout is measured, not assumed: 50 genuine 24.12 exports are in the set.
23.12 and 24.12 share 18 tables. On 16 of them the `%F` lines are identical in field
names, field count and column order. Two differ: RSRC and TASKRSRC, where 24.12
reshuffles the tail. Each is noted in its own section.

**No P6 22.x export is in the set.** Every count and field list below is measured at
19.12, 23.10, 23.12 and 24.12 only. Nothing here is a claim about 22.x. Where this
file says "the current family" it means 23.10, 23.12 and 24.12.

Eleven further P6 tables are named at the end of this file with no field list,
because none of them appears in the measured set. They are listed so a parser
author knows the catalogue is not closed, not so anyone can quote their fields.

---

## Export order (measured, not canonical)

There is no single canonical export order. The 166 ground-truth exports produced
**38 distinct `%T` sequences**. What holds is a stable set of ordering *rules*, plus
several placements that genuinely vary.

**Stable in every file where both tables appear:**

| Rule | Measured |
|------|----------|
| CURRTYPE is the first table | 166/166 |
| CURRTYPE, OBS and FINTMPL all before PROJECT | 166/166, 166/166, 163/163 |
| PROJECT before CALENDAR | 166/166 |
| PROJECT before PROJWBS | 166/166 |
| CALENDAR before SCHEDOPTIONS | 143/143 |
| SCHEDOPTIONS before PROJWBS | 143/143 |
| PROJWBS before TASK | 166/166 |
| TASK before TASKPRED | 162/162 |
| ACTVCODE after TASK | 88/88 (never before) |
| TASKPRED before TASKRSRC | 16/16 |
| TASKPRED before TASKACTV | 47/47 |

**Not stable, so never assert it in a parser:**

| Pair | Measured |
|------|----------|
| UDFTYPE before PROJECT | 52 of 71 files |
| ACTVTYPE before TASK | 57 of 88 |
| TASKMEMO before TASKPRED | 33 of 52 |
| MEMOTYPE before PROJECT | 33 of 53 |
| PCATTYPE before PROJECT | 11 of 15 |
| RSRC before TASK | 7 of 10 |
| UDFVALUE is the last table in the file | 60 of 69 |
| SCHEDOPTIONS present at all | 143 of 166 (23 genuine exports omit it entirely) |

**The single most common exact sequence** is 9 tables long and appears in 28 of the
166 files (23 at 23.12, 5 at 24.12):

```
CURRTYPE, FINTMPL, OBS, PROJECT, CALENDAR, SCHEDOPTIONS, PROJWBS, TASK, TASKPRED
```

The next three most common are 19 files (adds MEMOTYPE, ACTVTYPE, ACTVCODE,
TASKMEMO), 14 files (adds UDFTYPE, UDFVALUE) and 11 files (ACTVTYPE and ACTVCODE
*after* TASKPRED). No sequence covers even a fifth of the set.

**Overall shape.** Grouping the 32 tables by where they tend to fall, measured as
each table's mean position across the files that contain it, an export reads roughly:

```
definition tables   CURRTYPE, NONWORK, FINTMPL, RCATTYPE, OBS, RISKTYPE,
                    RSRCCURVDATA, RCATVAL
project header      PROJECT, ROLES, PCATTYPE, ROLERATE, UDFTYPE, CALENDAR,
                    MEMOTYPE, PCATVAL, SCHEDOPTIONS
structure           PROJWBS, PROJPCAT
codes and resources ACTVTYPE, RSRC, RSRCRATE
activities          TASK, RSRCRCAT, WBSSTEP, ACTVCODE, RSRCROLE
activity children   TASKPRED, TASKACTV, TASKMEMO, TASKRSRC
values              UDFVALUE
```

That is a reading aid, not a rule, and the order *within* a group means nothing.
CALENDAR and UDFTYPE sit 0.002 apart on the scale, close enough that dropping two
files from the set swaps them. Tables carried by only a handful of files, ROLES in
7, PCATTYPE in 15, ROLERATE and RSRCRCAT in 1 each, are placed on very little
evidence. The two rule tables above are the only part of this section a parser
should rely on.

The safe parser rule: read the whole file into a table map first, then resolve
cross-references. Do not build a single-pass parser that assumes a parent table
has already been seen.

---

## Table of Contents

The 32 tables observed in the measured set, in the approximate order they tend to
appear. Real files vary: see Export order above before relying on any sequence.

1. [CURRTYPE — Currencies](#currtype)
2. [NONWORK — Non-Work Types](#nonwork)
3. [FINTMPL — Financial Period Templates](#fintmpl)
4. [RCATTYPE — Resource Code Types](#rcattype)
5. [OBS — Organizational Breakdown Structure](#obs)
6. [RISKTYPE — Risk Categories](#risktype)
7. [RSRCCURVDATA — Resource Curves](#rsrccurvdata)
8. [RCATVAL — Resource Code Values](#rcatval)
9. [PROJECT — Project Header](#project)
10. [ROLES — Roles](#roles)
11. [PCATTYPE — Project Code Types](#pcattype)
12. [ROLERATE — Role Rates](#rolerate)
13. [CALENDAR — Work Calendars](#calendar)
14. [UDFTYPE — User Defined Field Types](#udftype)
15. [MEMOTYPE — Notebook Topics](#memotype)
16. [PCATVAL — Project Code Values](#pcatval)
17. [SCHEDOPTIONS — Scheduling Options](#schedoptions)
18. [PROJWBS — Work Breakdown Structure](#projwbs)
19. [PROJPCAT — Project Code Assignments](#projpcat)
20. [ACTVTYPE — Activity Code Types](#actvtype)
21. [RSRC — Resources](#rsrc)
22. [RSRCRATE — Resource Rates](#rsrcrate)
23. [TASK — Activities](#task)
24. [RSRCRCAT — Resource Code Assignments](#rsrcrcat)
25. [WBSSTEP — WBS Steps](#wbsstep)
26. [ACTVCODE — Activity Code Values](#actvcode)
27. [RSRCROLE — Resource Role Assignments](#rsrcrole)
28. [TASKPRED — Relationships / Logic Ties](#taskpred)
29. [TASKACTV — Task Activity Code Assignments](#taskactv)
30. [TASKMEMO — Activity Notebooks](#taskmemo)
31. [TASKRSRC — Resource Assignments](#taskrsrc)
32. [UDFVALUE — User Defined Field Values](#udfvalue)

Then: [P6 tables not present in the measured set](#unmeasured) and
[Parsing Pitfalls](#pitfalls).

---

<a name="currtype"></a>
## CURRTYPE — Currencies

Currency definitions used in the project. 11 fields in every measured version
(19.12, 23.10, 23.12, 24.12).

| Field | Description | Key Use |
|-------|-------------|---------|
| curr_id | Internal currency ID | Cross-ref from PROJECT and RSRC |
| decimal_digit_cnt | Decimal places | |
| curr_symbol | Symbol ($, £, etc.) | |
| decimal_symbol | Decimal separator | |
| digit_group_symbol | Thousands separator | |
| pos_curr_fmt_type | Positive format mask (e.g. `#1.1`) | |
| neg_curr_fmt_type | Negative format mask (e.g. `(#1.1)`) | |
| curr_type | **Full currency name** (e.g. `CAD DOLLAR`, `Pound Sterling`) | **Display name** |
| curr_short_name | Currency code (e.g. CAD, USD) | Matching |
| group_digit_cnt | Digits per thousands group (3 in every row measured) | |
| base_exch_rate | Exchange rate to base currency | Cost conversion |

There is no `curr_name` field. The full name lives in `curr_type`.

---

<a name="nonwork"></a>
## NONWORK — Non-Work Types

Timesheet non-work categories. Present in 3 of 166 files, all 19.12. 4 fields.

| Field | Description |
|-------|-------------|
| nonwork_type_id | Non-work type ID |
| seq_num | Sort order |
| nonwork_code | Short code |
| nonwork_type | Type name |

---

<a name="fintmpl"></a>
## FINTMPL — Financial Period Templates

Financial period templates for earned value and cost tracking. 3 fields.
Present in 163 of 166 files: every 23.10, 23.12 and 24.12 export, and none of the
three 19.12 exports.

| Field | Description |
|-------|-------------|
| fintmpl_id | Template ID |
| fintmpl_name | Template name (e.g. `Calendar`) |
| default_flag | Y/N default template |

---

<a name="rcattype"></a>
## RCATTYPE — Resource Code Types

Resource code categories. Present in 1 of 166 files (23.12). 5 fields.

| Field | Description |
|-------|-------------|
| rsrc_catg_type_id | Type ID |
| seq_num | Sort order |
| rsrc_catg_short_len | Short code length |
| rsrc_catg_type | Type name |
| export_flag | Include on export |

---

<a name="obs"></a>
## OBS — Organizational Breakdown Structure

Responsibility tree. 6 fields in every measured version.

| Field | Description | Key Use |
|-------|-------------|---------|
| obs_id | OBS node ID | Cross-ref from PROJWBS |
| parent_obs_id | Parent node | Hierarchy building |
| guid | Global unique ID | |
| seq_num | Sort order | Display order |
| obs_name | Node name | Responsibility reporting |
| obs_descr | Node description | Often an HTML fragment, not plain text |

There is no `obs_short_name` field. The description field is `obs_descr`, and P6
frequently writes a full HTML document into it, so strip markup before displaying.

---

<a name="risktype"></a>
## RISKTYPE — Risk Categories

Risk category tree. Present in 3 of 166 files, all 19.12. 4 fields.

| Field | Description |
|-------|-------------|
| risk_type_id | Category ID |
| seq_num | Sort order |
| risk_type | Category name |
| parent_risk_type_id | Parent category |

---

<a name="rsrccurvdata"></a>
## RSRCCURVDATA — Resource Curves

Resource distribution curves referenced by TASKRSRC. Present in 6 of 166 files
(19.12 and 23.12). 24 fields.

| Field | Description |
|-------|-------------|
| curv_id | Curve ID |
| curv_name | Curve name |
| default_flag | Y/N default curve |
| pct_usage_0 … pct_usage_20 | 21 percentage points defining the curve shape |

`pct_usage_0` through `pct_usage_20` are 21 separate columns, not an array.

---

<a name="rcatval"></a>
## RCATVAL — Resource Code Values

Values under a resource code type. Present in 1 of 166 files (23.12). 6 fields.

| Field | Description |
|-------|-------------|
| rsrc_catg_id | Value ID |
| rsrc_catg_type_id | Type reference |
| seq_num | Sort order |
| rsrc_catg_short_name | Short code |
| rsrc_catg_name | Description |
| parent_rsrc_catg_id | Parent value (hierarchy) |

---

<a name="project"></a>
## PROJECT — Project Header (71 fields in 23.10 / 23.12 / 24.12)

Project-level metadata. The most field-heavy table in every export measured.

19.12 carries 82 fields: the 71 below minus `fintmpl_id`, plus `matrix_id`,
`last_level_date`, `px_last_update_date`, `px_priority`, `hist_interval`,
`hist_level`, `control_updates_flag`, `px_enable_publication_flag`,
`schedule_type`, `sync_wbs_heir_flag`, `sched_wbs_heir_type`, `wbs_heir_levels`.

| Field | Description | Key Use |
|-------|-------------|---------|
| proj_id | Internal project ID | Cross-reference everywhere |
| fy_start_month_num | Fiscal year start month | |
| rsrc_self_add_flag | Resources may add themselves | |
| allow_complete_flag | Allow activities past 100% | |
| rsrc_multi_assign_flag | One resource may take multiple assignments on an activity | |
| checkout_flag | Project is checked out | |
| project_flag | Row is a project, not an EPS node | Filtering the real project row |
| step_complete_flag | Activity % complete driven by steps | |
| cost_qty_recalc_flag | Recalculate costs from quantities | |
| batch_sum_flag | Included in batch summarization | |
| name_sep_char | WBS code separator character | **Rebuilding WBS paths** |
| def_complete_pct_type | Default % complete type | Measured: CP_Drtn, CP_Phys |
| proj_short_name | Project code/name | **Display name** |
| acct_id | Default cost account | |
| orig_proj_id | Project this one was copied from | Provenance |
| source_proj_id | Source project of a baseline copy | Baseline provenance |
| base_type_id | Baseline type | |
| clndr_id | Project default calendar | Duration conversion fallback |
| sum_base_proj_id | Baseline project ID | Baseline cross-reference |
| task_code_base | Activity ID numbering base | |
| task_code_step | Activity ID increment | |
| priority_num | Project leveling priority | Leveling |
| wbs_max_sum_level | WBS summary max level | |
| strgy_priority_num | Strategic priority | |
| last_checksum | Internal checksum | |
| critical_drtn_hr_cnt | **Critical float threshold (hours)** | **What P6 calls critical** |
| def_cost_per_qty | Default cost per unit | |
| last_recalc_date | **Data date / status date** | **Most critical date in schedule** |
| plan_start_date | Project planned start | Baseline reference |
| plan_end_date | Project must-finish date | Contractual deadline |
| scd_end_date | Scheduled finish (calculated) | CPM-calculated finish |
| add_date | Project created | Audit trail |
| last_tasksum_date | Last summary calculation | |
| fcst_start_date | Forecast start | |
| def_duration_type | Default duration type | Measured: DT_FixedDrtn, DT_FixedQty, DT_FixedRate |
| task_code_prefix | Activity ID prefix | |
| guid | Global unique ID | Matching across exports |
| def_qty_type | Default quantity type | Measured: QT_Hour, QT_Day |
| add_by_name | Created by | Audit trail |
| web_local_root_path | Document root path | |
| proj_url | Project URL / free-text note field | |
| def_rate_type | Default price-per-unit rate | Measured: COST_PER_QTY |
| add_act_remain_flag | Actual plus remaining equals at-completion | |
| act_this_per_link_flag | Link actual-this-period to actual-to-date | |
| def_task_type | Default activity type | Measured: TT_Task |
| act_pct_link_flag | Link % complete to actuals | |
| critical_path_type | **How P6 flags critical** | **Measured: CT_TotFloat, CT_DrivPath. Read this before trusting total float** |
| task_code_prefix_flag | Auto-number new activities | |
| def_rollup_dates_flag | Roll up assignment dates | |
| use_project_baseline_flag | Use project baseline for earned value | |
| rem_target_link_flag | Link remaining duration to original duration | |
| reset_planned_flag | Reset planned to remaining | |
| allow_neg_act_flag | Allow negative actual units | |
| sum_assign_level | Summary assignment level | |
| last_fin_dates_id | Financial period reference | |
| fintmpl_id | Financial period template (absent in 19.12) | |
| last_baseline_update_date | Last baseline update | Baseline audit trail |
| cr_external_key | External key | |
| apply_actuals_date | Last apply-actuals run | Audit trail |
| location_id | Project location | |
| last_schedule_date | **Last time the project was scheduled** | **Audit trail. This is not a leveling date** |
| loaded_scope_level | Loaded scope level | |
| export_flag | Include on export | |
| new_fin_dates_id | Financial period for the next store-period-performance | |
| baselines_to_export | Baselines selected for export | |
| baseline_names_to_export | Names of the baselines selected for export | |
| next_data_date | Next planned data date | Update cycle |
| close_period_flag | Financial period closed | |
| sum_refresh_date | Last summarizer refresh | |
| trsrcsum_loaded | Resource assignment summaries present | |
| sumtask_loaded | Activity summaries present | |

There is no `sum_data_date`, no `def_cost_per_qty_link_flag`, and no
`last_level_date` in the 23.10, 23.12 or 24.12 layout. `last_level_date` exists
only in 19.12.

---

<a name="roles"></a>
## ROLES — Roles

Present in 7 of 166 files (19.12 and 23.12). 10 fields.

| Field | Description |
|-------|-------------|
| role_id | Role ID |
| parent_role_id | Parent role (hierarchy) |
| seq_num | Sort order |
| role_name | Role name |
| role_short_name | Role code |
| pobs_id | Owning OBS node |
| def_cost_qty_link_flag | Link cost to quantity by default |
| cost_qty_type | Default quantity type |
| role_descr | Description |
| last_checksum | Internal checksum |

---

<a name="pcattype"></a>
## PCATTYPE — Project Code Types

Present in 15 of 166 files. 5 fields in 23.10 and 23.12; 4 in 19.12 (no
`export_flag`). No 24.12 export in the set carries it.

| Field | Description |
|-------|-------------|
| proj_catg_type_id | Type ID |
| seq_num | Sort order |
| proj_catg_short_len | Short code length |
| proj_catg_type | Type name |
| export_flag | Include on export (absent in 19.12) |

---

<a name="rolerate"></a>
## ROLERATE — Role Rates

Present in 1 of 166 files (23.12). 9 fields.

| Field | Description |
|-------|-------------|
| role_rate_id | Rate record ID |
| role_id | Role reference |
| cost_per_qty | Rate 1 |
| cost_per_qty2 | Rate 2 |
| cost_per_qty3 | Rate 3 |
| cost_per_qty4 | Rate 4 |
| cost_per_qty5 | Rate 5 |
| start_date | Rate effective date |
| max_qty_per_hr | Max quantity per hour |

---

<a name="calendar"></a>
## CALENDAR — Work Calendars

13 fields in every measured version.

| Field | Description | Key Use |
|-------|-------------|---------|
| clndr_id | Calendar ID | Cross-ref from TASK |
| default_flag | Default calendar flag | |
| clndr_name | Calendar name | Display |
| proj_id | Project (empty = global calendar) | Filtering |
| base_clndr_id | Base/parent calendar | Inheritance |
| last_chng_date | Last modified | Audit trail |
| clndr_type | Calendar type | Measured: CA_Base, CA_Project, CT_Project |
| day_hr_cnt | **Hours per workday** | **Duration conversion** |
| week_hr_cnt | Hours per workweek | Duration conversion |
| month_hr_cnt | Hours per month | P6's default is **172**, not 168. Measured: 172 on 299 calendars, 160 on 175; the value 168 appears on none |
| year_hr_cnt | Hours per year | |
| rsrc_private | Resource-private flag | |
| clndr_data | **Encoded work pattern and exceptions** | **Full calendar logic** |

### Calendar Data Encoding (clndr_data)

Measured across all 523 CALENDAR records in the ground-truth set. Every one of them
carries a populated `clndr_data`, and every one uses the nested-block grammar below.
510 also carry an Exceptions block, though 105 of those blocks are empty, so 405
calendars actually carry at least one exception entry.

`clndr_data` is one long parenthesised string. The outer node is `CalendarData`,
which contains a `DaysOfWeek` block and, when the calendar has holidays or
modified days, an `Exceptions` block.

**A complete real calendar, copied verbatim from a 23.12 export** (a standard
five-day, eight-hour calendar with three holidays):

```
(0||CalendarData()((0||DaysOfWeek()((0||1()())(0||2()((0||0(s|08:00|f|16:00)())))(0||3()((0||0(s|08:00|f|16:00)())))(0||4()((0||0(s|08:00|f|16:00)())))(0||5()((0||0(s|08:00|f|16:00)())))(0||6()((0||0(s|08:00|f|16:00)())))(0||7()())))(0||Exceptions()((0||0(d|46192)())(0||0(d|46206)())(0||0(d|46272)())))))
```

**DaysOfWeek.** Each weekday is one segment of the form `(0||N()(<slots>))`:

- `N` is a **bare weekday ordinal**, 1 = Sunday through 7 = Saturday. There is no
  `d|` prefix on weekdays.
- A day whose segment contains at least one time slot is a **working day**.
- A day whose segment is empty, `(0||1()())`, is a **non-working day**.
- In the example above, days 2 to 6 carry slots and days 1 and 7 do not, so the
  calendar is Monday to Friday.

**Time slots.** A slot is `(0||i(s|HH:MM|f|HH:MM)())`, where `i` is the slot index
inside that day. A day can carry more than one slot. A real split-shift weekday,
verbatim from a 24.12 export:

```
(0||2()((0||0(s|08:00|f|12:00)())(0||1(s|13:00|f|17:00)())))
```

That is Monday, 08:00 to 12:00 and 13:00 to 17:00. Sum the slots to get the day's
work hours. Do not assume one slot per day.

**Hours are not zero-padded consistently.** The start time drops the leading zero in
some files: `s|8:00` as well as `s|08:00`. Measured across the ground-truth
calendars: 12,114 start times two digits wide, 509 one digit wide, spread over 21 of
the 166 files at 19.12, 23.10 and 23.12. The finish side is two digits in all 12,623
cases measured, and 24.12 pads both sides everywhere. A verbatim one-digit segment
from a 23.12 export:

```
(0||1()((0||0(s|8:00|f|16:00)())))
```

Match hours as `\d{1,2}`. A `\d\d:\d\d` pattern silently drops those slots and marks
the affected days non-working.

**Exceptions.** Each entry is `(0||i(d|<serial>)(<body>))`:

- `d|<serial>` carries the date as an **integer day serial on a 1899-12-30 epoch**
  (the Excel serial convention). `serial 40179` is 2010-01-01; `serial 46192` is
  2026-06-19. Decoding all 40,784 exception entries in the ground-truth set puts
  the top hits on 25 December (1,143), 1 January (1,085), 4 July (669),
  31 December (654), 1 July (639), 24 December (634) and 26 December (543), which
  confirms the epoch.
- `i` is a positional index. Of the 405 calendars carrying entries, 300 number them
  sequentially from 0 and 105 write `0` on every entry. Nothing else occurs, and no
  calendar mixes the two. It carries no date information, so ignore it.
- An **empty body** means a non-working exception, that is, a holiday:
  `(0||0(d|40179)())`.
- A body **containing a time slot** means a modified working day, not a holiday.
  Verbatim from a 23.12 export, with the P6 line markers shown as `\x7f`:

```
(0||24(d|45868)(\x7f\x7f      (0||0(s|08:00|f|17:00)())))
```

  Serial 45868 is 2025-07-30, worked 08:00 to 17:00.

**Two further things that will break a naive decoder:**

1. P6 inserts `\x7f\x7f` line markers and whitespace between an exception's serial
   and its body. A regex that requires the serial and the time slot to be adjacent
   classifies every modified working day as a holiday. On a continuous 7-day
   calendar that turns hundreds of worked days into days off and moves CPM finish
   dates by months.
2. There is no `e|` marker and no ISO date anywhere in `clndr_data`. Across all
   523 measured calendars, `e|YYYY-MM-DD` scores zero matches and so does the
   weekday form `(0||d|N(s|`.

`parse_calendar_data()` and `get_calendar_map()` in `scripts/xer_parser.py` are
the decoding entry points for this grammar. Any decoder written against it must
be separator-tolerant per point 1: match the serial and its body as one segment
bounded by the next serial, not as adjacent tokens.

---

<a name="udftype"></a>
## UDFTYPE — User Defined Field Types

9 fields in 23.10, 23.12 and 24.12; 8 in 19.12 (no `export_flag`).

| Field | Description | Key Use |
|-------|-------------|---------|
| udf_type_id | UDF type ID | Cross-ref from UDFVALUE |
| table_name | Target table | Measured: TASK, PROJECT, PROJWBS |
| udf_type_name | Internal name (e.g. `user_field_813`) | |
| udf_type_label | **Display label the scheduler typed** | **This is the name a user recognises** |
| logical_data_type | Data type | See below |
| super_flag | Global (enterprise-wide) flag | |
| indicator_expression | Indicator formula | |
| summary_indicator_expression | Summary indicator formula | |
| export_flag | Include on export (absent in 19.12) | |

**logical_data_type values measured in XER exports:** `FT_TEXT` (163 rows) and
`FT_STATICTYPE` (6 rows). XER uses the `FT_*` family. The `UDF_*` names belong to
P6's XML and API enumerations and appear in no XER file measured, so code that
branches on `UDF_TEXT` matches nothing.

Other `FT_*` codes exist in P6 for numeric, cost and date UDFs. Only the two above
were observed here, so only those two are stated as measured.

---

<a name="memotype"></a>
## MEMOTYPE — Notebook Topics

7 fields in 23.12 and 24.12.

| Field | Description | Key Use |
|-------|-------------|---------|
| memo_type_id | Topic ID | Cross-ref from TASKMEMO |
| seq_num | Sort order | Display order |
| eps_flag | Topic available on EPS nodes | **Scoping** |
| proj_flag | Topic available on projects | **Scoping** |
| wbs_flag | Topic available on WBS nodes | **Scoping** |
| task_flag | Topic available on activities | **Scoping** |
| memo_type | Topic name (e.g. `Notes`) | Display |

MEMOTYPE has no `proj_id`. Topics are global, and the four flags above are how
P6 scopes a topic to a level.

---

<a name="pcatval"></a>
## PCATVAL — Project Code Values

6 fields in every measured version.

| Field | Description |
|-------|-------------|
| proj_catg_id | Value ID |
| proj_catg_type_id | Type reference |
| seq_num | Sort order |
| proj_catg_short_name | Short code |
| parent_proj_catg_id | Parent value (hierarchy) |
| proj_catg_name | Description |

---

<a name="schedoptions"></a>
## SCHEDOPTIONS — Scheduling Options (25 fields, all measured versions)

Controls how the CPM engine calculates the schedule. 23 of the 166 genuine exports
carry no SCHEDOPTIONS table at all, so treat it as optional.

| Field | Description | Key Use |
|-------|-------------|---------|
| schedoptions_id | Options ID | |
| proj_id | Project reference | Filtering |
| sched_outer_depend_type | External dependency handling | Measured: SD_Both |
| sched_open_critical_flag | Treat open ends as critical | |
| sched_lag_early_start_flag | Compute lag from early start | |
| sched_retained_logic | **Retained logic (Y) or progress override (N)** | **Out-of-sequence handling** |
| sched_setplantoforecast | Set planned dates to forecast | |
| sched_float_type | **Float computation** | **Measured: FT_FF, FT_Min, FT_Start** |
| sched_calendar_on_relationship_lag | Calendar used for relationship lag | Measured: rcal_Predecessor |
| sched_use_expect_end_flag | Use expected finish dates | |
| sched_progress_override | Progress override | |
| level_float_thrs_cnt | Leveling float threshold | |
| level_outer_assign_flag | Level external assignments | |
| level_outer_assign_priority | External assignment priority | |
| level_over_alloc_pct | Over-allocation percentage | |
| level_within_float_flag | Level only within float | |
| level_keep_sched_date_flag | Preserve scheduled early/late dates | |
| level_all_rsrc_flag | Level all resources | |
| sched_use_project_end_date_for_float | Use project end date for float | **Changes every total float value** |
| enable_multiple_longest_path_calc | Multiple longest paths on | Multi-path float analysis |
| limit_multiple_longest_path_calc | Limit the multiple-longest-path search | |
| max_multiple_longest_path | Maximum paths to trace | |
| use_total_float_multiple_longest_paths | Use total float for multiple paths | |
| key_activity_for_multiple_longest_paths | Key activity anchoring the paths | |
| LevelPriorityList | Leveling priority list (e.g. `priority_type,ASC_BY_FIELD/ASC`) | |

Two traps here. First, the leveling threshold is `level_float_thrs_cnt`, with no
`sched_` prefix, unlike its neighbours. Second, `LevelPriorityList` is the only
field name in the whole format that is not lower case: of the 367 distinct field
names measured across all 32 tables, it is the single exception. A parser that
lower-cases field names loses it. There is no `sched_calc_id` field.

---

<a name="projwbs"></a>
## PROJWBS — Work Breakdown Structure (26 fields in 23.10 / 23.12 / 24.12)

19.12 carries 27: the 26 below plus `status_reviewer`.

| Field | Description | Key Use |
|-------|-------------|---------|
| wbs_id | WBS node ID | Cross-reference |
| proj_id | Project | Filtering |
| obs_id | OBS assignment | Responsibility |
| seq_num | Sort order | Display order |
| est_wt | Estimate weight | Earned value |
| proj_node_flag | **Y marks the project's own root row, not a real WBS band** | **Identify the project row before grouping activities by WBS** |
| sum_data_flag | Summary data present | |
| status_code | WBS status | Measured: WS_Open |
| wbs_short_name | WBS code | Display |
| wbs_name | **WBS description** | **Section headers / grouping** |
| phase_id | Phase reference | |
| parent_wbs_id | Parent WBS node | **Hierarchy building** |
| ev_user_pct | Earned value user % | |
| ev_etc_user_value | Earned value ETC value | |
| orig_cost | Original budget | |
| indep_remain_total_cost | Independent ETC | |
| ann_dscnt_rate_pct | Annual discount rate % | |
| dscnt_period_type | Discount period type | |
| indep_remain_work_qty | Independent remaining quantity | |
| anticip_start_date | Anticipated start | |
| anticip_end_date | Anticipated finish | |
| ev_compute_type | Earned value computation | Measured: EC_Cmp_pct, EC_PctCmpl, EC_MS, CE_MostLikely |
| ev_etc_compute_type | Earned value ETC computation | Measured: EE_Rem_hr, EE_PF_cpi, EE_Remaining, EE_PF_PctCmplt, EE_Rmn_hr |
| guid | Global unique ID | Matching across exports |
| tmpl_guid | Template GUID | |
| plan_open_state | Plan open state | |

There is no `wbs_id_prefix`, no `ev_etc_comp_flag` (the real field is
`ev_etc_compute_type`) and no `sum_data_date` (the real field is `sum_data_flag`).

---

<a name="projpcat"></a>
## PROJPCAT — Project Code Assignments

3 fields in every measured version.

| Field | Description |
|-------|-------------|
| proj_id | Project |
| proj_catg_type_id | Code type |
| proj_catg_id | Code value |

---

<a name="actvtype"></a>
## ACTVTYPE — Activity Code Types

8 fields in 23.10, 23.12 and 24.12; 7 in 19.12 (no `export_flag`).

| Field | Description | Key Use |
|-------|-------------|---------|
| actv_code_type_id | Type ID | Cross-ref from ACTVCODE and TASKACTV |
| actv_short_len | Short code length | |
| seq_num | Sort order | Display order |
| actv_code_type | Type name | **Column heading in reports** |
| proj_id | Owning project (empty on global codes) | Filtering |
| wbs_id | Owning WBS node on WBS-level codes | Filtering |
| actv_code_type_scope | **Code scope** | **Measured: AS_Project, AS_Global** |
| export_flag | Include on export (absent in 19.12) | |

There is no `super_flag` in ACTVTYPE. Scope is carried by `actv_code_type_scope`.

---

<a name="rsrc"></a>
## RSRC — Resources (31 fields in 24.12; 28 or 31 in 23.12)

Present in 10 of 166 files. Two different field lists appear inside 23.12 itself:
a 28-field form, and the 31-field form documented below, which appends
`load_tasks_flag`, `level_flag` and `last_checksum` after `rsrc_notes`. 24.12 uses
the same 31 names but moves `rsrc_type` and `location_id` from positions 26-27 to
the end of the row. Never hard-code this table's field count or column order.

| Field | Description | Key Use |
|-------|-------------|---------|
| rsrc_id | Resource ID | Cross-ref from TASKRSRC |
| parent_rsrc_id | Parent resource (hierarchy) | Rollups |
| clndr_id | Resource calendar | Availability |
| role_id | Primary role | |
| shift_id | Shift assignment | |
| user_id | Linked P6 user | |
| pobs_id | Owning OBS node | |
| guid | Global unique ID | Matching across exports |
| rsrc_seq_num | Sort order | Display order |
| email_addr | Email | |
| employee_code | Employee code | |
| office_phone | Office phone | |
| other_phone | Other phone | |
| rsrc_name | **Resource name** | **Reporting** |
| rsrc_short_name | **Resource code** | **Reporting** |
| rsrc_title_name | Title | |
| def_qty_per_hr | Default quantity per hour | Units conversion |
| cost_qty_type | Default quantity type | Measured: QT_Hour |
| ot_factor | Overtime factor | |
| active_flag | Resource active | Filtering |
| auto_compute_act_flag | Auto-compute actuals | |
| def_cost_qty_link_flag | Link cost to quantity by default | |
| ot_flag | Overtime allowed | |
| curr_id | Currency | Cost conversion |
| unit_id | Unit of measure | |
| rsrc_type | **RT_Labor / RT_Equip / RT_Mat** | **Resource classification** |
| location_id | Location | |
| rsrc_notes | Notes | |
| load_tasks_flag | Load activities for this resource (31-field form only) | |
| level_flag | Include in leveling (31-field form only) | |
| last_checksum | Internal checksum (31-field form only) | |

`max_qty_per_hr` is not in RSRC. Availability lives in RSRCRATE.

`rsrc_type` measured values are `RT_Labor`, `RT_Equip` and `RT_Mat`. Not
`RT_Nonlabor`, and not `RT_Matrl`.

---

<a name="rsrcrate"></a>
## RSRCRATE — Resource Rates (10 fields)

Present in 3 of 166 files (23.12).

| Field | Description | Key Use |
|-------|-------------|---------|
| rsrc_rate_id | Rate record ID | Primary key |
| rsrc_id | Resource reference | Join to RSRC |
| max_qty_per_hr | **Max quantity per hour** | **Availability limit** |
| cost_per_qty | Price/unit rate 1 | **Cost calculation** |
| start_date | Rate effective date | Rate escalation over time |
| shift_period_id | Shift period reference | |
| cost_per_qty2 | Price/unit rate 2 | |
| cost_per_qty3 | Price/unit rate 3 | |
| cost_per_qty4 | Price/unit rate 4 | |
| cost_per_qty5 | Price/unit rate 5 | |

The primary key is `rsrc_rate_id`, not `rsrcrate_id`. P6 carries five price/unit
columns per resource, and TASKRSRC's `rate_type` records which rate an assignment
was priced at.

---

<a name="task"></a>
## TASK — Activities (61 fields in 23.10 / 23.12 / 24.12)

The core schedule data table. Every activity in the schedule lives here.

`crt_path_num` is the 61st and last field in all 163 exports measured at 23.10,
23.12 and 24.12, with no exceptions, including all 50 genuine 24.12 files. It is a
standard member of the 61-field layout, not a version-specific addition, and it
does not take TASK to 62. Do not version-gate it.

19.12 carries 66 fields: the 61 below minus `crt_path_num`, plus `cbs_id`,
`control_updates_flag`, `pre_pess_start_date`, `pre_pess_finish_date`,
`post_pess_start_date` and `post_pess_finish_date`.

| Field | Description | Key Use |
|-------|-------------|---------|
| task_id | Internal activity ID | **Primary key** |
| proj_id | Project reference | Multi-project filtering |
| wbs_id | WBS assignment | **Grouping** |
| clndr_id | Calendar assignment | **Duration calculation** |
| phys_complete_pct | Physical % complete | **Progress** |
| rev_fdbk_flag | Review feedback flag | |
| est_wt | Estimate weight | Earned value |
| lock_plan_flag | Locked to plan | |
| auto_compute_act_flag | Auto-compute actuals | |
| complete_pct_type | % complete type | Measured: CP_Drtn, CP_Phys |
| task_type | **TT_Task / TT_Mile / TT_FinMile / TT_LOE / TT_Rsrc / TT_WBS** | **Activity classification** |
| duration_type | Duration type | Measured: DT_FixedDrtn, DT_FixedQty, DT_FixedDUR2, DT_FixedRate, DT_FixedDrtnAndQty |
| status_code | **TK_NotStart / TK_Active / TK_Complete** | **Activity status** |
| task_code | **Activity ID (user-visible)** | **Reporting** |
| task_name | **Activity description** | **Reporting** |
| rsrc_id | Primary resource | Resource-dependent activities |
| total_float_hr_cnt | **Total float (hours)** | **Critical path ID** |
| free_float_hr_cnt | Free float (hours) | Near-critical analysis |
| remain_drtn_hr_cnt | **Remaining duration (hours)** | **Remaining work** |
| act_work_qty | Actual work quantity | |
| remain_work_qty | Remaining work quantity | |
| target_work_qty | Baseline work quantity | |
| target_drtn_hr_cnt | **Baseline/target duration (hours)** | **Planned duration** |
| target_equip_qty | Target equipment quantity | |
| act_equip_qty | Actual equipment quantity | |
| remain_equip_qty | Remaining equipment quantity | |
| cstr_date | Primary constraint date | Constraint analysis |
| act_start_date | **Actual start** | **As-built start** |
| act_end_date | **Actual finish** | **As-built finish** |
| late_start_date | Late start | Float calculation |
| late_end_date | Late finish | Float calculation |
| expect_end_date | Expected finish | Forecasting |
| early_start_date | **Calculated early start** | **CPM schedule** |
| early_end_date | **Calculated early finish** | **CPM schedule** |
| restart_date | Restart date after suspension | Delay evidence |
| reend_date | Re-finish date after suspension | Delay evidence |
| target_start_date | **Baseline early start** | **Planned start** |
| target_end_date | **Baseline early finish** | **Planned finish** |
| rem_late_start_date | **Remaining late start** | **Late dates for the unfinished portion. Use these, not late_start_date, on in-progress work** |
| rem_late_end_date | **Remaining late finish** | **Same, for finish** |
| cstr_type | Primary constraint type | Measured: CS_MANDSTART, CS_MSOA, CS_MSO, CS_MEO, CS_MEOB, CS_MEOA, CS_MSOB, CS_MANDFIN |
| priority_type | Leveling priority | Measured: PT_Normal, PT_Top |
| suspend_date | Suspension date | Delay evidence |
| resume_date | Resume date | Delay evidence |
| float_path | **Multiple-float-path number** | **Path tracing when multiple longest paths are on** |
| float_path_order | **Order within that float path** | **Sequencing a traced path** |
| guid | Global unique ID | **Matching activities across exports even when task_code changes** |
| tmpl_guid | Template GUID | |
| cstr_date2 | Secondary constraint date | Constraint analysis |
| cstr_type2 | Secondary constraint type | Measured: CS_MANDFIN, CS_ALAP |
| driving_path_flag | **Y/N longest path indicator** | **Critical path** |
| act_this_per_work_qty | Work quantity this period | |
| act_this_per_equip_qty | Equipment quantity this period | |
| external_early_start_date | External early start | Inter-project logic |
| external_late_end_date | External late finish | Inter-project logic |
| create_date | Activity creation date | **Audit trail: when an activity was added** |
| update_date | Last update date | Audit trail |
| create_user | Created by | Audit trail |
| update_user | Updated by | Audit trail |
| location_id | Location reference | |
| crt_path_num | **Longest path number** | **Longest path trace** |

TASK has no `priority_num`, no `memo_exist_flag`, no `rsrc_exist_flag` and no
`pred_exist_flag`. To know whether an activity has notes, resources or logic, join
to TASKMEMO, TASKRSRC and TASKPRED.

### Duration Conversion Rules

All durations in TASK are stored in **hours**:

- `target_drtn_hr_cnt / hours_per_day = baseline workdays`
- Get `hours_per_day` from the CALENDAR table (via `clndr_id`)
- Default: 8 hours/day if calendar lookup fails
- Duration delta: `actual_duration - baseline_duration = delay in workdays`

### Status Code Reference

| Code | Meaning |
|------|---------|
| TK_NotStart | Not Started |
| TK_Active | In Progress |
| TK_Complete | Complete |

### Task Type Reference

| Code | Meaning | Include in CP? |
|------|---------|----------------|
| TT_Task | Task Dependent | Yes |
| TT_Rsrc | Resource Dependent | Yes |
| TT_Mile | Start Milestone | Yes |
| TT_FinMile | Finish Milestone | Yes |
| TT_LOE | Level of Effort | **No** |
| TT_WBS | WBS Summary | **No** |

### Constraint Type Reference (measured)

| Code | Meaning | Effect |
|------|---------|--------|
| CS_MSO | Start On | Pins the start |
| CS_MSOA | Start On or After | Early constraint |
| CS_MSOB | Start On or Before | Late constraint |
| CS_MEO | Finish On | Pins the finish |
| CS_MEOA | Finish On or After | Early constraint |
| CS_MEOB | Finish On or Before | Late constraint |
| CS_MANDSTART | Mandatory Start | **Overrides logic** |
| CS_MANDFIN | Mandatory Finish | **Overrides logic** |
| CS_ALAP | As Late As Possible | Consumes free float |

The mandatory codes are `CS_MANDSTART` and `CS_MANDFIN`. Not `CS_MANSTART` or
`CS_MANFINISH`: neither spelling appears in any genuine export measured.

---

<a name="rsrcrcat"></a>
## RSRCRCAT — Resource Code Assignments

Present in 1 of 166 files (23.12). 3 fields.

| Field | Description |
|-------|-------------|
| rsrc_id | Resource |
| rsrc_catg_type_id | Code type |
| rsrc_catg_id | Code value |

The table header is `RSRCRCAT`. No export measured writes a `RSRCCAT` header, so
code keyed on that spelling never fires.

---

<a name="wbsstep"></a>
## WBSSTEP — WBS Steps

Weighted steps under a WBS node. Present in 6 of 166 files (19.12 and 23.12).
7 fields.

| Field | Description |
|-------|-------------|
| wbs_step_id | Step ID |
| proj_id | Project |
| wbs_id | WBS node |
| seq_num | Sort order |
| complete_flag | Step complete |
| step_name | Step description |
| step_wt | Step weight |

---

<a name="actvcode"></a>
## ACTVCODE — Activity Code Values

8 fields in every measured version.

| Field | Description | Key Use |
|-------|-------------|---------|
| actv_code_id | Code value ID | Cross-ref from TASKACTV |
| parent_actv_code_id | Parent code (hierarchy) | Rollups |
| actv_code_type_id | Code type reference | Join to ACTVTYPE |
| actv_code_name | **Code description** | **Reporting label** |
| short_name | **Short code** | **Grouping key** |
| seq_num | Sort order | Display order |
| color | Display colour | |
| total_assignments | Count of activities carrying this value | Quick coverage check |

---

<a name="rsrcrole"></a>
## RSRCROLE — Resource Role Assignments

Present in 1 of 166 files (23.12). 9 fields.

| Field | Description |
|-------|-------------|
| rsrc_id | Resource |
| role_id | Role |
| skill_level | Proficiency level |
| role_short_name | Role code |
| role_name | Role name |
| rsrc_short_name | Resource code |
| rsrc_name | Resource name |
| rsrc_type | Resource type |
| rsrc_role_id | Assignment record ID |

---

<a name="taskpred"></a>
## TASKPRED — Relationships / Logic Ties (11 fields in 23.10 / 23.12 / 24.12)

19.12 carries 10: the 11 below without `comments`.

Column order is uniform across all 159 measured 23.10, 23.12 and 24.12 exports:
`comments` is always field 8, straight after `lag_hr_cnt`. Files that place it
elsewhere are not Oracle exports.

| Field | Description | Key Use |
|-------|-------------|---------|
| task_pred_id | Internal ID | Primary key |
| task_id | **Successor activity** | Logic analysis |
| pred_task_id | **Predecessor activity** | Logic analysis |
| proj_id | Successor project | |
| pred_proj_id | Predecessor project | Inter-project logic |
| pred_type | **PR_FS / PR_FF / PR_SS / PR_SF** | **Relationship type** |
| lag_hr_cnt | **Lag duration (hours)** | **Lag analysis** |
| comments | Relationship comments (absent in 19.12) | Evidence of a documented tie |
| float_path | Float path number | Longest path trace |
| aref | Date value written by the scheduler | Undocumented by Oracle. Holds a date in every populated row measured. Do not build logic on it |
| arls | Date value written by the scheduler | Same |

### Relationship Types (measured share across 148,946 relationships)

| Code | Meaning | Measured |
|------|---------|----------|
| PR_FS | Finish-to-Start | 133,804 (89.8%) |
| PR_SS | Start-to-Start | 7,822 (5.3%) |
| PR_FF | Finish-to-Finish | 7,081 (4.8%) |
| PR_SF | Start-to-Finish | 239 (0.2%), flag if found |

Percentages of relationships are always taken over the relationship count, never
over the activity count.

---

<a name="taskactv"></a>
## TASKACTV — Task Activity Code Assignments

4 fields in every measured version.

| Field | Description |
|-------|-------------|
| task_id | Activity reference |
| actv_code_type_id | Code type |
| actv_code_id | Code value |
| proj_id | Project |

---

<a name="taskmemo"></a>
## TASKMEMO — Activity Notebooks

5 fields in 23.12 and 24.12.

| Field | Description | Key Use |
|-------|-------------|---------|
| memo_id | Notebook entry ID | Primary key |
| task_id | Activity | **Join to TASK** |
| memo_type_id | Topic reference | Join to MEMOTYPE |
| proj_id | Project | Filtering |
| task_memo | **Notebook text** | **Contemporaneous narrative evidence. Often HTML** |

---

<a name="taskrsrc"></a>
## TASKRSRC — Resource Assignments (47 fields in 23.12; 48 in 24.12)

The third field-heaviest table in a resource-loaded export, ahead of PROJWBS and
SCHEDOPTIONS. 24.12 carries 48: the 47 below minus `has_rsrchours`, plus
`update_user` and `update_date`. 19.12 carries 48: the 47 below plus `cbs_id`.

| Field | Description | Key Use |
|-------|-------------|---------|
| taskrsrc_id | Assignment ID | Primary key |
| task_id | Activity reference | **Join to TASK** |
| proj_id | Project | Filtering |
| cost_qty_link_flag | Cost linked to quantity | |
| role_id | Role on this assignment | |
| acct_id | Cost account | Cost coding |
| rsrc_id | Resource reference | **Join to RSRC** |
| pobs_id | Owning OBS node | |
| skill_level | Proficiency level | |
| remain_qty | **Remaining quantity** | **Remaining hours** |
| target_qty | **Budgeted quantity** | **Budgeted hours** |
| remain_qty_per_hr | Remaining units per hour | Crew size |
| target_lag_drtn_hr_cnt | Assignment lag (hours) | |
| target_qty_per_hr | Budgeted units per hour | **Crew size** |
| act_ot_qty | Actual overtime quantity | |
| act_reg_qty | Actual regular quantity | **Actual hours** |
| relag_drtn_hr_cnt | Re-lag duration (hours) | |
| ot_factor | Overtime factor | |
| cost_per_qty | **Rate applied** | **Cost calculation** |
| target_cost | **Budgeted cost** | **Budget** |
| act_reg_cost | Actual regular cost | **Cost to date** |
| act_ot_cost | Actual overtime cost | |
| remain_cost | **Remaining cost** | **ETC** |
| act_start_date | Actual start | As-built |
| act_end_date | Actual finish | As-built |
| restart_date | Restart date | |
| reend_date | Re-finish date | |
| target_start_date | Planned start | |
| target_end_date | Planned finish | |
| rem_late_start_date | Remaining late start | |
| rem_late_end_date | Remaining late finish | |
| rollup_dates_flag | Roll assignment dates to the activity | |
| target_crv | Budgeted curve | Join to RSRCCURVDATA |
| remain_crv | Remaining curve | |
| actual_crv | Actual curve | |
| ts_pend_act_end_flag | Timesheet pending actual finish | |
| guid | Global unique ID | Matching across exports |
| rate_type | **Which price/unit rate applies to this assignment** | Measured: COST_PER_QTY, rt_Price |
| act_this_per_cost | Cost this period | Period reporting |
| act_this_per_qty | Quantity this period | Period reporting |
| curv_id | Curve reference | |
| rsrc_type | Resource type on the assignment | Measured: RT_Labor, RT_Mat, RT_Equip |
| cost_per_qty_source_type | Where the rate came from | Measured: ST_Role, ST_Rsrc |
| create_user | Created by | Audit trail |
| create_date | Created on | Audit trail |
| has_rsrchours | Timesheet hours present (23.12 only) | |
| taskrsrc_sum_id | Summary record reference | |

TASKRSRC has no `remain_drtn_hr_cnt` and no `pend_complete_pct`. Remaining duration
lives on the activity, in TASK.

---

<a name="udfvalue"></a>
## UDFVALUE — User Defined Field Values

7 fields in every measured version.

| Field | Description | Key Use |
|-------|-------------|---------|
| udf_type_id | UDF type reference | Join to UDFTYPE |
| fk_id | **Foreign key into the target table** | **task_id, proj_id or wbs_id, per UDFTYPE.table_name** |
| proj_id | Project | Filtering |
| udf_date | Date value | |
| udf_number | Numeric value | |
| udf_text | Text value | |
| udf_code_id | Code value reference | |

---

<a name="unmeasured"></a>
## P6 tables not present in the measured set

P6 can emit tables beyond the 32 above. The following are named in P6's own
schema but appear in none of the 166 ground-truth exports, so no field list is
published for them here. If your export carries one, read its `%F` line.

TASKFIN, TRSRCFIN, TASKDOC, PROJDOCS, SHIFT, SHIFTPER, ACCOUNT, WBSMEMO,
PROJMEMO, RISK, POBS.

The catalogue is not closed. Build the parser to read whatever `%T` blocks the
file contains rather than to a fixed list.

---

<a name="pitfalls"></a>
## Parsing Pitfalls — Quick Reference

| Pitfall | Detail |
|---------|--------|
| **Tab delimiters** | XER uses `\t`, never commas or spaces. Fields may contain commas and spaces that are not delimiters. |
| **Empty fields** | Empty strings between tabs, not NULL, not "N/A". |
| **Dates** | Always `YYYY-MM-DD HH:MM`, and **timezone-naive local wall-clock**. The file carries no timezone marker of any kind, and P6 applies no conversion on export. Never convert from UTC. Measured: every one of the 1,367,430 cells in the ground-truth set that begins with a date matches `YYYY-MM-DD HH:MM` exactly, none carries a `Z`, a `T` or an offset, none is date-only, and 8,561 of 8,879 timed actual starts land on exactly 08:00, matching the calendars' own 08:00 work-window start. A site 08:00 exported as UTC from an Ontario database would read 12:00 or 13:00, and none do. |
| **Durations** | ALL in hours. Divide by `day_hr_cnt` from CALENDAR for workdays. |
| **Calendar times** | `clndr_data` hours are not consistently zero-padded: `s|8:00` occurs alongside `s|08:00` in 21 of the 166 files (19.12, 23.10, 23.12). Match `\d{1,2}:\d\d`, or the affected days parse as non-working. |
| **Hours per month** | P6's default `month_hr_cnt` is 172, not 168. Measured across 523 calendars: 172 on 299, 160 on 175, and 168 on none. |
| **Multi-project** | XER can contain multiple projects. Filter by `proj_id`. |
| **LOE/WBS Summary** | Exclude `TT_LOE` and `TT_WBS` from critical path analysis. |
| **Constraints** | Hard constraints distort float. Flag `cstr_type` and `cstr_type2` activities. `CS_MANDSTART` and `CS_MANDFIN` override logic outright. |
| **Relationship percentages** | Non-FS share, lead share and similar logic metrics are shares of the TASKPRED row count, never of the activity count. |
| **Read the %F line** | Field count and column order vary within one version and between adjacent versions: RSRC appears with 28 and 31 fields at 23.12, 24.12 moves `rsrc_type` and `location_id` to the end of the RSRC row, and TASKRSRC swaps `has_rsrchours` for `update_user`/`update_date` at 24.12. Index by name, never by position. |
| **Case sensitivity** | `LevelPriorityList` in SCHEDOPTIONS is the one mixed-case field name. Do not lower-case field names. |
| **%F vs %R mismatch** | If field count doesn't match data columns, the import grid will be blank in P6. |
| **Encoding** | Try UTF-8 first, then CP1252, then Latin-1. |
| **CRLF** | P6 expects `\r\n` line endings when importing. |
| **Field counts, 23.10 / 23.12 / 24.12** | PROJECT=71, SCHEDOPTIONS=25, PROJWBS=26, TASK=61 (including `crt_path_num`), TASKPRED=11, identical across all three versions. Denominators differ because not every export carries every table: PROJECT, PROJWBS and TASK in 163 of 163 exports, TASKPRED in 159, SCHEDOPTIONS in 140. No 22.x export was measured, so these counts are not claimed for 22.x. |
| **Field counts, 19.12** | PROJECT=82, SCHEDOPTIONS=25, PROJWBS=27, TASK=66 (no `crt_path_num`), TASKPRED=10. Three exports measured. |
| **Field-heaviest tables** | Measured ranking: PROJECT 71, TASK 61, TASKRSRC 47–48, RSRC 28–31, PROJWBS 26, SCHEDOPTIONS 25, RSRCCURVDATA 24. In a resource-loaded export, TASKRSRC and RSRC outrank PROJWBS and SCHEDOPTIONS. |
