#!/usr/bin/env python3
"""
Tests for compute_half_step_xer — AACE 29R-03 MIP 3.4 half-step XER generator.

MIP 3.4 ("Observational / Dynamic / Contemporaneous Split") produces
a "half-step" schedule: take the period-START schedule (base), apply ONLY the
progress fields from the next update, and output a XER that isolates progress
impact from logic-revision impact.

Tests cover:
  - Smoke: 3 activities, A complete + B in-progress + C not-started
  - Added activity in updated (not in base) → unmatched_in_updated; NOT added to output
  - Removed activity in updated (in base, not in updated) → unmatched_in_base; preserved in output
  - AACE 29R-03 MIP 3.4 attribution appears in docstring and PROJECT row
  - Logic (TASKPRED) is preserved verbatim from base
  - Forbidden fields (target_drtn_hr_cnt, task_name) are NOT copied from updated
  - Output XER is re-parseable with same activity count and relationship count as base
"""

import os
import sys
import tempfile

SKILL_SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts')
if SKILL_SCRIPTS not in sys.path:
    sys.path.insert(0, SKILL_SCRIPTS)

from xer_parser import (
    parse_xer, generate_xer, get_table, compute_half_step_xer,
    COMPLETE_STATUS, ACTIVE_STATUS, NOT_STARTED_STATUS,
)

TAB = '\t'


# ──────────────────────────────────────────────────────────────────────────────
# XER BUILDERS
# ──────────────────────────────────────────────────────────────────────────────

def _make_task_row(task_id, task_code, task_name, status, target_drtn,
                   remain_drtn, phys_pct, act_start='', act_end='',
                   early_start='', early_end=''):
    """Build a single TASK %R line string."""
    return TAB.join([
        '%R', task_id, task_code, task_name, 'PROJ1', 'W1', 'C1',
        status, 'TT_Task', str(phys_pct),
        str(target_drtn), str(remain_drtn), '0',
        '2026-01-01 08:00', '2026-01-31 16:00',
        act_start, act_end, early_start, early_end, 'N', '',
    ])


TASK_FIELDS = TAB.join([
    '%F', 'task_id', 'task_code', 'task_name', 'proj_id', 'wbs_id', 'clndr_id',
    'status_code', 'task_type', 'phys_complete_pct',
    'target_drtn_hr_cnt', 'remain_drtn_hr_cnt', 'total_float_hr_cnt',
    'target_start_date', 'target_end_date',
    'act_start_date', 'act_end_date', 'early_start_date', 'early_end_date',
    'driving_path_flag', 'cstr_type',
])


def _make_xer(tasks_rows, pred_rows=None, extra_proj_fields=None):
    """Build a minimal XER string from lists of pre-built %R row strings."""
    pred_rows = pred_rows or []
    lines = [
        TAB.join(['ERMHDR', '24.12', '2026-05-09 08:00', 'Project',
                  'admin', 'Test Admin', 'dbxTest', 'Project Management', 'CAD']),
        TAB.join(['%T', 'PROJECT']),
        TAB.join(['%F', 'proj_id', 'proj_short_name', 'last_recalc_date',
                  'plan_start_date', 'plan_end_date', 'proj_url']),
        TAB.join(['%R', 'PROJ1', 'TEST-PROJ', '2026-05-01 00:00',
                  '2026-01-01 00:00', '2026-12-31 00:00', '']),
        TAB.join(['%T', 'PROJWBS']),
        TAB.join(['%F', 'wbs_id', 'parent_wbs_id', 'wbs_name', 'proj_id']),
        TAB.join(['%R', 'W1', '', 'Root WBS', 'PROJ1']),
        TAB.join(['%T', 'CALENDAR']),
        TAB.join(['%F', 'clndr_id', 'clndr_name', 'day_hr_cnt', 'week_hr_cnt', 'clndr_data']),
        TAB.join(['%R', 'C1', '5-Day', '8', '40', '']),
        TAB.join(['%T', 'TASK']),
        TASK_FIELDS,
    ] + tasks_rows

    if pred_rows:
        lines += [
            TAB.join(['%T', 'TASKPRED']),
            TAB.join(['%F', 'task_pred_id', 'task_id', 'pred_task_id',
                      'pred_type', 'lag_hr_cnt']),
        ] + pred_rows

    lines.append('%E')
    return '\r\n'.join(lines) + '\r\n'


