"""Regression (2026-09-29): calendar time slots decode in either field order.

P6 writes a working time slot as either

    (s|08:00|f|16:00)     start-first
    (f|16:00|s|08:00)     finish-first

and the order belongs to the individual calendar: one genuine P6 24.12 export
carries a start-first five-day calendar beside a finish-first six-day calendar.
The decoder required start-first at all three places it looks for a slot: the
DaysOfWeek work-week classifier, the balanced-paren exception classifier and
the fallback exception classifier. So every finish-first calendar decoded to
``work_days == []``, which the working-day helpers then counted as Mon-Fri,
and every finish-first exception body was filed as a HOLIDAY, an invented day
off, instead of a forced working day.

The same file pins three neighbouring fixes to the exception decoder:

- The fallback classifier looked for a time slot ADJACENT to the serial. P6
  puts ``\\x7f\\x7f`` line markers and whitespace between them, so on a
  continuous calendar every worked exception became a holiday. It now scans
  each serial's own segment, up to the next serial.
- Exception dates outside 1990-2050 were dropped. The window is 1970-2099.
- When two parse paths disagree on a date, a day carrying work hours is a
  working day, never a holiday.

Every calendar string below is built in this file. The encoding follows the
P6 grammar in references/table-reference.md; no real export is copied.
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'scripts'))

from xer_parser import (  # noqa: E402
    get_calendar_map,
    get_work_days_between,
    parse_calendar_data,
)

SEP = '\x7f\x7f'  # the P6 line marker

# Serials on the 1899-12-30 epoch, checked against their dates in
# test_the_serials_used_here_are_the_dates_named.
S_2026_12_25 = 46381   # Friday, empty body -> holiday
S_2027_01_01 = 46388   # Friday, empty body -> holiday
S_2026_12_26 = 46382   # Saturday, carries work hours -> special workday
S_2026_12_27 = 46383   # Sunday, carries work hours -> special workday


def _finish_first_six_day():
    """Days 2..7 (Mon..Sat) worked, each as two finish-first slots."""
    return (
        '(0||CalendarData()((0||DaysOfWeek()((0||1()())'
        + ''.join(
            '(0||%d()((0||0(f|11:30|s|07:00)())(0||1(f|16:30|s|12:00)())))' % d
            for d in range(2, 8))
        + '))(0||Exceptions())(0||VIEW(ShowTotal|Y)())))')


def _start_first_five_day():
    """Days 2..6 (Mon..Fri) worked, start-first; days 1 and 7 empty."""
    return (
        '(0||CalendarData()((0||DaysOfWeek()((0||1()())'
        + ''.join(
            '(0||%d()((0||0(s|07:00|f|11:30)())(0||1(s|12:00|f|16:30)())))' % d
            for d in range(2, 7))
        + '(0||7()()))))(0||Exceptions())(0||VIEW(ShowTotal|Y)())))')


def _finish_first_seven_day():
    """Every day worked, finish-first, with two empty-body exceptions
    (holidays) and two finish-first work-hour exceptions (forced working)."""
    return (
        '(0||CalendarData()((0||DaysOfWeek()('
        + ''.join(
            '(0||%d()((0||0(f|12:00|s|06:00)())(0||1(f|18:00|s|12:00)())))' % d
            for d in range(1, 8))
        + '))(0||Exceptions()('
        + '(0||0(d|%d)())' % S_2026_12_25
        + '(0||1(d|%d)())' % S_2027_01_01
        + '(0||2(d|%d)((0||0(f|12:00|s|7:00)())(0||1(f|15:00|s|12:30)())))'
        % S_2026_12_26
        + '(0||3(d|%d)((0||0(f|12:00|s|7:00)())(0||1(f|15:00|s|12:30)())))'
        % S_2026_12_27
        + '))))')


def test_the_serials_used_here_are_the_dates_named():
    from datetime import date, timedelta
    epoch = date(1899, 12, 30)
    assert epoch + timedelta(days=S_2026_12_25) == date(2026, 12, 25)
    assert epoch + timedelta(days=S_2027_01_01) == date(2027, 1, 1)
    assert epoch + timedelta(days=S_2026_12_26) == date(2026, 12, 26)
    assert epoch + timedelta(days=S_2026_12_27) == date(2026, 12, 27)


# ── Slot order ───────────────────────────────────────────────────────────

def test_finish_first_week_decodes_to_six_days():
    """The defect: this decoded to [] and was counted as Mon-Fri."""
    info = parse_calendar_data(_finish_first_six_day())
    assert info['work_days'] == [1, 2, 3, 4, 5, 6], info['work_days']
    assert info['work_day_names'][-1] == 'Saturday'


def test_start_first_week_still_decodes():
    """Guard against a pattern loosened into one that accepts anything."""
    info = parse_calendar_data(_start_first_five_day())
    assert info['work_days'] == [1, 2, 3, 4, 5], info['work_days']


def test_both_orders_decode_from_one_file():
    """Both orders occur in one genuine export, so the decoder cannot pick an
    order per file. Decoded together through get_calendar_map."""
    data = {'tables': {'CALENDAR': {
        'fields': ['clndr_id', 'clndr_name', 'day_hr_cnt', 'clndr_data'],
        'records': [
            {'clndr_id': 'C5', 'clndr_name': 'Five day', 'day_hr_cnt': '9',
             'clndr_data': _start_first_five_day()},
            {'clndr_id': 'C6', 'clndr_name': 'Six day', 'day_hr_cnt': '9',
             'clndr_data': _finish_first_six_day()},
        ]}}}
    cal_map = get_calendar_map(data)
    assert cal_map['C5']['work_days'] == [1, 2, 3, 4, 5]
    assert cal_map['C6']['work_days'] == [1, 2, 3, 4, 5, 6]


def test_finish_first_exception_bodies_are_working_days_not_holidays():
    info = parse_calendar_data(_finish_first_seven_day())
    assert info['work_days'] == [0, 1, 2, 3, 4, 5, 6], info['work_days']
    assert info['special_workdays'] == ['2026-12-26', '2026-12-27'], \
        info['special_workdays']
    # Empty-body exceptions stay holidays.
    assert info['holidays'] == ['2026-12-25', '2027-01-01'], info['holidays']


def test_a_legacy_iso_dated_exception_with_a_finish_first_body_is_worked():
    """ISO-dated exceptions are read only by the balanced-paren classifier,
    so this pins that classifier's slot order on its own."""
    info = parse_calendar_data(_five_day_with_exceptions([
        '(0||0(d|2026-12-26)((0||0(f|12:00|s|08:00)())))']))
    assert info['special_workdays'] == ['2026-12-26'], info['special_workdays']
    assert info['holidays'] == [], info['holidays']


