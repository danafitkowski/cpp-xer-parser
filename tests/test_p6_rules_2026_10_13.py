"""The data date and calendar rules P6 schedules by (2026-10-12 and 2026-10-13).

Each rule was measured on Primavera P6 Professional 23.12.1's own F9 and is
the one cpp-cpm-engine v2.10.1's parseXER applies.

- A blank PROJECT.last_recalc_date is the project's planned start: P6
  schedules "from the project data date, using the project start date as the
  initial data date". parse_xer fills it in place and lists the fill in
  data['data_date_filled'].
- A filed data date on an EARLIER DAY than the planned start is lifted to it,
  as P6 lifts it when it opens the project (data date 28-Aug, planned start
  01-Sep: P6 shows and schedules from 01-Sep). The entry keeps the filed date
  as filed_data_date. A planned start later the same day is left as filed.
- An EMPTY calendar record (no clndr_data) is P6's internal Standard,
  Monday to Friday 08:00-16:00, eight hours, no holidays, whatever hours a
  day it declares; the declared figure is kept in declared_hours_per_day.
  It has no shifts, so calendar_shift_hours does not list it.
- resource_dependent_assignments reads each TASKRSRC row as P6 schedules it
  on a resource dependent activity: the resource's calendar, remaining units
  over remaining units per hour, the remaining lag (the planned lag when
  that is blank), and Drive Activity Dates.

The tests marked [discriminating] fail on v0.3.0. Every file below is built
in this file; no real export is copied.
"""
import os
import sys
import tempfile
import warnings
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'scripts'))

from xer_parser import (parse_xer, get_table, get_calendar_map,  # noqa: E402
                        calendar_shift_hours, duration_hours_to_days,
                        get_work_days_between, resource_dependent_assignments)

TAB = '\t'


def _parse(tables):
    lines = ['ERMHDR\t23.12\t2026-10-13\tProject\tuser\tUser\tdb\tProject Management\tUSD']
    for name, fields, rows in tables:
        lines.append('%T' + TAB + name)
        lines.append('%F' + TAB + TAB.join(fields))
        for r in rows:
            lines.append('%R' + TAB + TAB.join(r))
    lines.append('%E')
    fd, path = tempfile.mkstemp(suffix='.xer')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return parse_xer(path)
    finally:
        os.unlink(path)


_PROJ = ['proj_id', 'proj_short_name', 'last_recalc_date', 'plan_start_date']


# ── the data date ─────────────────────────────────────────────────────

def test_a_blank_data_date_reads_as_the_planned_start():
    # [discriminating]
    data = _parse([('PROJECT', _PROJ, [['1', 'BL', '', '2024-12-02 08:00']])])
    assert get_table(data, 'PROJECT')[0]['last_recalc_date'] == '2024-12-02 08:00'
    assert data['data_date_filled'] == [
        {'proj_id': '1', 'last_recalc_date': '2024-12-02 08:00', 'filled_from': 'plan_start_date'}]


def test_a_blank_with_no_planned_start_stays_blank():
    data = _parse([('PROJECT', _PROJ, [['1', 'X', '', '']])])
    assert get_table(data, 'PROJECT')[0]['last_recalc_date'] == ''
    assert data['data_date_filled'] == []


def test_a_data_date_before_a_later_planned_start_is_lifted_to_it():
    # [discriminating]
    data = _parse([('PROJECT', _PROJ, [['1', 'XZ', '2026-08-28 08:00', '2026-09-01 08:00']])])
    assert get_table(data, 'PROJECT')[0]['last_recalc_date'] == '2026-09-01 08:00'
    assert data['data_date_filled'] == [{
        'proj_id': '1', 'last_recalc_date': '2026-09-01 08:00',
        'filled_from': 'plan_start_date', 'filed_data_date': '2026-08-28 08:00'}]


def test_a_planned_start_later_the_same_day_leaves_the_data_date_as_filed():
    data = _parse([('PROJECT', _PROJ, [['1', 'SD', '2026-09-01 00:00', '2026-09-01 08:00']])])
    assert get_table(data, 'PROJECT')[0]['last_recalc_date'] == '2026-09-01 00:00'
    assert data['data_date_filled'] == []


def test_a_data_date_after_the_planned_start_is_left_as_filed():
    data = _parse([('PROJECT', _PROJ, [['1', 'UP', '2026-10-05 08:00', '2026-09-01 08:00']])])
    assert get_table(data, 'PROJECT')[0]['last_recalc_date'] == '2026-10-05 08:00'
    assert data['data_date_filled'] == []


def test_each_project_is_read_on_its_own():
    # [discriminating]
    data = _parse([('PROJECT', _PROJ, [['1', 'A', '', '2025-10-06 08:00'],
                                       ['2', 'B', '2026-01-05 08:00', '2025-01-01 08:00']])])
    recs = get_table(data, 'PROJECT')
    assert [r['last_recalc_date'] for r in recs] == ['2025-10-06 08:00', '2026-01-05 08:00']
    assert [f['proj_id'] for f in data['data_date_filled']] == ['1']


