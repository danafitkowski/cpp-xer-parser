#!/usr/bin/env python3
"""Smoke tests for xer_parser.

Run with: python tests/test_xer_parser.py

No external dependencies — uses tempfile + assert.
Each test builds a minimal synthetic XER in memory so we don't need a fixture file.
"""
import os
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'scripts'))

from xer_parser import (  # noqa: E402
    parse_xer,
    get_table,
    build_udf_map,
    duration_hours_to_days,
    generate_summary,
    generate_xer,
    CONSTRAINT_TYPES,
)

TAB = '\t'


def _tiny_xer():
    lines = [
        TAB.join(['ERMHDR', '24.12', '2026-01-01', 'Project', 'admin',
                  'Test User', 'dbxDB', 'Project Management', 'USD']),
        TAB.join(['%T', 'PROJECT']),
        TAB.join(['%F', 'proj_id', 'proj_short_name', 'proj_long_name',
                  'last_recalc_date', 'plan_start_date', 'plan_end_date', 'scd_end_date']),
        TAB.join(['%R', '1', 'TINY', 'Tiny Test Project',
                  '2026-01-01 00:00', '2026-01-01 00:00',
                  '2026-06-01 00:00', '2026-06-01 00:00']),
        TAB.join(['%T', 'PROJWBS']),
        TAB.join(['%F', 'wbs_id', 'parent_wbs_id', 'wbs_name',
                  'wbs_short_name', 'proj_id']),
        TAB.join(['%R', 'W1', '', 'Root', 'W1', '1']),
        TAB.join(['%R', 'W2', 'W1', 'Child', 'W2', '1']),
        TAB.join(['%T', 'CALENDAR']),
        TAB.join(['%F', 'clndr_id', 'clndr_name', 'day_hr_cnt',
                  'week_hr_cnt', 'clndr_data']),
        TAB.join(['%R', 'C1', '5-Day', '8', '40', '']),
        TAB.join(['%T', 'TASK']),
        TAB.join(['%F', 'task_id', 'task_code', 'task_name', 'proj_id', 'wbs_id',
                  'clndr_id', 'status_code', 'task_type', 'phys_complete_pct',
                  'target_drtn_hr_cnt', 'remain_drtn_hr_cnt', 'total_float_hr_cnt',
                  'target_start_date', 'target_end_date', 'driving_path_flag',
                  'cstr_type']),
        TAB.join(['%R', '1', 'A1', 'Activity One', '1', 'W2', 'C1', 'TK_NotStart',
                  'TT_Task', '0', '40', '40', '0', '2026-02-01 08:00',
                  '2026-02-07 16:00', 'Y', 'CS_MSO']),
        TAB.join(['%R', '2', 'A2', 'Activity Two', '1', 'W2', 'C1', 'TK_NotStart',
                  'TT_Task', '0', '40', '40', '16', '2026-02-08 08:00',
                  '2026-02-14 16:00', 'N', '']),
        TAB.join(['%T', 'TASKPRED']),
        TAB.join(['%F', 'task_pred_id', 'task_id', 'pred_task_id', 'pred_type',
                  'lag_hr_cnt']),
        TAB.join(['%R', '1', '2', '1', 'PR_FS', '0']),
        '%E',
    ]
    return '\r\n'.join(lines) + '\r\n'


def _write_temp(content):
    with tempfile.NamedTemporaryFile('w', suffix='.xer', delete=False, encoding='utf-8') as f:
        f.write(content)
        return f.name


def test_parse_basic():
    path = _write_temp(_tiny_xer())
    try:
        data = parse_xer(path)
        assert 'PROJECT' in data['tables']
        assert 'TASK' in data['tables']
        assert len(get_table(data, 'TASK')) == 2
        assert len(get_table(data, 'TASKPRED')) == 1
    finally:
        os.unlink(path)


def test_ermhdr_9_fields():
    path = _write_temp(_tiny_xer())
    try:
        data = parse_xer(path)
        raw = data['ermhdr']['raw']
        assert len(raw) == 9, f'Expected 9-field ERMHDR, got {len(raw)}'
        assert raw[0] == 'ERMHDR'
        assert data['ermhdr']['version'] == '24.12'
    finally:
        os.unlink(path)


def test_constraint_types_canonical():
    assert CONSTRAINT_TYPES['CS_MSO'] == 'Start On'
    assert CONSTRAINT_TYPES['CS_MEO'] == 'Finish On'
    assert CONSTRAINT_TYPES['CS_MSOA'] == 'Start On or After'
    assert CONSTRAINT_TYPES['CS_MEOB'] == 'Finish On or Before'
    assert CONSTRAINT_TYPES['CS_MANDSTART'] == 'Mandatory Start'
    assert CONSTRAINT_TYPES['CS_MANDFIN'] == 'Mandatory Finish'