def _write_temp(content):
    """Write content to a temp XER file and return its path."""
    with tempfile.NamedTemporaryFile('w', suffix='.xer', delete=False, encoding='utf-8') as f:
        f.write(content)
        return f.name


# ──────────────────────────────────────────────────────────────────────────────
# TEST 1: Smoke test — 3 activities (A complete, B in-progress, C not-started)
# ──────────────────────────────────────────────────────────────────────────────

def test_smoke_three_activities():
    """
    Base: A/B/C all not-started.
    Updated: A complete, B in-progress (50%), C not-started.
    Assert:
      - matched_count == 3
      - progressed_count == 2  (A and B have progress; C has none)
      - unmatched_in_updated == []
      - output file exists
      - re-parse: A has act_start_date + act_end_date
      - re-parse: B has remain_drtn_hr_cnt < original AND phys_complete_pct == '50'
      - re-parse: C is unchanged (still TK_NotStart, remain == target)
    """
    base_rows = [
        _make_task_row('T1', 'TASK-A', 'Activity A', NOT_STARTED_STATUS, 40, 40, 0),
        _make_task_row('T2', 'TASK-B', 'Activity B', NOT_STARTED_STATUS, 80, 80, 0),
        _make_task_row('T3', 'TASK-C', 'Activity C', NOT_STARTED_STATUS, 40, 40, 0),
    ]
    updated_rows = [
        _make_task_row('T1', 'TASK-A', 'Activity A', COMPLETE_STATUS, 40, 0, 100,
                       act_start='2026-01-05 08:00', act_end='2026-01-10 16:00',
                       early_start='2026-01-05 08:00', early_end='2026-01-10 16:00'),
        _make_task_row('T2', 'TASK-B', 'Activity B', ACTIVE_STATUS, 80, 40, 50,
                       act_start='2026-01-11 08:00'),
        _make_task_row('T3', 'TASK-C', 'Activity C', NOT_STARTED_STATUS, 40, 40, 0),
    ]

    base_path = _write_temp(_make_xer(base_rows))
    updated_path = _write_temp(_make_xer(updated_rows))
    out_fd, out_path = tempfile.mkstemp(suffix='.xer')
    os.close(out_fd)

    try:
        result = compute_half_step_xer(base_path, updated_path, out_path)

        # Summary dict checks
        assert result['matched_count'] == 3, f"Expected 3 matched, got {result['matched_count']}"
        assert result['progressed_count'] == 2, \
            f"Expected 2 progressed (A+B), got {result['progressed_count']}"
        assert result['unmatched_in_updated'] == [], \
            f"Expected no unmatched_in_updated, got {result['unmatched_in_updated']}"
        assert result['unmatched_in_base'] == [], \
            f"Expected no unmatched_in_base, got {result['unmatched_in_base']}"

        # Output file must exist
        assert os.path.exists(out_path), "Output XER file was not created"
        assert os.path.getsize(out_path) > 0, "Output XER file is empty"

        # Re-parse and verify field values
        reparsed = parse_xer(out_path)
        tasks = {t['task_code']: t for t in get_table(reparsed, 'TASK')}

        # A: should be TK_Complete with act_start + act_end
        assert tasks['TASK-A']['status_code'] == COMPLETE_STATUS, \
            f"TASK-A should be complete, got {tasks['TASK-A']['status_code']}"
        assert tasks['TASK-A']['act_start_date'] == '2026-01-05 08:00', \
            f"TASK-A act_start wrong: {tasks['TASK-A']['act_start_date']}"
        assert tasks['TASK-A']['act_end_date'] == '2026-01-10 16:00', \
            f"TASK-A act_end wrong: {tasks['TASK-A']['act_end_date']}"
        # Anchor fields should be copied for completed activity
        assert tasks['TASK-A']['early_start_date'] == '2026-01-05 08:00', \
            f"TASK-A early_start wrong: {tasks['TASK-A']['early_start_date']}"

        # B: should be TK_Active with remain_drtn_hr_cnt == '40' and phys_pct == '50'
        assert tasks['TASK-B']['status_code'] == ACTIVE_STATUS, \
            f"TASK-B should be active, got {tasks['TASK-B']['status_code']}"
        assert tasks['TASK-B']['remain_drtn_hr_cnt'] == '40', \
            f"TASK-B remain_drtn wrong: {tasks['TASK-B']['remain_drtn_hr_cnt']}"
        assert tasks['TASK-B']['phys_complete_pct'] == '50', \
            f"TASK-B phys_pct wrong: {tasks['TASK-B']['phys_complete_pct']}"
        assert tasks['TASK-B']['act_start_date'] == '2026-01-11 08:00', \
            f"TASK-B act_start wrong: {tasks['TASK-B']['act_start_date']}"
        # B is not complete so target_drtn should be unchanged at base value
        assert tasks['TASK-B']['target_drtn_hr_cnt'] == '80', \
            f"TASK-B target_drtn should be base 80, got {tasks['TASK-B']['target_drtn_hr_cnt']}"

        # C: should be unchanged — still TK_NotStart, remain == 40
        assert tasks['TASK-C']['status_code'] == NOT_STARTED_STATUS, \
            f"TASK-C should still be not-started"
        assert tasks['TASK-C']['remain_drtn_hr_cnt'] == '40', \
            f"TASK-C remain_drtn should still be 40"
        assert tasks['TASK-C']['act_start_date'] == '', \
            f"TASK-C should have no act_start, got {tasks['TASK-C']['act_start_date']}"

    finally:
        for p in [base_path, updated_path, out_path]:
            if os.path.exists(p):
                os.unlink(p)


