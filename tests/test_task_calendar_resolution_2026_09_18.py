"""Regression (2026-09-18): a blank TASK.clndr_id means the project calendar.

MPXJ (Python ``mpxj`` 16.1, ``UniversalProjectWriter(FileFormat.XER)``) converts
an MS Project .mpp into an XER whose TASK.clndr_id is an EMPTY STRING for every
task that carries no task-level calendar, while PROJECT.clndr_id correctly
names the project calendar. That is MS Project's own meaning: no task calendar
= the project calendar.

A consumer that looks the calendar up as ``cal_map.get(task['clndr_id'])`` gets
None for the blank id and falls through to its last resort: 8 h/day in
``duration_hours_to_days``, without a word, and in cpp-cpm-engine a continuous
seven-day week, with an ALERT, unless the caller hands it the project
calendar.

``resolve_task_calendars`` is the one place the chain now lives:

    TASK.clndr_id  ->  PROJECT.clndr_id for the task's proj_id
                   ->  the CALENDAR row flagged default_flag = 'Y'
                   ->  unresolved, which is REPORTED, never papered over

A blank id that resolves is disclosed (INFO). One that cannot resolve is a
BLOCK finding, because the arithmetic downstream then runs on a week the file
does not declare.
"""
import os
import sys
import tempfile
import warnings

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from xer_parser import (  # noqa: E402
    generate_summary,
    get_calendar_map,
    get_table,
    parse_xer,
    resolve_task_calendars,
    validate_schedule,
    with_resolved_calendars,
)

TAB = '\t'


def _week_blob(hours):
    """Mon-Fri clndr_data; `hours` picks an 8 h or a 10 h working day."""
    slots = {
        8: '(0||0(s|08:00|f|12:00)())(0||1(s|13:00|f|17:00)())',
        10: '(0||0(s|07:00|f|12:00)())(0||1(s|13:00|f|18:00)())',
    }[hours]
    return (
        '(0||CalendarData()((0||DaysOfWeek()((0||1()())'
        + ''.join('(0||%d()(%s))' % (d, slots) for d in range(2, 7))
        + '(0||7()())))(0||Exceptions()())))'
    )


def _xer(*, project_clndr='C10', default_flags=('N', 'N'), task_clndrs=('', ''),
         second_project=False, ten_hour_id='C10'):
    """Two calendars (C8 = 8 h/day, C10 = 10 h/day) and two tasks of 100 h
    total float. Every argument names one thing a test varies."""
    lines = [
        TAB.join(['ERMHDR', '20.12', '2026-09-18', 'Project', 'admin', 'admin',
                  'dbxDatabaseNoName', 'Project Management', 'USD']),
        TAB.join(['%T', 'PROJECT']),
        TAB.join(['%F', 'proj_id', 'proj_short_name', 'last_recalc_date',
                  'clndr_id']),
        TAB.join(['%R', '1', 'NEUTRAL', '2026-09-21 08:00', project_clndr]),
    ]
    if second_project:
        lines.append(TAB.join(['%R', '2', 'OTHER', '2026-09-21 08:00', 'C8']))
    lines += [
        TAB.join(['%T', 'CALENDAR']),
        TAB.join(['%F', 'clndr_id', 'default_flag', 'clndr_name', 'clndr_type',
                  'day_hr_cnt', 'week_hr_cnt', 'clndr_data']),
        TAB.join(['%R', 'C8', default_flags[0], 'Eight Hour', 'CA_Base', '8',
                  '40', _week_blob(8)]),
        TAB.join(['%R', ten_hour_id, default_flags[1], 'Ten Hour', 'CA_Base', '10',
                  '50', _week_blob(10)]),
        TAB.join(['%T', 'TASK']),
        TAB.join(['%F', 'task_id', 'proj_id', 'wbs_id', 'clndr_id', 'task_code',
                  'task_name', 'task_type', 'status_code',
                  'target_drtn_hr_cnt', 'remain_drtn_hr_cnt',
                  'total_float_hr_cnt']),
        TAB.join(['%R', '11', '1', 'W1', task_clndrs[0], 'A100', 'Neutral A',
                  'TT_Task', 'TK_NotStart', '100', '100', '0']),
        TAB.join(['%R', '12', '2' if second_project else '1', 'W1',
                  task_clndrs[1], 'A200', 'Neutral B', 'TT_Task',
                  'TK_NotStart', '100', '100', '0']),
        TAB.join(['%T', 'TASKPRED']),
        TAB.join(['%F', 'task_pred_id', 'task_id', 'pred_task_id', 'pred_type',
                  'lag_hr_cnt']),
        TAB.join(['%R', '1', '12', '11', 'PR_FS', '0']),
        '%E',
    ]
    return '\r\n'.join(lines) + '\r\n'


