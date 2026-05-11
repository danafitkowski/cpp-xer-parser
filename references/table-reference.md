# P6 XER Complete Table Reference

All tables that can appear in a Primavera P6 XER file export (P6 Professional 24.12). Tables are listed in canonical export order.

## Table of Contents

1. [CURRTYPE — Currencies](#currtype)
2. [FINTMPL — Financial Templates](#fintmpl)
3. [OBS — Organizational Breakdown Structure](#obs)
4. [PROJECT — Project Header](#project)
5. [CALENDAR — Work Calendars](#calendar)
6. [SCHEDOPTIONS — Scheduling Options](#schedoptions)
7. [PROJWBS — Work Breakdown Structure](#projwbs)
8. [TASK — Activities](#task)
9. [TASKPRED — Relationships / Logic Ties](#taskpred)
10. [TASKRSRC — Resource Assignments](#taskrsrc)
11. [RSRC — Resources](#rsrc)
12. [RSRCRATE — Resource Rates](#rsrcrate)
13. [ACTVTYPE — Activity Code Types](#actvtype)
14. [ACTVCODE — Activity Code Values](#actvcode)
15. [TASKACTV — Task Activity Code Assignments](#taskactv)
16. [UDFTYPE — User Defined Field Types](#udftype)
17. [UDFVALUE — User Defined Field Values](#udfvalue)
18. [PROJPCAT — Project Code Assignments](#projpcat)
19. [PCATTYPE — Project Code Types](#pcattype)
20. [PCATVAL — Project Code Values](#pcatval)
21. [TASKFIN — Task Financial Periods](#taskfin)
22. [TRSRCFIN — Resource Financial Periods](#trsrcfin)
23. [TASKDOC — Task Documents](#taskdoc)
24. [PROJDOCS — Project Documents](#projdocs)
25. [ROLERATE — Role Rates](#rolerate)
26. [ROLES — Roles](#roles)
27. [RSRCROLE — Resource Role Assignments](#rsrcrole)
28. [SHIFT — Shifts](#shift)
29. [SHIFTPER — Shift Periods](#shiftper)
30. [ACCOUNT — Cost Accounts](#account)
31. [RCATTYPE — Resource Code Types](#rcattype)
32. [RCATVAL — Resource Code Values](#rcatval)
33. [RSRCCAT — Resource Code Assignments](#rsrccat)
34. [MEMOTYPE — Notebook Topics](#memotype)
35. [TASKMEMO — Activity Notebooks](#taskmemo)
36. [WBSMEMO — WBS Notebooks](#wbsmemo)
37. [PROJMEMO — Project Notebooks](#projmemo)
38. [RISKTYPE — Risk Categories](#risktype)
39. [RISK — Risks](#risk)
40. [RISKTYPES — Risk Type Assignments](#risktypes)

---

<a name="currtype"></a>
## CURRTYPE — Currencies

Currency definitions used in the project.

| Field | Description |
|-------|-------------|
| curr_id | Internal currency ID |
| curr_short_name | Currency code (e.g., CAD, USD) |
| curr_name | Full name |
| decimal_digit_cnt | Decimal places |
| curr_symbol | Symbol ($, €, etc.) |
| decimal_symbol | Decimal separator |
| digit_group_symbol | Thousands separator |
| pos_curr_fmt_type | Positive format |
| neg_curr_fmt_type | Negative format |
| base_exch_rate | Exchange rate to base currency |

---

<a name="fintmpl"></a>
## FINTMPL — Financial Templates

Financial period templates for earned value / cost tracking.

| Field | Description |
|-------|-------------|
| fintmpl_id | Template ID |
| fintmpl_name | Template name |

---

<a name="obs"></a>
## OBS — Organizational Breakdown Structure

| Field | Description |
|-------|-------------|
| obs_id | OBS node ID |
| parent_obs_id | Parent node |
| obs_name | Node name |
| obs_short_name | Short code |
| seq_num | Sort order |

---

<a name="project"></a>
## PROJECT — Project Header (72 fields in P6 24.12)

Project-level metadata — the most field-heavy table.

| Field | Description | Key Use |
|-------|-------------|---------|
| proj_id | Internal project ID | Cross-reference everywhere |
| proj_short_name | Project code/name | Display name |
| task_code_prefix | Activity ID prefix | |
| last_recalc_date | **Data date / status date** | **Most critical date in schedule** |
| plan_start_date | Project planned start | Baseline reference |
| plan_end_date | Project must-finish date | Contractual deadline |
| scd_end_date | Scheduled finish (calculated) | CPM-calculated finish |
| sum_data_date | Summary data date | |
| last_tasksum_date | Last summary calculation | |
| last_fin_dates_id | Financial periods ref | |
| fintmpl_id | Financial template | |
| def_complete_pct_type | % complete type (CP_Phys, CP_Drtn, CP_Units) | |
| act_this_per_link_flag | Actuals this period | |
| def_cost_per_qty_link_flag | Cost/qty link default | |
| rsrc_self_add_flag | Resource self-add | |
| allow_complete_flag | Allow activities past 100% | |
| sum_assign_level | Summary assignment level | |
| last_baseline_update_date | Last baseline update | |
| cr_external_key | External key | |
| sum_base_proj_id | Baseline project ID | Baseline cross-reference |
| last_level_date | Last leveling date | |
| def_qty_type | Default quantity type | |
| add_by_name | Created by | |
| task_code_base | Activity ID numbering base | |
| task_code_step | Activity ID increment | |
| priority_num | Project priority | |
| wbs_max_sum_level | WBS summary max level | |
| strgy_priority_num | Strategic priority | |
| last_checksum | Checksum | |
| critical_path_type | Critical path method (CP_TotalFloat, CP_LongestPath) | |
| critical_drtn_hr_cnt | Critical float threshold (hours) | |
| fy_start_month_num | Fiscal year start month | |

*Note: PROJECT has many additional administrative fields (GUIDs, permissions, flags). The above are the scheduling-critical ones. Full field list is available in the parsed output.*

---

<a name="calendar"></a>
## CALENDAR — Work Calendars

| Field | Description | Key Use |
|-------|-------------|---------|
| clndr_id | Calendar ID | Cross-ref from TASK |
| clndr_name | Calendar name | Display |
| proj_id | Project (null = global) | Filtering |
| base_clndr_id | Base/parent calendar | Inheritance |
| day_hr_cnt | **Hours per workday** | **Duration conversion** |
| week_hr_cnt | Hours per workweek | Duration conversion |
| month_hr_cnt | Hours per month | |
| year_hr_cnt | Hours per year | |
| clndr_data | **Encoded work pattern + holidays** | **Full calendar logic** |
| default_flag | Default calendar flag | |
| clndr_type | Calendar type | |
| rsrc_private | Resource-private flag | |
| last_chng_date | Last modified | |

### Calendar Data Encoding (clndr_data)

The `clndr_data` field is a proprietary encoded string containing:
- Standard work week pattern (which days are work days, with start/finish times)
- Holiday exception dates (non-work days)
- Work-hour exceptions (modified work hours on specific dates)

**Pattern structure:**
```
(0||d|1(s|08:00|f|17:00))(0||d|2(s|08:00|f|17:00))...
```
- `d|N` = day number (1=Sunday through 7=Saturday)
- `s|HH:MM` = start time
- `f|HH:MM` = finish time
- Empty parens `d|N()` = non-work day

**Exception dates appear as:**
```
(0||e|YYYY-MM-DD(...))
```

The `xer_parser.py` script's `parse_calendar_data()` and `get_calendar_map()` functions handle full decoding including holidays.

---

<a name="schedoptions"></a>
## SCHEDOPTIONS — Scheduling Options (26 fields in P6 24.12)

Controls how the CPM engine calculates the schedule.

| Field | Description |
|-------|-------------|
| schedoptions_id | Options ID |
| proj_id | Project reference |
| sched_outer_depend_type | External dependencies handling |
| sched_open_critical_flag | Open-ended critical |
| sched_lag_early_start_flag | Lag calculation method |
| sched_retained_logic | Retained logic (Y/N) |
| sched_setplantoforecast | Plan to forecast |
| sched_float_type | Float type (FT_Start, FT_Finish) |
| sched_calendar_on_relationship_lag | Calendar for relationship lag |
| sched_use_expect_end_flag | Use expected finish |
| sched_use_project_end_date_for_float | Use project end for float |
| sched_level_float_thrs_cnt | Leveling float threshold |
| enable_multiple_longest_path_calc | Multiple longest paths |
| sched_calc_id | Schedule calculation method |
| limit_multiple_longest_path_calc | Limit for multiple LP |
| sched_progress_override | Progress override |

---

<a name="projwbs"></a>
## PROJWBS — Work Breakdown Structure (27 fields in P6 24.12)

| Field | Description | Key Use |
|-------|-------------|---------|
| wbs_id | WBS node ID | Cross-reference |
| proj_id | Project | Filtering |
| obs_id | OBS assignment | Responsibility |
| parent_wbs_id | Parent WBS node | **Hierarchy building** |
| wbs_short_name | WBS code | Display |
| wbs_name | **WBS description** | **Section headers / grouping** |
| seq_num | Sort order | Display order |
| est_wt | Estimate weight | EV calculation |
| status_code | WBS status | |
| wbs_id_prefix | ID prefix | |
| ev_user_pct | EV user % | |
| ev_etc_user_value | EV ETC value | |
| ev_etc_comp_flag | EV ETC complete flag | |
| ev_compute_type | EV computation type | |
| sum_data_date | Summary data date | |
| guid | Global unique ID | |
| tmpl_guid | Template GUID | |
| phase_id | Phase reference | |
| orig_cost | Original budget | |
| indep_remain_total_cost | Independent ETC | |
| indep_remain_work_qty | Independent remaining qty | |
| anticip_start_date | Anticipated start | |
| anticip_end_date | Anticipated finish | |

---

<a name="task"></a>
## TASK — Activities (62 fields in P6 24.12, includes crt_path_num)

The core schedule data table. Every activity in the schedule lives here.

| Field | Description | Key Use |
|-------|-------------|---------|
| task_id | Internal activity ID | **Primary key** |
| task_code | **Activity ID (user-visible)** | **Reporting** |
| task_name | **Activity description** | **Reporting** |
| proj_id | Project reference | Multi-project filtering |
| wbs_id | WBS assignment | **Grouping** |
| clndr_id | Calendar assignment | **Duration calculation** |
| phys_complete_pct | Physical % complete | **Progress** |
| rev_fdbk_flag | Review feedback | |
| est_wt | Estimate weight | |
| lock_plan_flag | Locked to baseline | |
| auto_compute_act_flag | Auto-compute actuals | |
| complete_pct_type | % complete type | |
| task_type | **TT_Task / TT_Mile / TT_FinMile / TT_LOE / TT_Rsrc / TT_WBS** | **Activity classification** |
| duration_type | DT_FixedDrtn / DT_FixedQty / DT_FixedDUR2 / DT_FixedRate | |
| status_code | **TK_NotStart / TK_Active / TK_Complete** | **Activity status** |
| target_drtn_hr_cnt | **Baseline/target duration (hours)** | **Planned duration** |
| remain_drtn_hr_cnt | **Remaining duration (hours)** | **Remaining work** |
| target_start_date | **Baseline early start** | **Planned start** |
| target_end_date | **Baseline early finish** | **Planned finish** |
| act_start_date | **Actual start** | **As-built start** |
| act_end_date | **Actual finish** | **As-built finish** |
| early_start_date | **Calculated early start** | **CPM schedule** |
| early_end_date | **Calculated early finish** | **CPM schedule** |
| late_start_date | Late start | Float calculation |
| late_end_date | Late finish | Float calculation |
| expect_end_date | Expected finish | Forecasting |
| total_float_hr_cnt | **Total float (hours)** | **Critical path ID** |
| free_float_hr_cnt | Free float (hours) | Near-critical analysis |
| driving_path_flag | **Y/N — longest path indicator** | **Critical path** |
| crt_path_num | **Longest path number** | **Longest path trace** |
| suspend_date | Suspension date | Delay evidence |
| resume_date | Resume date | Delay evidence |
| cstr_date | Primary constraint date | Constraint analysis |
| cstr_type | Constraint type code | Constraint analysis |
| cstr_date2 | Secondary constraint date | |
| cstr_type2 | Secondary constraint type | |
| priority_type | Priority type | Leveling |
| priority_num | Priority number | Leveling |
| guid | Global unique ID | |
| tmpl_guid | Template GUID | |
| memo_exist_flag | Notebook exists | |
| rsrc_exist_flag | Resources assigned | |
| pred_exist_flag | Predecessors exist | |
| target_work_qty | Baseline work quantity | |
| act_work_qty | Actual work quantity | |
| remain_work_qty | Remaining work quantity | |
| target_equip_qty | Target equipment qty | |
| act_equip_qty | Actual equipment qty | |
| remain_equip_qty | Remaining equipment qty | |
| restart_date | Restart date | |
| reend_date | Re-end date | |
| create_date | Activity creation date | Audit trail |
| update_date | Last update date | Audit trail |
| create_user | Created by | |
| update_user | Updated by | |
| external_early_start_date | External ES | |
| external_late_end_date | External LF | |
| location_id | Location reference | |
| act_this_per_work_qty | Work qty this period | |
| act_this_per_equip_qty | Equip qty this period | |

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

---

<a name="taskpred"></a>
## TASKPRED — Relationships / Logic Ties (12 fields in P6 24.12, includes comments/aref/arls)

| Field | Description | Key Use |
|-------|-------------|---------|
| task_pred_id | Internal ID | Primary key |
| task_id | **Successor activity** | Logic analysis |
| pred_task_id | **Predecessor activity** | Logic analysis |
| proj_id | Successor project | |
| pred_proj_id | Predecessor project | Inter-project logic |
| pred_type | **PR_FS / PR_FF / PR_SS / PR_SF** | **Relationship type** |
| lag_hr_cnt | **Lag duration (hours)** | **Lag analysis** |
| float_path | Float path number | Longest path trace |
| aref | Actual relationship reference | |
| arls | Actual relationship lag status | |
| comments | Relationship comments | |

### Relationship Types

| Code | Meaning | Usage |
|------|---------|-------|
| PR_FS | Finish-to-Start | Most common (~80%+) |
| PR_FF | Finish-to-Finish | Common in concurrent work |
| PR_SS | Start-to-Start | Common in concurrent work |
| PR_SF | Start-to-Finish | Rare — flag if found |

---

<a name="taskrsrc"></a>
## TASKRSRC — Resource Assignments

| Field | Description |
|-------|-------------|
| taskrsrc_id | Assignment ID |
| task_id | Activity reference |
| proj_id | Project |
| rsrc_id | Resource reference |
| acct_id | Cost account |
| rsrc_type | Resource type |
| target_qty | Planned quantity |
| target_lag_drtn_hr_cnt | Planned lag |
| target_cost | Planned cost |
| act_reg_qty | Actual regular qty |
| act_ot_qty | Actual overtime qty |
| act_reg_cost | Actual regular cost |
| act_ot_cost | Actual overtime cost |
| remain_qty | Remaining quantity |
| remain_cost | Remaining cost |
| remain_drtn_hr_cnt | Remaining duration (hours) |
| target_start_date | Planned start |
| target_end_date | Planned finish |
| act_start_date | Actual start |
| act_end_date | Actual finish |
| pend_complete_pct | Pending % complete |
| target_crv | Planned curve |
| remain_crv | Remaining curve |
| act_this_per_cost | Cost this period |
| act_this_per_qty | Qty this period |

---

<a name="rsrc"></a>
## RSRC — Resources

| Field | Description |
|-------|-------------|
| rsrc_id | Resource ID |
| parent_rsrc_id | Parent resource |
| rsrc_short_name | Resource code |
| rsrc_name | Resource name |
| rsrc_type | RT_Labor / RT_Nonlabor / RT_Matrl |
| unit_id | Unit of measure |
| def_qty_per_hr | Default qty/hour |
| clndr_id | Calendar assignment |
| max_qty_per_hr | Max qty/hour |
| email_addr | Email |
| employee_code | Employee code |

---

<a name="rsrcrate"></a>
## RSRCRATE — Resource Rates

| Field | Description |
|-------|-------------|
| rsrcrate_id | Rate ID |
| rsrc_id | Resource reference |
| max_qty_per_hr | Max quantity per hour |
| cost_per_qty | Cost per unit |
| start_date | Rate effective date |
| shift_period_id | Shift period reference |

---

<a name="actvtype"></a>
## ACTVTYPE — Activity Code Types

| Field | Description |
|-------|-------------|
| actv_code_type_id | Type ID |
| actv_code_type | Type name |
| proj_id | Project (null = global) |
| seq_num | Sort order |
| actv_short_len | Short code length |
| super_flag | Super flag |

---

<a name="actvcode"></a>
## ACTVCODE — Activity Code Values

| Field | Description |
|-------|-------------|
| actv_code_id | Code value ID |
| parent_actv_code_id | Parent code (hierarchy) |
| actv_code_type_id | Code type reference |
| actv_code_name | Code description |
| short_name | Short code |
| seq_num | Sort order |
| color | Display color |

---

<a name="taskactv"></a>
## TASKACTV — Task Activity Code Assignments

| Field | Description |
|-------|-------------|
| task_id | Activity reference |
| actv_code_type_id | Code type |
| actv_code_id | Code value |
| proj_id | Project |

---

<a name="udftype"></a>
## UDFTYPE — User Defined Field Types

| Field | Description |
|-------|-------------|
| udf_type_id | UDF type ID |
| table_name | Target table (TASK, PROJECT, etc.) |
| udf_type_name | Internal name |
| udf_type_label | Display label |
| logical_data_type | Data type (UDF_TEXT, UDF_DOUBLE, UDF_INT, UDF_DATE, UDF_CODE, UDF_INDICATOR) |
| super_flag | Global flag |

---

<a name="udfvalue"></a>
## UDFVALUE — User Defined Field Values

| Field | Description |
|-------|-------------|
| udf_type_id | UDF type reference |
| fk_id | Foreign key (e.g., task_id) |
| proj_id | Project |
| udf_date | Date value |
| udf_number | Numeric value |
| udf_text | Text value |
| udf_code_id | Code value reference |

---

<a name="pcattype"></a>
## PCATTYPE — Project Code Types

| Field | Description |
|-------|-------------|
| proj_catg_type_id | Type ID |
| proj_catg_short_len | Short code length |
| proj_catg_type | Type name |
| seq_num | Sort order |

---

<a name="pcatval"></a>
## PCATVAL — Project Code Values

| Field | Description |
|-------|-------------|
| proj_catg_id | Value ID |
| proj_catg_type_id | Type reference |
| parent_proj_catg_id | Parent (hierarchy) |
| proj_catg_short_name | Short code |
| proj_catg_name | Description |
| seq_num | Sort order |

---

<a name="projpcat"></a>
## PROJPCAT — Project Code Assignments

| Field | Description |
|-------|-------------|
| proj_id | Project |
| proj_catg_type_id | Code type |
| proj_catg_id | Code value |

---

<a name="taskfin"></a>
## TASKFIN — Task Financial Periods

Earned value period-by-period data at the task level.

| Field | Description |
|-------|-------------|
| taskfin_id | Record ID |
| task_id | Activity |
| proj_id | Project |
| fin_dates_id | Financial period |
| act_cost | Actual cost |
| act_qty | Actual quantity |

---

<a name="trsrcfin"></a>
## TRSRCFIN — Resource Financial Periods

Earned value period-by-period at the resource assignment level.

| Field | Description |
|-------|-------------|
| trsrcfin_id | Record ID |
| taskrsrc_id | Resource assignment |
| fin_dates_id | Financial period |
| act_cost | Actual cost |
| act_qty | Actual quantity |

---

<a name="account"></a>
## ACCOUNT — Cost Accounts

| Field | Description |
|-------|-------------|
| acct_id | Account ID |
| parent_acct_id | Parent account |
| acct_short_name | Account code |
| acct_name | Account name |
| acct_seq_num | Sort order |
| acct_descr | Description |

---

<a name="memotype"></a>
## MEMOTYPE — Notebook Topics

| Field | Description |
|-------|-------------|
| memo_type_id | Topic ID |
| memo_type | Topic name |
| proj_id | Project (null = global) |
| seq_num | Sort order |

---

<a name="taskmemo"></a>
## TASKMEMO — Activity Notebooks

| Field | Description |
|-------|-------------|
| memo_id | Notebook entry ID |
| task_id | Activity |
| proj_id | Project |
| memo_type_id | Topic reference |
| task_memo | Notebook text content |

---

<a name="wbsmemo"></a>
## WBSMEMO — WBS Notebooks

| Field | Description |
|-------|-------------|
| wbs_memo_id | Entry ID |
| wbs_id | WBS node |
| proj_id | Project |
| memo_type_id | Topic |
| wbs_memo | Text content |

---

<a name="projmemo"></a>
## PROJMEMO — Project Notebooks

| Field | Description |
|-------|-------------|
| proj_memo_id | Entry ID |
| proj_id | Project |
| memo_type_id | Topic |
| proj_memo | Text content |

---

## Additional Tables (Less Common)

### TASKDOC / PROJDOCS — Document References
Links to external documents attached to activities or projects.

### ROLES / ROLERATE / RSRCROLE — Role Management
Role definitions, rates, and resource-to-role assignments.

### SHIFT / SHIFTPER — Shift Definitions
Shift patterns and shift periods for resource leveling.

### RCATTYPE / RCATVAL / RSRCCAT — Resource Codes
Resource categorization system (parallel to activity codes).

### RISKTYPE / RISK / RISKTYPES — Risk Register
Risk categories, individual risks, and risk-to-type assignments.

---

## Parsing Pitfalls — Quick Reference

| Pitfall | Detail |
|---------|--------|
| **Tab delimiters** | XER uses `\t` — never commas or spaces. Fields may contain commas/spaces that are NOT delimiters. |
| **Empty fields** | Empty strings between tabs — not NULL, not "N/A" |
| **Dates** | Always `YYYY-MM-DD HH:MM`, UTC timezone |
| **Durations** | ALL in hours. Divide by `day_hr_cnt` from CALENDAR for workdays. |
| **Multi-project** | XER can contain multiple projects. Filter by `proj_id`. |
| **LOE/WBS Summary** | Exclude `TT_LOE` and `TT_WBS` from critical path analysis. |
| **Constraints** | Hard constraints distort float. Flag `cstr_type` activities. |
| **%F vs %R mismatch** | If field count doesn't match data columns, the import grid will be blank in P6. |
| **Encoding** | Try UTF-8 first, then CP1252, then Latin-1. |
| **CRLF** | P6 expects `\r\n` line endings when importing. |
| **P6 24.12 field counts** | PROJECT=72, SCHEDOPTIONS=26, PROJWBS=27, TASK=62 (incl. crt_path_num), TASKPRED=12 |