# ──────────────────────────────────────────────────────────────────────────────
# TEST 2: Added activity in updated (not in base) → unmatched_in_updated
# ──────────────────────────────────────────────────────────────────────────────

def test_added_activity_in_updated_not_added_to_output():
    """
    Base: 2 activities (TASK-A, TASK-B).
    Updated: 3 activities (TASK-A, TASK-B, TASK-NEW).
    Assert:
      - unmatched_in_updated == ['TASK-NEW']
      - Output XER does NOT contain TASK-NEW
      - matched_count == 2
    """
    base_rows = [
        _make_task_row('T1', 'TASK-A', 'Activity A', NOT_STARTED_STATUS, 40, 40, 0),
        _make_task_row('T2', 'TASK-B', 'Activity B', NOT_STARTED_STATUS, 40, 40, 0),
    ]
    updated_rows = [
        _make_task_row('T1', 'TASK-A', 'Activity A', COMPLETE_STATUS, 40, 0, 100,
                       act_start='2026-01-05 08:00', act_end='2026-01-10 16:00'),
        _make_task_row('T2', 'TASK-B', 'Activity B', NOT_STARTED_STATUS, 40, 40, 0),
        _make_task_row('T99', 'TASK-NEW', 'Brand New Activity', NOT_STARTED_STATUS, 24, 24, 0),
    ]

    base_path = _write_temp(_make_xer(base_rows))
    updated_path = _write_temp(_make_xer(updated_rows))
    out_fd, out_path = tempfile.mkstemp(suffix='.xer')
    os.close(out_fd)

    try:
        result = compute_half_step_xer(base_path, updated_path, out_path)

        assert result['unmatched_in_updated'] == ['TASK-NEW'], \
            f"Expected ['TASK-NEW'], got {result['unmatched_in_updated']}"
        assert result['matched_count'] == 2, \
            f"Expected 2 matched, got {result['matched_count']}"

        # Output XER must NOT contain TASK-NEW
        reparsed = parse_xer(out_path)
        output_codes = {t['task_code'] for t in get_table(reparsed, 'TASK')}
        assert 'TASK-NEW' not in output_codes, \
            f"TASK-NEW should NOT appear in half-step output; found codes: {output_codes}"
        assert 'TASK-A' in output_codes, "TASK-A should be in output"
        assert 'TASK-B' in output_codes, "TASK-B should be in output"

    finally:
        for p in [base_path, updated_path, out_path]:
            if os.path.exists(p):
                os.unlink(p)


# ──────────────────────────────────────────────────────────────────────────────
# TEST 3: Removed activity in updated (in base, not in updated) → unmatched_in_base
# ──────────────────────────────────────────────────────────────────────────────