def test_generate_roundtrip():
    src = _write_temp(_tiny_xer())
    dst = src + '.out.xer'
    try:
        data = parse_xer(src)
        generate_xer(data, dst)
        reparsed = parse_xer(dst)
        assert len(get_table(reparsed, 'TASK')) == 2
        # Source ERMHDR preserved verbatim
        assert reparsed['ermhdr']['raw'] == data['ermhdr']['raw']
    finally:
        for p in (src, dst):
            if os.path.exists(p):
                os.unlink(p)


def test_constraint_counter():
    """data_quality.constraint_types should count occurrences, not fix at 1."""
    content = '\r\n'.join([
        TAB.join(['ERMHDR', '24.12', '2026-01-01', 'Project', 'u', 'U',
                  'db', 'Project Management', 'USD']),
        TAB.join(['%T', 'PROJECT']),
        TAB.join(['%F', 'proj_id', 'proj_short_name', 'last_recalc_date']),
        TAB.join(['%R', '1', 'X', '2026-01-01 00:00']),
        TAB.join(['%T', 'TASK']),
        TAB.join(['%F', 'task_id', 'task_code', 'task_name', 'proj_id',
                  'task_type', 'status_code', 'cstr_type']),
        TAB.join(['%R', '1', 'A', 'A', '1', 'TT_Task', 'TK_NotStart', 'CS_MSO']),
        TAB.join(['%R', '2', 'B', 'B', '1', 'TT_Task', 'TK_NotStart', 'CS_MSO']),
        TAB.join(['%R', '3', 'C', 'C', '1', 'TT_Task', 'TK_NotStart', 'CS_MEO']),
        '%E',
    ]) + '\r\n'
    path = _write_temp(content)
    try:
        data = parse_xer(path)
        summary = generate_summary(data)
        counts = summary['data_quality']['constraint_types']
        assert counts.get('Start On') == 2, f'expected 2 Start On, got {counts}'
        assert counts.get('Finish On') == 1, f'expected 1 Finish On, got {counts}'
    finally:
        os.unlink(path)


def test_duration_hours_to_days_unrounded_by_default():
    cal = {'hours_per_day': 8}
    assert duration_hours_to_days('12', cal) == 1.5
    assert duration_hours_to_days('12', cal, ndigits=0) == 2


def test_udf_map_keys_on_table():
    """Same fk_id in different tables must not collide."""
    content = '\r\n'.join([
        TAB.join(['ERMHDR', '24.12', '2026-01-01', 'Project', 'u', 'U',
                  'db', 'Project Management', 'USD']),
        TAB.join(['%T', 'UDFTYPE']),
        TAB.join(['%F', 'udf_type_id', 'table_name', 'udf_type_label',
                  'udf_type_name']),
        TAB.join(['%R', 'U1', 'TASK', 'Task Note', 'task_note']),
        TAB.join(['%R', 'U2', 'PROJECT', 'Project Note', 'proj_note']),
        TAB.join(['%T', 'UDFVALUE']),
        TAB.join(['%F', 'udf_type_id', 'fk_id', 'udf_text', 'udf_number', 'udf_date']),
        TAB.join(['%R', 'U1', '100', 'task-note-value', '', '']),
        TAB.join(['%R', 'U2', '100', 'project-note-value', '', '']),
        '%E',
    ]) + '\r\n'
    path = _write_temp(content)
    try:
        data = parse_xer(path)
        udf_map = build_udf_map(data)
        assert ('TASK', '100') in udf_map
        assert ('PROJECT', '100') in udf_map
        assert udf_map[('TASK', '100')][0]['value'] == 'task-note-value'
        assert udf_map[('PROJECT', '100')][0]['value'] == 'project-note-value'
    finally:
        os.unlink(path)


if __name__ == '__main__':
    tests = [
        test_parse_basic,
        test_ermhdr_9_fields,
        test_constraint_types_canonical,
        test_generate_roundtrip,
        test_constraint_counter,
        test_duration_hours_to_days_unrounded_by_default,
        test_udf_map_keys_on_table,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f'ok  {t.__name__}')
        except AssertionError as e:
            print(f'FAIL {t.__name__}: {e}')
            failed += 1
        except Exception as e:
            print(f'FAIL {t.__name__}: {type(e).__name__}: {e}')
            failed += 1
    print('')
    if failed:
        print(f'{failed} / {len(tests)} failures')
        sys.exit(1)
    print(f'{len(tests)} / {len(tests)} passed')
