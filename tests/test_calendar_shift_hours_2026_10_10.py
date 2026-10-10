"""Hours per day are the hours a calendar's shifts work (2026-10-10), when every
working day of its week works the same hours and they are not what
CALENDAR.day_hr_cnt says.

P6 schedules a duration in hours against the calendar's shifts; day_hr_cnt
("Hours per Day") only converts hours to days for display. Scheduled with F9 in
Primavera P6 Professional 23.12.1 on 10-Oct-2026, a Monday-Saturday
07:00-17:00 calendar, ten hours a day, declaring day_hr_cnt 8, ran a 40 h
activity over four days. Dividing by day_hr_cnt gives five.

The rule. When every working weekday of the DaysOfWeek block works the same
number of hours H and H is not day_hr_cnt, hours_per_day is H, the file's
figure is kept as declared_hours_per_day, calendar_shift_hours lists the
calendar and a CalendarShiftHoursWarning names it. A week whose working days
work different hours keeps day_hr_cnt: no one figure is right for it.

The tests marked [discriminating] fail on v0.2.1. Every calendar string below
is built in this file; no real export is copied.
"""
import os
import sys
import warnings

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'scripts'))

import xer_parser  # noqa: E402
from xer_parser import duration_hours_to_days, get_calendar_map  # noqa: E402

TEN = '(0||0(s|07:00|f|17:00)())'
TEN_FINISH_FIRST = '(0||0(f|17:00|s|07:00)())'
EIGHT = '(0||0(s|08:00|f|12:00)())(0||1(s|13:00|f|17:00)())'
FOUR = '(0||0(s|08:00|f|12:00)())'


def _blob(days):
    """days: {P6 weekday 1=Sun..7=Sat: slot string}."""
    return ('(0||CalendarData()((0||DaysOfWeek()('
            + ''.join('(0||%d()(%s))' % (d, days.get(d, '')) for d in range(1, 8))
            + '))(0||Exceptions()())))')


def _data(rows):
    return {'tables': {'CALENDAR': {'fields': [], 'records': [
        {'clndr_id': cid, 'clndr_name': name, 'clndr_type': 'CA_Project', 'day_hr_cnt': day_hr,
         'week_hr_cnt': '40', 'clndr_data': blob} for cid, name, day_hr, blob in rows]}}}


def _map(rows):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        cm = get_calendar_map(_data(rows))
    return cm, [w for w in caught
                if issubclass(w.category, getattr(xer_parser, 'CalendarShiftHoursWarning', ()))]


def test_a_ten_hour_week_declared_at_eight_converts_on_ten():
    """[discriminating] Monday-Saturday 07:00-17:00, day_hr_cnt 8."""
    cm, caught = _map([('1', 'Six by ten', '8', _blob({d: TEN for d in range(2, 8)}))])
    cal = cm['1']
    assert cal['hours_per_day'] == 10.0
    assert cal['declared_hours_per_day'] == 8.0
    assert xer_parser.calendar_shift_hours(cm) == [
        {'clndr_id': '1', 'clndr_name': 'Six by ten', 'hours_per_day': 10.0,
         'declared_hours_per_day': 8.0}]
    assert len(caught) == 1
    assert "'Six by ten'" in str(caught[0].message)


def test_forty_hours_on_that_calendar_are_four_days():
    """[discriminating] The conversion every caller makes reads the shifts' ten."""
    cm, _ = _map([('1', 'Six by ten', '8', _blob({d: TEN for d in range(2, 8)}))])
    assert duration_hours_to_days('40', cm['1']) == 4.0


def test_finish_first_slots_count_the_same():
    """[discriminating] P6 writes some calendars' slots finish first."""
    cm, _ = _map([('2', 'Seven by ten', '8', _blob({d: TEN_FINISH_FIRST for d in range(1, 8)}))])
    assert cm['2']['hours_per_day'] == 10.0
    assert cm['2']['declared_hours_per_day'] == 8.0


def test_a_calendar_whose_shifts_match_day_hr_cnt_is_unchanged():
    cm, caught = _map([('3', 'Standard', '8', _blob({d: EIGHT for d in range(2, 7)}))])
    assert cm['3']['hours_per_day'] == 8.0
    assert 'declared_hours_per_day' not in cm['3']
    assert xer_parser.calendar_shift_hours(cm) == []
    assert caught == []


def test_a_week_of_unequal_days_keeps_day_hr_cnt():
    """Monday-Friday eight hours and a Saturday morning: day_hr_cnt stands."""
    days = {d: EIGHT for d in range(2, 7)}
    days[7] = FOUR
    cm, caught = _map([('4', 'Six day short Saturday', '8', _blob(days))])
    assert cm['4']['hours_per_day'] == 8.0
    assert 'declared_hours_per_day' not in cm['4']
    assert caught == []


def test_a_finish_at_midnight_is_the_end_of_the_day():
    """01:00-12:00 and 13:00-00:00 work 22 hours, as day_hr_cnt 22 says."""
    day = '(0||0(s|01:00|f|12:00)())(0||1(s|13:00|f|00:00)())'
    cm, caught = _map([('5', 'Seven by twenty-two', '22', _blob({d: day for d in range(1, 8)}))])
    assert cm['5']['hours_per_day'] == 22.0
    assert 'declared_hours_per_day' not in cm['5']
    assert caught == []


def test_a_calendar_with_no_week_keeps_day_hr_cnt():
    """No DaysOfWeek block, or an older bare-day encoding with no hours."""
    cm, caught = _map([('6', 'Blank', '8', ''), ('7', 'Bare days', '10', '(d|2)(d|3)(d|4)(d|5)(d|6)')])
    assert cm['6']['hours_per_day'] == 8.0
    assert cm['7']['hours_per_day'] == 10.0
    assert xer_parser.calendar_shift_hours(cm) == []
    assert caught == []


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