def test_removed_activity_preserved_in_output():
    """
    Base: 3 activities (TASK-A, TASK-B, TASK-C).
    Updated: 2 activities (TASK-A, TASK-B — TASK-C was deleted in the update).
    Assert:
      - unmatched_in_base == ['TASK-C']
      - Output XER preserves all 3 base activities
      - TASK-C stays not-started (no progress to apply)
    """
    base_rows = [
        _make_task_row('T1', 'TASK-A', 'Activity A', NOT_STARTED_STATUS, 40, 40, 0),
        _make_task_row('T2', 'TASK-B', 'Activity B', NOT_STARTED_STATUS, 40, 40, 0),
        _make_task_row('T3', 'TASK-C', 'Activity C', NOT_STARTED_STATUS, 40, 40, 0),
    ]
    updated_rows = [
        _make_task_row('T1', 'TASK-A', 'Activity A', COMPLETE_STATUS, 40, 0, 100,
                       act_start='2026-01-05 08:00', act_end='2026-01-10 16:00'),
        _make_task_row('T2', 'TASK-B', 'Activity B', ACTIVE_STATUS, 40, 20, 50,
                       act_start='2026-01-11 08:00'),
        # TASK-C deleted from updated — simulates contractor removing an activity
    ]

    base_path = _write_temp(_make_xer(base_rows))
    updated_path = _write_temp(_make_xer(updated_rows))
    out_fd, out_path = tempfile.mkstemp(suffix='.xer')
    os.close(out_fd)

    try:
        result = compute_half_step_xer(base_path, updated_path, out_path)

        assert result['unmatched_in_base'] == ['TASK-C'], \
            f"Expected ['TASK-C'], got {result['unmatched_in_base']}"
        assert result['matched_count'] == 2, \
            f"Expected 2 matched, got {result['matched_count']}"

        # Output must have all 3 base activities
        reparsed = parse_xer(out_path)
        tasks = {t['task_code']: t for t in get_table(reparsed, 'TASK')}
        assert len(tasks) == 3, f"Expected 3 tasks in output, got {len(tasks)}: {list(tasks)}"

        # TASK-C should still be not-started (no progress from updated)
        assert 'TASK-C' in tasks, "TASK-C must be preserved in output"
        assert tasks['TASK-C']['status_code'] == NOT_STARTED_STATUS, \
            f"TASK-C should be NOT_STARTED, got {tasks['TASK-C']['status_code']}"
        assert tasks['TASK-C']['act_start_date'] == '', \
            f"TASK-C should have no act_start"

    finally:
        for p in [base_path, updated_path, out_path]:
            if os.path.exists(p):
                os.unlink(p)


# ──────────────────────────────────────────────────────────────────────────────
# TEST 4: AACE 29R-03 MIP 3.4 attribution in docstring + PROJECT row
# ──────────────────────────────────────────────────────────────────────────────

def test_mip34_attribution_in_docstring_and_project_row():
    """
    AACE 29R-03 MIP 3.4 must be cited in the function docstring.
    The PROJECT row's proj_url field must carry the attribution text.
    """
    import inspect

    # Check docstring contains the AACE citation
    doc = inspect.getdoc(compute_half_step_xer)
    assert doc is not None, "compute_half_step_xer has no docstring"
    assert 'AACE 29R-03' in doc, \
        "Docstring must cite AACE 29R-03"
    assert 'MIP 3.4' in doc, \
        "Docstring must mention MIP 3.4"

    # Check PROJECT row gets the attribution
    base_rows = [_make_task_row('T1', 'TASK-A', 'Activity A', NOT_STARTED_STATUS, 40, 40, 0)]
    updated_rows = [_make_task_row('T1', 'TASK-A', 'Activity A', ACTIVE_STATUS, 40, 20, 50,
                                   act_start='2026-01-05 08:00')]

    base_path = _write_temp(_make_xer(base_rows))
    updated_path = _write_temp(_make_xer(updated_rows))
    out_fd, out_path = tempfile.mkstemp(suffix='.xer')
    os.close(out_fd)

    try:
        compute_half_step_xer(base_path, updated_path, out_path)

        reparsed = parse_xer(out_path)
        projects = get_table(reparsed, 'PROJECT')
        assert projects, "No PROJECT records in output XER"

        proj = projects[0]
        # Check either proj_url or web_site carries the attribution
        attribution_found = (
            'MIP 3.4' in proj.get('proj_url', '') or
            'MIP 3.4' in proj.get('web_site', '')
        )
        assert attribution_found, \
            f"MIP 3.4 attribution not found in PROJECT row. proj_url={proj.get('proj_url')!r}"
        assert 'AACE 29R-03' in (proj.get('proj_url', '') + proj.get('web_site', '')), \
            "AACE 29R-03 must appear in PROJECT attribution field"

    finally:
        for p in [base_path, updated_path, out_path]:
            if os.path.exists(p):
                os.unlink(p)