def _parse(text):
    with tempfile.NamedTemporaryFile('w', suffix='.xer', delete=False,
                                     encoding='utf-8') as f:
        f.write(text)
        path = f.name
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return parse_xer(path)
    finally:
        os.unlink(path)


def _findings(data, check_id):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        report = validate_schedule(data)
    return [f for f in report.findings if f.check_id == check_id]


# ── the chain ────────────────────────────────────────────────────────────

def test_blank_task_calendar_resolves_to_the_project_calendar():
    res = resolve_task_calendars(_parse(_xer(project_clndr='C10')))
    assert res['by_task'] == {'11': 'C10', '12': 'C10'}
    assert res['unresolved'] == []
    assert [(r['task_code'], r['clndr_id'], r['tier'])
            for r in res['resolved_by_fallback']] == [
        ('A100', 'C10', 'project'), ('A200', 'C10', 'project')]


def test_an_explicit_task_calendar_is_never_overridden():
    res = resolve_task_calendars(_parse(_xer(project_clndr='C10',
                                             task_clndrs=('C8', ''))))
    assert res['by_task'] == {'11': 'C8', '12': 'C10'}
    assert [r['task_code'] for r in res['resolved_by_fallback']] == ['A200']


def test_each_task_falls_back_to_its_own_projects_calendar():
    res = resolve_task_calendars(_parse(_xer(project_clndr='C10',
                                             second_project=True)))
    assert res['by_task'] == {'11': 'C10', '12': 'C8'}


def test_default_flag_calendar_is_the_second_tier():
    """PROJECT.clndr_id blank, or naming a calendar the file does not carry."""
    for project_clndr in ('', 'C-NOT-IN-FILE'):
        res = resolve_task_calendars(_parse(_xer(project_clndr=project_clndr,
                                                 default_flags=('N', 'Y'))))
        assert res['by_task'] == {'11': 'C10', '12': 'C10'}, project_clndr
        assert {r['tier'] for r in res['resolved_by_fallback']} == {'default'}
        assert res['unresolved'] == []


def test_no_fallback_calendar_leaves_the_task_unresolved_and_says_so():
    res = resolve_task_calendars(_parse(_xer(project_clndr='')))
    assert res['by_task'] == {'11': '', '12': ''}
    assert res['resolved_by_fallback'] == []
    assert [(r['task_code'], r['reason']) for r in res['unresolved']] == [
        ('A100', 'blank'), ('A200', 'blank')]


def test_a_calendar_id_the_file_does_not_declare_is_not_silently_replaced():
    """Substituting the project calendar for a NAMED calendar would swap in a
    week the activity was never assigned; it is reported instead."""
    res = resolve_task_calendars(_parse(_xer(project_clndr='C10',
                                             task_clndrs=('C-GONE', 'C8'))))
    assert res['by_task'] == {'11': 'C-GONE', '12': 'C8'}
    assert [(r['task_code'], r['clndr_id'], r['reason'])
            for r in res['unresolved']] == [('A100', 'C-GONE', 'undeclared')]


def test_every_resolved_id_is_a_key_the_calendar_map_answers_to():
    """``get_calendar_map`` keys a calendar by its id exactly as the file
    writes it, and the parser keeps a padded id padded. A resolver that tidied
    the id would report the row resolved while every lookup on it missed."""
    data = _parse(_xer(project_clndr='C10 ', ten_hour_id='C10 '))
    res = resolve_task_calendars(data)
    cal_map = get_calendar_map(data)
    rows = with_resolved_calendars(get_table(data, 'TASK'), res)
    assert res['unresolved'] == []
    assert [cal_map[r['clndr_id']]['hours_per_day'] for r in rows] == [10.0, 10.0]