def test_finish_first_with_line_markers_and_a_one_digit_hour():
    days = SEP.join(
        '    (0||%d()(%s      (0||0(f|15:00|s|7:00)())))' % (d, SEP)
        for d in range(2, 8))
    exc = ('    (0||0(d|%d)(%s      (0||0(f|15:00|s|9:00)())))'
           '%s    (0||1(d|%d)())' % (S_2026_12_27, SEP, SEP, S_2026_12_25))
    cd = ('(0||CalendarData()(%s  (0||DaysOfWeek()(%s%s))%s  '
          '(0||Exceptions()(%s%s)))' % (SEP, SEP, days, SEP, SEP, exc))
    info = parse_calendar_data(cd)
    assert info['work_days'] == [1, 2, 3, 4, 5, 6], info['work_days']
    assert info['special_workdays'] == ['2026-12-27']
    assert info['holidays'] == ['2026-12-25']


def test_a_finish_first_seven_day_week_counts_every_day():
    """What the defect did downstream: Monday to the next Monday on a
    seven-day calendar is eight working days inclusive. Decoded as [] it was
    counted on Mon-Fri, six."""
    cal = parse_calendar_data(_finish_first_seven_day())
    assert get_work_days_between('2026-11-02', '2026-11-09', cal) == 8


# ── Exception segments are read up to the next serial ───────────────────