# ──────────────────────────────────────────────────────────────────────────────
# TEST 5: Logic (TASKPRED) is preserved from BASE, not updated
# ──────────────────────────────────────────────────────────────────────────────

def test_logic_preserved_from_base():
    """
    Base has FS relationship A→B.
    Updated has a different relationship (B→A, reversed) — a typical
    contractor logic revision.
    Half-step output must have the BASE relationship (A→B), not the updated one.
    Activity counts and relationship counts must match base.
    """
    base_rows = [
        _make_task_row('T1', 'TASK-A', 'Activity A', NOT_STARTED_STATUS, 40, 40, 0),
        _make_task_row('T2', 'TASK-B', 'Activity B', NOT_STARTED_STATUS, 40, 40, 0),
    ]
    base_pred_rows = [
        TAB.join(['%R', 'P1', 'T2', 'T1', 'PR_FS', '0']),  # A→B (FS)
    ]

    updated_rows = [
        _make_task_row('T1', 'TASK-A', 'Activity A', ACTIVE_STATUS, 40, 20, 50,
                       act_start='2026-01-05 08:00'),
        _make_task_row('T2', 'TASK-B', 'Activity B', NOT_STARTED_STATUS, 40, 40, 0),
    ]
    # Updated has REVERSED logic: B→A (contractor revision — should NOT appear in half-step)
    updated_pred_rows = [
        TAB.join(['%R', 'P1', 'T1', 'T2', 'PR_FS', '0']),  # B→A (reversed)
    ]

    base_path = _write_temp(_make_xer(base_rows, base_pred_rows))
    updated_path = _write_temp(_make_xer(updated_rows, updated_pred_rows))
    out_fd, out_path = tempfile.mkstemp(suffix='.xer')
    os.close(out_fd)

    try:
        compute_half_step_xer(base_path, updated_path, out_path)
        reparsed = parse_xer(out_path)

        # Activity count must match base
        base_data = parse_xer(base_path)
        assert len(get_table(reparsed, 'TASK')) == len(get_table(base_data, 'TASK')), \
            "Activity count in output must match base"

        # Relationship count must match base
        output_preds = get_table(reparsed, 'TASKPRED')
        base_preds = get_table(base_data, 'TASKPRED')
        assert len(output_preds) == len(base_preds), \
            f"Relationship count mismatch: base={len(base_preds)}, output={len(output_preds)}"

        # The relationship direction must be A→B (base), not B→A (updated)
        # In the base: pred_task_id='T1' (A), task_id='T2' (B)
        assert output_preds[0]['pred_task_id'] == 'T1', \
            f"Logic should be A→B (pred T1); got pred={output_preds[0]['pred_task_id']}"
        assert output_preds[0]['task_id'] == 'T2', \
            f"Logic should be A→B (task T2); got task={output_preds[0]['task_id']}"

    finally:
        for p in [base_path, updated_path, out_path]:
            if os.path.exists(p):
                os.unlink(p)


# ──────────────────────────────────────────────────────────────────────────────
# TEST 6: Forbidden fields (target_drtn_hr_cnt, task_name) NOT copied
# ──────────────────────────────────────────────────────────────────────────────

