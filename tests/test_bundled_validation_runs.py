#!/usr/bin/env python3
"""The bundled validation stubs must actually bind on a plain clone.

The README tells a reader that `validate_schedule` and `aace_31r_compliance`
run end-to-end from a clone, using the `validation.py` and `config_profiles.py`
that ship in scripts/. That was false: the import stanza pulled `audit_trail`
(which does NOT ship here) in the same try block, so one missing module
discarded the two that were present, both names fell back to None, and both
functions raised RuntimeError with their dependencies sitting next to them.

The fix splits the two import groups. These tests pin the behaviour on both
sides of the split, so the claim in the README cannot quietly go false again:

  - the validation pair binds and the two functions return real objects;
  - the manifest guard still fires when the audit-trail module is genuinely
    absent, which is the state of a plain clone and the state CI runs in.

Run with: python tests/test_bundled_validation_runs.py
"""
import os
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'scripts'))

import xer_parser  # noqa: E402
from xer_parser import (  # noqa: E402
    parse_xer,
    validate_schedule,
    aace_31r_compliance,
    generate_xer_manifest,
    BLOCK,
    WARN,
)

TAB = '\t'


def _synthetic_xer():
    """A minimal but structurally valid XER, built in memory.

    Real values in the shapes P6 actually emits: hour-denominated durations,
    'YYYY-MM-DD HH:MM' dates, a TASKPRED tie so the logic check has something
    to pass on, and a decodable Monday-to-Friday clndr_data block.
    """
    clndr = (
        '(0||CalendarData()('
        '0||DaysOfWeek()('
        '(0||1()())'
        '(0||2()((0||0(s|08:00|f|16:00)()))) '
        '(0||3()((0||0(s|08:00|f|16:00)())))'
        '(0||4()((0||0(s|08:00|f|16:00)())))'
        '(0||5()((0||0(s|08:00|f|16:00)())))'
        '(0||6()((0||0(s|08:00|f|16:00)())))'
        '(0||7()())'
        ')))'
    )
    lines = [
        TAB.join(['ERMHDR', '24.12', '2026-01-05', 'Project', 'admin',
                  'Test User', 'dbxDB', 'Project Management', 'CAD']),
        TAB.join(['%T', 'PROJECT']),
        TAB.join(['%F', 'proj_id', 'proj_short_name', 'proj_long_name',
                  'last_recalc_date', 'plan_start_date', 'plan_end_date',
                  'scd_end_date']),
        TAB.join(['%R', '1', 'SYNTH', 'Synthetic Validation Project',
                  '2026-01-05 08:00', '2026-01-05 08:00',
                  '2026-03-27 16:00', '2026-03-27 16:00']),
        TAB.join(['%T', 'PROJWBS']),
        TAB.join(['%F', 'wbs_id', 'parent_wbs_id', 'wbs_name',
                  'wbs_short_name', 'proj_id']),
        TAB.join(['%R', 'W1', '', 'Synthetic Project', 'W1', '1']),
        TAB.join(['%R', 'W2', 'W1', 'Structures', 'W2', '1']),
        TAB.join(['%R', 'W3', 'W2', 'Foundations', 'W3', '1']),
        TAB.join(['%T', 'CALENDAR']),
        TAB.join(['%F', 'clndr_id', 'clndr_name', 'day_hr_cnt',
                  'week_hr_cnt', 'clndr_data']),
        TAB.join(['%R', 'C1', '5 x 8 Standard', '8', '40', clndr]),
        TAB.join(['%T', 'TASK']),
        TAB.join(['%F', 'task_id', 'task_code', 'task_name', 'proj_id', 'wbs_id',
                  'clndr_id', 'status_code', 'task_type', 'phys_complete_pct',
                  'target_drtn_hr_cnt', 'remain_drtn_hr_cnt',
                  'total_float_hr_cnt', 'target_start_date', 'target_end_date',
                  'driving_path_flag', 'cstr_type']),
        TAB.join(['%R', '1001', 'A1000', 'Excavate footings', '1', 'W3', 'C1',
                  'TK_NotStart', 'TT_Task', '0', '40', '40', '0',
                  '2026-01-05 08:00', '2026-01-09 16:00', 'Y', '']),
        TAB.join(['%R', '1002', 'A1010', 'Form and pour footings', '1', 'W3',
                  'C1', 'TK_NotStart', 'TT_Task', '0', '80', '80', '0',
                  '2026-01-12 08:00', '2026-01-23 16:00', 'Y', '']),
        TAB.join(['%T', 'TASKPRED']),
        TAB.join(['%F', 'task_pred_id', 'task_id', 'pred_task_id', 'pred_type',
                  'lag_hr_cnt']),
        TAB.join(['%R', '1', '1002', '1001', 'PR_FS', '0']),
        '%E',
    ]
    return '\r\n'.join(lines) + '\r\n'