def _continuous_with_marker_separated_exceptions():
    """A seven-day calendar in the marker-separated layout, whose exception
    entries use non-zero positional indices, which only the fallback
    classifier reads. Two carry work hours; one has an empty body."""
    days = SEP.join(
        '    (0||%d()(%s      (0||0(s|06:00|f|12:00)())%s'
        '      (0||1(s|12:30|f|18:30)())))' % (d, SEP, SEP)
        for d in range(1, 8))
    exc = (
        '    (0||4(d|%d)(%s      (0||0(s|07:00|f|12:00)())%s'
        '      (0||1(s|12:30|f|15:00)())))' % (S_2026_12_26, SEP, SEP)
        + '%s    (0||5(d|%d)(%s      (0||0(s|07:00|f|15:00)())))'
        % (SEP, S_2026_12_27, SEP)
        + '%s    (0||6(d|%d)())' % (SEP, S_2027_01_01))
    return ('(0||CalendarData()(%s  (0||DaysOfWeek()(%s%s))%s  '
            '(0||Exceptions()(%s%s)))' % (SEP, SEP, days, SEP, SEP, exc))


def test_worked_exceptions_separated_by_line_markers_are_not_holidays():
    info = parse_calendar_data(_continuous_with_marker_separated_exceptions())
    assert info['work_days'] == [0, 1, 2, 3, 4, 5, 6]
    assert info['special_workdays'] == ['2026-12-26', '2026-12-27'], \
        info['special_workdays']
    assert info['holidays'] == ['2027-01-01'], info['holidays']


def test_empty_body_exceptions_on_a_work_calendar_stay_holidays():
    days = SEP.join(
        '    (0||%d()(%s      (0||0(s|08:00|f|16:00)())))' % (d, SEP)
        for d in range(2, 7))
    exc = '    (0||2(d|%d)())%s    (0||3(d|%d)())' % (
        S_2026_12_25, SEP, S_2027_01_01)
    cd = ('(0||CalendarData()(%s  (0||DaysOfWeek()(%s%s))%s  '
          '(0||Exceptions()(%s%s)))' % (SEP, SEP, days, SEP, SEP, exc))
    info = parse_calendar_data(cd)
    assert info['holidays'] == ['2026-12-25', '2027-01-01']
    assert info['special_workdays'] == []


# ── Exception date window ────────────────────────────────────────────────

def _five_day_with_exceptions(entries):
    return ('(0||CalendarData()((0||DaysOfWeek()('
            + ''.join('(0||%d()((0||0(s|08:00|f|16:00)())))' % d
                      for d in range(2, 7))
            + '))(0||Exceptions()(' + ''.join(entries) + '))))')


def test_exception_dates_from_1970_to_2099_are_kept():
    # 31229 is 1985-07-01; 58441 is 2060-01-01. Both were dropped by the
    # old 1990-2050 window.
    info = parse_calendar_data(_five_day_with_exceptions([
        '(0||0(d|31229)())', '(0||1(d|58441)())']))
    assert info['holidays'] == ['1985-07-01', '2060-01-01'], info['holidays']


def test_iso_string_exception_dates_use_the_same_window():
    info = parse_calendar_data(_five_day_with_exceptions([
        # index 0 with work hours: read by the balanced-paren classifier.
        # 1985-07-06 is a Saturday.
        '(0||0(d|1985-07-06)((0||0(s|08:00|f|12:00)())))',
        # index 1, empty body: read only by the fallback classifier.
        '(0||1(d|2060-01-01)())']))
    assert info['special_workdays'] == ['1985-07-06'], info['special_workdays']
    assert info['holidays'] == ['2060-01-01'], info['holidays']


def test_dates_outside_the_window_are_still_dropped():
    # 25203 is 1968-12-31; 73051 is 2100-01-01.
    info = parse_calendar_data(_five_day_with_exceptions([
        '(0||0(d|25203)())', '(0||1(d|73051)())']))
    assert info['holidays'] == []


# ── A day with work hours is never also a holiday ────────────────────────

def test_a_date_listed_both_off_and_worked_is_a_working_day():
    """The same date appears twice: once with an empty body, once with work
    hours. It used to land in BOTH lists."""
    info = parse_calendar_data(_five_day_with_exceptions([
        '(0||0(d|%d)())' % S_2026_12_26,
        '(0||0(d|%d)((0||0(s|08:00|f|12:00)())))' % S_2026_12_26]))
    assert info['special_workdays'] == ['2026-12-26']
    assert info['holidays'] == [], info['holidays']


if __name__ == '__main__':
    import inspect
    tests = [f for n, f in sorted(globals().items())
             if n.startswith('test_') and inspect.isfunction(f)]
    for t in tests:
        t()
    print('%d / %d passed' % (len(tests), len(tests)))