def test_forbidden_fields_not_copied():
    """
    Updated changes task_name and target_drtn_hr_cnt (planned duration).
    Half-step must preserve the BASE values for both — these are logic-revision
    fields, not progress fields.
    """
    base_rows = [
        _make_task_row('T1', 'TASK-A', 'Original Name', NOT_STARTED_STATUS, 80, 80, 0),
    ]
    updated_rows = [
        # Updated: task_name changed, target_drtn changed from 80→40, but progress is 50%
        _make_task_row('T1', 'TASK-A', 'Changed Name', ACTIVE_STATUS, 40, 20, 50,
                       act_start='2026-01-05 08:00'),
    ]

    base_path = _write_temp(_make_xer(base_rows))
    updated_path = _write_temp(_make_xer(updated_rows))
    out_fd, out_path = tempfile.mkstemp(suffix='.xer')
    os.close(out_fd)

    try:
        compute_half_step_xer(base_path, updated_path, out_path)
        reparsed = parse_xer(out_path)

        tasks = {t['task_code']: t for t in get_table(reparsed, 'TASK')}
        assert 'TASK-A' in tasks

        # task_name must be base value
        assert tasks['TASK-A']['task_name'] == 'Original Name', \
            f"task_name should be base 'Original Name', got {tasks['TASK-A']['task_name']!r}"

        # target_drtn_hr_cnt must be base value (80, not updated 40)
        assert tasks['TASK-A']['target_drtn_hr_cnt'] == '80', \
            f"target_drtn should be base '80', got {tasks['TASK-A']['target_drtn_hr_cnt']!r}"

        # Progress fields should be applied
        assert tasks['TASK-A']['status_code'] == ACTIVE_STATUS, \
            f"status_code should be active (from progress)"
        assert tasks['TASK-A']['phys_complete_pct'] == '50', \
            f"phys_complete_pct should be '50' (from progress)"

    finally:
        for p in [base_path, updated_path, out_path]:
            if os.path.exists(p):
                os.unlink(p)


# ──────────────────────────────────────────────────────────────────────────────
# TEST 7: P6 re-importability — output XER re-parses with same counts as base
# ──────────────────────────────────────────────────────────────────────────────

def test_output_xer_is_reparseable_and_matches_base():
    """
    The half-step XER must be re-importable into P6.
    Re-parsing the output must yield:
      - Same activity count as base
      - Same relationship count as base
      - ERMHDR present (required for P6 import)
    """
    base_rows = [
        _make_task_row('T1', 'TASK-A', 'Activity A', NOT_STARTED_STATUS, 40, 40, 0),
        _make_task_row('T2', 'TASK-B', 'Activity B', NOT_STARTED_STATUS, 40, 40, 0),
        _make_task_row('T3', 'TASK-C', 'Activity C', NOT_STARTED_STATUS, 40, 40, 0),
    ]
    base_preds = [
        TAB.join(['%R', 'P1', 'T2', 'T1', 'PR_FS', '0']),
        TAB.join(['%R', 'P2', 'T3', 'T2', 'PR_FS', '0']),
    ]
    updated_rows = [
        _make_task_row('T1', 'TASK-A', 'Activity A', COMPLETE_STATUS, 40, 0, 100,
                       act_start='2026-01-05 08:00', act_end='2026-01-10 16:00',
                       early_start='2026-01-05 08:00', early_end='2026-01-10 16:00'),
        _make_task_row('T2', 'TASK-B', 'Activity B', ACTIVE_STATUS, 40, 20, 50,
                       act_start='2026-01-11 08:00'),
        _make_task_row('T3', 'TASK-C', 'Activity C', NOT_STARTED_STATUS, 40, 40, 0),
    ]
    updated_preds = base_preds[:]  # same logic in this scenario

    base_path = _write_temp(_make_xer(base_rows, base_preds))
    updated_path = _write_temp(_make_xer(updated_rows, updated_preds))
    out_fd, out_path = tempfile.mkstemp(suffix='.xer')
    os.close(out_fd)

    try:
        compute_half_step_xer(base_path, updated_path, out_path)

        base_data = parse_xer(base_path)
        reparsed = parse_xer(out_path)

        # ERMHDR must be present (required for P6 import)
        assert reparsed.get('ermhdr', {}).get('raw'), \
            "ERMHDR missing from output XER — P6 will reject this file"

        # Activity count
        base_task_count = len(get_table(base_data, 'TASK'))
        out_task_count = len(get_table(reparsed, 'TASK'))
        assert base_task_count == out_task_count, \
            f"Activity count mismatch: base={base_task_count}, output={out_task_count}"

        # Relationship count
        base_pred_count = len(get_table(base_data, 'TASKPRED'))
        out_pred_count = len(get_table(reparsed, 'TASKPRED'))
        assert base_pred_count == out_pred_count, \
            f"Relationship count mismatch: base={base_pred_count}, output={out_pred_count}"

        # CALENDAR and PROJECT must be present
        assert get_table(reparsed, 'CALENDAR'), "CALENDAR table lost in output"
        assert get_table(reparsed, 'PROJECT'), "PROJECT table lost in output"

    finally:
        for p in [base_path, updated_path, out_path]:
            if os.path.exists(p):
                os.unlink(p)