def test_a_file_with_no_project_table_has_nothing_filled():
    data = _parse([('TASK', ['task_id'], [['1']])])
    assert data['data_date_filled'] == []


# ── an empty calendar record ──────────────────────────────────────────

_CAL = ['clndr_id', 'clndr_name', 'day_hr_cnt', 'week_hr_cnt', 'clndr_data']
_TEN_HOUR_WEEK = ('(0||CalendarData()((0||DaysOfWeek()((0||1()())'
                  + ''.join('(0||%d()((0||0(s|07:00|f|17:00)())))' % d for d in range(2, 7))
                  + '(0||7()())))(0||Exceptions()())))')


def _cal_map(rows):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return get_calendar_map(_parse([('CALENDAR', _CAL, rows)]))


def test_an_empty_record_is_p6s_internal_standard_whatever_it_declares():
    # [discriminating] on v0.3.0 an empty record had no working days at all
    # and converted hours at the declared figure.
    cm = _cal_map([['E10', 'Empty ten', '10', '50', ''],
                   ['E24', 'Empty twenty-four', '24', '168', ''],
                   ['E8', 'Empty eight', '8', '40', '']])
    for cid, declared in (('E10', 10.0), ('E24', 24.0), ('E8', 8.0)):
        cal = cm[cid]
        assert cal['work_days'] == [1, 2, 3, 4, 5]
        assert cal['work_day_names'] == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        assert cal['holidays'] == [] and cal['special_workdays'] == []
        assert cal['hours_per_day'] == 8.0
        assert cal['empty_record'] is True
        assert cal['declared_hours_per_day'] == declared


def test_hours_on_an_empty_record_convert_at_eight():
    # [discriminating] 40 h on an empty record declaring 10 h a day is five
    # P6 days, not four.
    cal = _cal_map([['E10', 'Empty ten', '10', '50', '']])['E10']
    assert duration_hours_to_days(40, cal) == 5.0


def test_an_empty_record_works_monday_to_friday():
    # Friday 4 Sep to Monday 14 Sep 2026 on P6's Standard, which has no
    # holidays (Labour Day, Monday 7 Sep, is a working day): the same count
    # as a plain Monday to Friday week. (v0.3.0 reached the same count by
    # falling back to Monday to Friday for a week with no working days.)
    cal = _cal_map([['E10', 'Empty ten', '10', '50', '']])['E10']
    assert get_work_days_between(datetime(2026, 9, 4), datetime(2026, 9, 14), cal) == \
        get_work_days_between(datetime(2026, 9, 4), datetime(2026, 9, 14),
                              {'work_days': [1, 2, 3, 4, 5], 'holidays': []})


def test_an_empty_record_is_not_a_calendar_whose_hours_came_from_its_shifts():
    cm = _cal_map([['E10', 'Empty ten', '10', '50', ''],
                   ['S10', 'Ten hour shifts declared eight', '8', '40', _TEN_HOUR_WEEK]])
    assert cm['S10']['hours_per_day'] == 10.0
    assert [c['clndr_id'] for c in calendar_shift_hours(cm)] == ['S10']


def test_a_calendar_with_its_week_is_read_as_before():
    cm = _cal_map([['S10', 'Ten hour shifts declared ten', '10', '50', _TEN_HOUR_WEEK]])
    assert cm['S10']['hours_per_day'] == 10.0
    assert 'empty_record' not in cm['S10']
    assert 'declared_hours_per_day' not in cm['S10']


# ── resource dependent assignments ────────────────────────────────────

_RSRC = ('RSRC', ['rsrc_id', 'rsrc_name', 'clndr_id'], [['R1', 'Crane', 'RC'], ['R2', 'Crew', '']])
_TASKRSRC = ['taskrsrc_id', 'task_id', 'rsrc_id', 'remain_qty', 'remain_qty_per_hr',
             'relag_drtn_hr_cnt', 'target_lag_drtn_hr_cnt', 'rollup_dates_flag']


def test_resource_dependent_assignments_read_each_row_as_p6_schedules_it():
    # [discriminating] the function is new in v0.4.0.
    data = _parse([_RSRC, ('TASKRSRC', _TASKRSRC, [
        ['1', 'T1', 'R1', '40', '2', '4', '8', 'Y'],
        ['2', 'T1', 'R2', '16', '1', '', '8', 'N'],
        ['3', 'T2', '', '10', '0', '', '', ''],
    ])])
    assert resource_dependent_assignments(data) == {
        'T1': [
            {'rsrc_id': 'R1', 'clndr_id': 'RC', 'remaining_hours': 20.0, 'lag_hours': 4.0, 'driving': True},
            {'rsrc_id': 'R2', 'clndr_id': None, 'remaining_hours': 16.0, 'lag_hours': 8.0, 'driving': False},
        ],
        'T2': [
            {'rsrc_id': '', 'clndr_id': None, 'remaining_hours': 0.0, 'lag_hours': 0.0, 'driving': True},
        ],
    }


def test_a_file_with_no_assignments_has_none():
    assert resource_dependent_assignments(_parse([_RSRC])) == {}


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
