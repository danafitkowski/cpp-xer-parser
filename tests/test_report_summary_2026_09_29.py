#!/usr/bin/env python3
"""The bundled ValidationReport carries a summary and its worst severity
(2026-09-29).

Run with: python tests/test_report_summary_2026_09_29.py

CPP's internal ValidationReport serialises to a dict with a `summary` block:
the number of findings at each severity, the total, and `worst_severity`,
the worst severity present. A caller reads the headline of a report there,
for example `cpp-critical-path-validator`, which lifts the embedded DCMA-14
report's worst severity to the top of its results. The bundled subset had
`counts` but no `summary` and no `worst_severity`, so that read found
nothing. These tests pin the summary's keys and values, the severity order,
the empty report, `count()` with no argument, and that the output earlier
releases produced (`counts`, and findings in the order they were added) is
unchanged.
"""
import json
import os
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'scripts'))

from validation import (  # noqa: E402
    BLOCK, INFO, PASS, WARN, Finding, ValidationReport,
)
from xer_parser import parse_xer, validate_schedule  # noqa: E402

TAB = '\t'
_SUMMARY_KEYS = ['block', 'warn', 'info', 'pass', 'total', 'worst_severity']


def _report(*severities):
    r = ValidationReport(subject='synthetic', context={'profile': 'test'})
    for i, sev in enumerate(severities):
        r.add(Finding(severity=sev, check_id='CHK-%02d' % i,
                      message='finding %d' % i))
    return r


def test_summary_counts_each_severity_and_the_total():
    r = _report(INFO, BLOCK, PASS, WARN, INFO, BLOCK, INFO)
    assert r.to_dict()['summary'] == {
        'block': 2, 'warn': 1, 'info': 3, 'pass': 1, 'total': 7,
        'worst_severity': BLOCK,
    }


def test_summary_keys_are_the_internal_reports_in_its_order():
    assert list(_report(WARN).to_dict()['summary']) == _SUMMARY_KEYS


def test_worst_severity_ranks_block_over_warn_over_info_over_pass():
    assert _report(PASS, INFO, WARN, BLOCK).worst_severity == BLOCK
    assert _report(BLOCK, WARN, INFO, PASS).worst_severity == BLOCK
    assert _report(INFO, WARN, PASS).worst_severity == WARN
    assert _report(PASS, INFO).worst_severity == INFO
    assert _report(PASS, PASS).worst_severity == PASS


def test_worst_severity_is_the_summarys():
    for sevs in ((WARN, INFO), (INFO,), (PASS, BLOCK)):
        r = _report(*sevs)
        assert r.to_dict()['summary']['worst_severity'] == r.worst_severity


def test_an_empty_report_is_pass_with_nothing_counted():
    r = ValidationReport(subject='empty')
    assert r.worst_severity == PASS
    assert r.to_dict()['summary'] == {
        'block': 0, 'warn': 0, 'info': 0, 'pass': 0, 'total': 0,
        'worst_severity': PASS,
    }


def test_count_with_no_severity_is_the_total():
    r = _report(BLOCK, WARN, WARN, INFO)
    assert r.count() == 4
    assert r.count(None) == 4
    assert (r.count(BLOCK), r.count(WARN), r.count(INFO), r.count(PASS)) == (
        1, 2, 1, 0)


def test_earlier_output_is_unchanged():
    """`counts` stays, and findings keep the order they were added in."""
    r = _report(INFO, BLOCK, PASS, WARN)
    d = r.to_dict()
    assert set(d) == {'subject', 'context', 'summary', 'findings', 'counts'}
    assert d['counts'] == r.counts() == {
        BLOCK: 1, WARN: 1, INFO: 1, PASS: 1}
    assert [f['check_id'] for f in d['findings']] == [
        'CHK-00', 'CHK-01', 'CHK-02', 'CHK-03']
    assert d['subject'] == 'synthetic' and d['context'] == {'profile': 'test'}


def test_the_dict_is_json_serialisable():
    d = _report(BLOCK, INFO).to_dict()
    assert json.loads(json.dumps(d))['summary']['worst_severity'] == BLOCK


def _xer_without_logic():
    """Two activities and no TASKPRED table: validate_schedule raises its
    BLOCK for missing logic, so the report's worst severity is BLOCK."""
    lines = [
        TAB.join(['ERMHDR', '24.12', '2026-01-05', 'Project', 'admin',
                  'Test User', 'dbxDB', 'Project Management', 'CAD']),
        TAB.join(['%T', 'PROJECT']),
        TAB.join(['%F', 'proj_id', 'proj_short_name', 'clndr_id',
                  'last_recalc_date', 'plan_start_date']),
        TAB.join(['%R', '1', 'SYNTH', 'C1', '2026-01-05 08:00',
                  '2026-01-05 08:00']),
        TAB.join(['%T', 'CALENDAR']),
        TAB.join(['%F', 'clndr_id', 'default_flag', 'clndr_name',
                  'day_hr_cnt', 'week_hr_cnt', 'clndr_data']),
        TAB.join(['%R', 'C1', 'Y', 'Standard', '8', '40', '']),
        TAB.join(['%T', 'PROJWBS']),
        TAB.join(['%F', 'wbs_id', 'parent_wbs_id', 'wbs_name',
                  'wbs_short_name', 'proj_id']),
        TAB.join(['%R', 'W1', '', 'Synthetic', 'W1', '1']),
        TAB.join(['%T', 'TASK']),
        TAB.join(['%F', 'task_id', 'task_code', 'task_name', 'proj_id',
                  'wbs_id', 'clndr_id', 'status_code', 'task_type',
                  'target_drtn_hr_cnt', 'remain_drtn_hr_cnt']),
        TAB.join(['%R', '1', 'A1000', 'First', '1', 'W1', 'C1',
                  'TK_NotStart', 'TT_Task', '40', '40']),
        TAB.join(['%R', '2', 'A1010', 'Second', '1', 'W1', 'C1',
                  'TK_NotStart', 'TT_Task', '40', '40']),
        '%E',
    ]
    return '\r\n'.join(lines) + '\r\n'


def test_validate_schedule_reports_its_worst_severity():
    with tempfile.NamedTemporaryFile('w', suffix='.xer', delete=False,
                                     encoding='utf-8', newline='') as f:
        f.write(_xer_without_logic())
        path = f.name
    try:
        report = validate_schedule(parse_xer(path), profile='commercial')
    finally:
        os.unlink(path)
    assert report.count(BLOCK) >= 1, [x.check_id for x in report.findings]
    summary = report.to_dict()['summary']
    assert summary['worst_severity'] == BLOCK
    assert summary['total'] == len(report.findings)
    assert summary['block'] == report.count(BLOCK)


if __name__ == '__main__':
    tests = [f for name, f in list(globals().items())
             if name.startswith('test_') and callable(f)]
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