# ──────────────────────────────────────────────────────────────────────────────
# TEST 8: Early-date anchor logic — only applied when updated is TK_Complete
# ──────────────────────────────────────────────────────────────────────────────

def test_early_date_anchor_only_for_completed():
    """
    early_start_date / early_end_date copied ONLY when updated is TK_Complete
    and base is not.  For in-progress activities these fields are left as-is
    (CPM forward-pass will recompute them).
    """
    base_rows = [
        # Both start with blank early dates
        _make_task_row('T1', 'TASK-A', 'Activity A', NOT_STARTED_STATUS, 40, 40, 0),
        _make_task_row('T2', 'TASK-B', 'Activity B', NOT_STARTED_STATUS, 40, 40, 0),
    ]
    updated_rows = [
        # A is TK_Complete → anchor should copy
        _make_task_row('T1', 'TASK-A', 'Activity A', COMPLETE_STATUS, 40, 0, 100,
                       act_start='2026-01-05 08:00', act_end='2026-01-10 16:00',
                       early_start='2026-01-05 08:00', early_end='2026-01-10 16:00'),
        # B is TK_Active → anchor must NOT copy (CPM re-run will set them)
        _make_task_row('T2', 'TASK-B', 'Activity B', ACTIVE_STATUS, 40, 20, 50,
                       act_start='2026-01-11 08:00',
                       early_start='2026-01-11 08:00', early_end='2026-01-21 16:00'),
    ]

    base_path = _write_temp(_make_xer(base_rows))
    updated_path = _write_temp(_make_xer(updated_rows))
    out_fd, out_path = tempfile.mkstemp(suffix='.xer')
    os.close(out_fd)

    try:
        compute_half_step_xer(base_path, updated_path, out_path)
        reparsed = parse_xer(out_path)
        tasks = {t['task_code']: t for t in get_table(reparsed, 'TASK')}

        # A: should have early dates copied (it's complete)
        assert tasks['TASK-A']['early_start_date'] == '2026-01-05 08:00', \
            f"TASK-A (complete) should have early_start anchored; got {tasks['TASK-A']['early_start_date']!r}"
        assert tasks['TASK-A']['early_end_date'] == '2026-01-10 16:00', \
            f"TASK-A (complete) should have early_end anchored; got {tasks['TASK-A']['early_end_date']!r}"

        # B: early dates should remain blank (base had blank, active doesn't get anchor)
        assert tasks['TASK-B']['early_start_date'] == '', \
            f"TASK-B (active) should NOT have early_start from updated; got {tasks['TASK-B']['early_start_date']!r}"
        assert tasks['TASK-B']['early_end_date'] == '', \
            f"TASK-B (active) should NOT have early_end from updated; got {tasks['TASK-B']['early_end_date']!r}"

    finally:
        for p in [base_path, updated_path, out_path]:
            if os.path.exists(p):
                os.unlink(p)


# ──────────────────────────────────────────────────────────────────────────────
# Runner (plain python fallback — pytest also picks these up automatically)
# ──────────────────────────────────────────────────────────────────────────────

def _run(name, fn):
    try:
        fn()
        print(f"ok  {name}")
        return True
    except AssertionError as e:
        print(f"FAIL {name}: {e}")
        return False
    except Exception as e:
        print(f"ERR  {name}: {type(e).__name__}: {e}")
        return False


if __name__ == '__main__':
    tests = [
        test_smoke_three_activities,
        test_added_activity_in_updated_not_added_to_output,
        test_removed_activity_preserved_in_output,
        test_mip34_attribution_in_docstring_and_project_row,
        test_logic_preserved_from_base,
        test_forbidden_fields_not_copied,
        test_output_xer_is_reparseable_and_matches_base,
        test_early_date_anchor_only_for_completed,
    ]
    passed = sum(_run(t.__name__, t) for t in tests)
    print(f"\n{passed} / {len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