def test_a_tidied_id_that_the_calendar_map_would_miss_is_reported():
    """PROJECT names 'C10', the CALENDAR row is 'C10 ': not the same key, so
    not a fallback. The rows go unresolved and are reported, never half-fixed."""
    res = resolve_task_calendars(_parse(_xer(project_clndr='C10',
                                             ten_hour_id='C10 ')))
    assert res['resolved_by_fallback'] == []
    assert [u['reason'] for u in res['unresolved']] == ['blank', 'blank']


def test_rows_are_filled_by_their_own_project_not_by_a_shared_task_id():
    """Malformed rows sharing a task_id share one ``by_task`` slot. Each row is
    filled from its OWN proj_id, and a row that NAMES its calendar keeps it."""
    data = _parse(_xer(project_clndr='C10', second_project=True,
                       task_clndrs=('', '')))
    data['tables']['PROJECT']['records'][1]['clndr_id'] = ''   # project 2: none
    for row in data['tables']['TASK']['records']:
        row['task_id'] = 'DUP'
    res = resolve_task_calendars(data)
    rows = with_resolved_calendars(get_table(data, 'TASK'), res)
    assert [(r['task_code'], r['clndr_id']) for r in rows] == [
        ('A100', 'C10'), ('A200', '')]
    assert [r['task_code'] for r in res['resolved_by_fallback']] == ['A100']
    assert [u['task_code'] for u in res['unresolved']] == ['A200']

    data['tables']['TASK']['records'][0]['clndr_id'] = 'C8'     # now explicit
    rows = with_resolved_calendars(get_table(data, 'TASK'),
                                   resolve_task_calendars(data))
    assert [r['clndr_id'] for r in rows] == ['C8', '']


def test_with_resolved_calendars_copies_rows_and_leaves_the_parse_untouched():
    data = _parse(_xer(project_clndr='C10'))
    raw = data['tables']['TASK']['records']
    rows = with_resolved_calendars(raw, resolve_task_calendars(data))
    assert [r['clndr_id'] for r in rows] == ['C10', 'C10']
    assert [r['clndr_id'] for r in raw] == ['', '']   # the file as received
    assert rows[0]['task_code'] == 'A100'


# ── validate_schedule ────────────────────────────────────────────────────

def test_unresolvable_blank_calendar_is_a_block_finding():
    found = _findings(_parse(_xer(project_clndr='')),
                      'XER-TASK-CALENDAR-UNRESOLVED')
    assert len(found) == 1
    assert found[0].severity == 'BLOCK'
    assert found[0].evidence['unresolved_count'] == 2
    assert found[0].evidence['task_codes'] == ['A100', 'A200']
    # names what each consumer falls back to, not one week for all of them
    assert '8 h/day' in found[0].message and 'seven-day' in found[0].message


def test_resolved_fallback_is_disclosed_without_costing_the_score():
    data = _parse(_xer(project_clndr='C10'))
    assert _findings(data, 'XER-TASK-CALENDAR-UNRESOLVED') == []
    found = _findings(data, 'XER-TASK-CALENDAR-FALLBACK')
    assert len(found) == 1
    assert found[0].severity == 'INFO'
    assert found[0].evidence['resolved_count'] == 2
    assert found[0].evidence['calendars'] == [
        {'clndr_id': 'C10', 'clndr_name': 'Ten Hour', 'tier': 'project',
         'task_count': 2}]


def test_explicit_calendars_raise_neither_finding():
    data = _parse(_xer(task_clndrs=('C8', 'C10')))
    assert _findings(data, 'XER-TASK-CALENDAR-UNRESOLVED') == []
    assert _findings(data, 'XER-TASK-CALENDAR-FALLBACK') == []


# ── the duration helpers' caller ─────────────────────────────────────────

def test_summary_converts_float_on_the_resolved_calendar():
    """100 h of float on the 10 h/day project calendar is 10 days; the blank id
    used to fall through to the hard-coded 8 h/day and report 12.5."""
    text = _xer(project_clndr='C10').replace(
        TAB.join(['100', '100', '0']), TAB.join(['100', '100', '-100']))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        summary = generate_summary(_parse(text))
    crit = summary['critical_path']['critical_activities']
    assert [c['total_float_days'] for c in crit] == [-10, -10]