def _parsed():
    with tempfile.NamedTemporaryFile('w', suffix='.xer', delete=False,
                                     encoding='utf-8', newline='') as f:
        f.write(_synthetic_xer())
        path = f.name
    try:
        return parse_xer(path), path
    except Exception:
        os.unlink(path)
        raise


def test_bundled_validation_modules_bind_without_audit_trail():
    """The two modules that DO ship must bind on their own.

    This is the regression: before the import split these were None whenever
    `audit_trail` was missing, which is every plain clone and every CI run.
    """
    assert xer_parser.ValidationReport is not None, (
        'ValidationReport is None — scripts/validation.py ships in this repo '
        'and must bind independently of the unbundled audit_trail module')
    assert xer_parser.Finding is not None, 'Finding is None — see above'
    assert xer_parser.get_profile is not None, (
        'get_profile is None — scripts/config_profiles.py ships in this repo')
    assert xer_parser._VALIDATION_AVAILABLE is True


def test_validate_schedule_runs_end_to_end_on_a_plain_clone():
    """The README claim, executed: a report comes back, not a RuntimeError."""
    data, path = _parsed()
    try:
        report = validate_schedule(data, profile='commercial')
    finally:
        os.unlink(path)

    assert report is not None
    # A report that cannot count severities is not a report.
    assert report.count(BLOCK) == 0, (
        'structurally valid synthetic XER produced BLOCK findings: %s'
        % [str(f) for f in getattr(report, 'findings', [])])
    assert isinstance(report.count(WARN), int)


def test_structure_score_runs_and_scores_the_synthetic_schedule():
    """The score must come back, and must equal the documented arithmetic.

    Asserting the invariant rather than a fixed number: this fixture is a
    deliberately abbreviated export, so it legitimately draws WARN findings
    (field counts below a full P6 24.12 row, activity count below the
    commercial profile floor). What must hold is that the score is derived
    from the findings, not that it lands on a chosen figure.
    """
    data, path = _parsed()
    try:
        result = aace_31r_compliance(data, profile='commercial')
        report = validate_schedule(data, profile='commercial')
    finally:
        os.unlink(path)

    assert isinstance(result, dict)
    assert 0 <= result['score_100'] <= 100
    assert result['grade'] in ('A', 'B', 'C', 'D', 'F')

    expected = 100 - 20 * report.count(BLOCK) - 5 * report.count(WARN)
    expected = max(0, min(100, expected))
    assert result['score_100'] == expected, (
        'score %s does not match 100 - 20*BLOCK(%d) - 5*WARN(%d)'
        % (result['score_100'], report.count(BLOCK), report.count(WARN)))

    # The scoring path is only exercised if findings actually reached it.
    assert report.count(WARN) > 0, (
        'no WARN findings on an abbreviated fixture — the check surface did '
        'not run, so the score arithmetic above proves nothing')


def test_manifest_guard_still_fires_when_audit_trail_is_absent():
    """Guard coverage for the half that is genuinely NOT bundled.

    A plain clone has no audit_trail module, so generate_xer_manifest must
    raise rather than hand back a manifest with missing provenance fields.
    Where the internal module IS importable, it must instead return a dict —
    both directions are pinned so this cannot pass vacuously.
    """
    data, path = _parsed()
    try:
        if xer_parser.generate_manifest is None:
            assert xer_parser._AUDIT_TRAIL_AVAILABLE is False
            raised = None
            try:
                generate_xer_manifest(data, path)
            except RuntimeError as exc:
                raised = exc
            assert raised is not None, (
                'generate_xer_manifest returned a manifest with no audit-trail '
                'module available; the provenance guard did not fire')
            assert 'cannot build manifest' in str(raised)
        else:
            assert xer_parser._AUDIT_TRAIL_AVAILABLE is True
            manifest = generate_xer_manifest(data, path)
            assert isinstance(manifest, dict)
    finally:
        os.unlink(path)


if __name__ == '__main__':
    tests = [
        test_bundled_validation_modules_bind_without_audit_trail,
        test_validate_schedule_runs_end_to_end_on_a_plain_clone,
        test_structure_score_runs_and_scores_the_synthetic_schedule,
        test_manifest_guard_still_fires_when_audit_trail_is_absent,
    ]
    for t in tests:
        t()
        print('PASS  %s' % t.__name__)
    print('\n%d/%d passed' % (len(tests), len(tests)))
