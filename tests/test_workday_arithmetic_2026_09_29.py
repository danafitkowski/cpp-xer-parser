"""Regression (2026-09-29): working-day arithmetic.

Five defects in get_work_days_between, add_work_days and subtract_work_days:

1. SPECIAL WORKDAYS IGNORED. parse_calendar_data files a worked Saturday
   under ``special_workdays``, and every working-day helper dropped it, so the
   day fell out of every count and every step.
2. CLOCK TIMES. get_work_days_between stripped the time from string inputs
   only. A datetime whose clock time was earlier than the start's was never
   reached by the day walk: Friday 17:00 to Monday 08:00 counted Friday alone,
   and a date could not be compared with a datetime at all (TypeError).
3. NO SPAN GUARD. A sentinel finish such as 9999-12-31 walked millions of
   days and returned a plausible-looking count.
4. HALF-DAY ROUNDING. int(round(x)) is round-half-to-even: 0.5 -> 0 and
   2.5 -> 2, where cpp-cpm-engine rounds half-up to 1 and 3.
5. ZERO-DAY IDENTITY. add_work_days(d, 0) returned d unchanged; the engine
   snaps a non-working anchor forward (and subtract_work_days(d, 0) snaps it
   backward).

The docstrings of add_work_days and subtract_work_days also stated the
opposite of what the functions do. They walk N gaps, so a task of D working
days starting on ES finishes on add_work_days(ES, D - 1). The docstring is
pinned below together with the recipe it publishes.

2026-08-17 is a Monday, 2026-08-22 a Saturday and 2026-06-06 a Saturday;
test_the_anchor_dates_are_the_weekdays_named checks each.
"""
import os
import sys
from datetime import date, datetime, timedelta

import pytest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'scripts'))

from xer_parser import (  # noqa: E402
    _is_work_day,
    _round_half_up,
    add_work_days,
    get_work_days_between,
    subtract_work_days,
)

MON_FRI = {'work_days': [1, 2, 3, 4, 5], 'holidays': [], 'special_workdays': []}

# Mon-Fri with Saturday 2026-06-06 forced ON.
SAT_WORKED = {'work_days': [1, 2, 3, 4, 5], 'holidays': [],
              'special_workdays': ['2026-06-06']}


def _cal(work_days, holidays=()):
    return {'work_days': list(work_days), 'holidays': list(holidays),
            'special_workdays': []}


def test_the_anchor_dates_are_the_weekdays_named():
    assert date(2026, 8, 17).strftime('%a') == 'Mon'
    assert date(2026, 8, 22).strftime('%a') == 'Sat'
    assert date(2026, 6, 6).strftime('%a') == 'Sat'
    assert date(2026, 1, 9).strftime('%a') == 'Fri'


# ── 1. Special workdays ──────────────────────────────────────────────────

def test_is_work_day_honours_a_forced_on_saturday():
    assert _is_work_day(date(2026, 6, 6), [1, 2, 3, 4, 5], set(),
                        {'2026-06-06'}) is True


def test_a_holiday_beats_a_special_workday_on_the_same_date():
    assert _is_work_day(date(2026, 6, 6), [1, 2, 3, 4, 5], {'2026-06-06'},
                        {'2026-06-06'}) is False


def test_get_work_days_between_counts_a_special_workday():
    # Fri + Sat (worked) + Mon = 3 inclusive; without the Saturday, 2.
    assert get_work_days_between(date(2026, 6, 5), date(2026, 6, 8),
                                 SAT_WORKED) == 3


def test_add_work_days_lands_on_a_special_workday():
    assert add_work_days(date(2026, 6, 5), 1, SAT_WORKED) == date(2026, 6, 6)


def test_subtract_work_days_lands_on_a_special_workday():
    assert subtract_work_days(date(2026, 6, 8), 1, SAT_WORKED) == date(2026, 6, 6)


def test_a_special_workday_on_a_normal_weekday_is_not_counted_twice():
    cal = {'work_days': [1, 2, 3, 4, 5], 'holidays': [],
           'special_workdays': ['2026-06-08']}          # a Monday
    assert get_work_days_between(date(2026, 6, 8), date(2026, 6, 8), cal) == 1


# ── 2. Dates are read on their calendar day ──────────────────────────────

FRI_17 = datetime(2026, 1, 9, 17, 0)
MON_08 = datetime(2026, 1, 12, 8, 0)
MON_17 = datetime(2026, 1, 12, 17, 0)


def test_friday_evening_to_monday_morning_counts_both_days():
    assert get_work_days_between(FRI_17, MON_08) == 2
    assert get_work_days_between('2026-01-09 17:00', MON_08) == 2
    assert get_work_days_between(FRI_17, '2026-01-12 08:00') == 2


def test_the_same_day_at_two_times_is_one_working_day():
    assert get_work_days_between(MON_17, MON_08) == 1
    assert get_work_days_between(MON_08, MON_17) == 1


def test_a_date_and_a_datetime_can_be_compared():
    assert get_work_days_between(date(2026, 1, 9), MON_08) == 2
    assert get_work_days_between(date(2026, 1, 12), MON_17) == 1


def test_unreadable_dates_still_return_none():
    assert get_work_days_between('not-a-date', '2026-01-12') is None
    assert get_work_days_between('2026-01-09', None) is None
    assert get_work_days_between(object(), '2026-01-12') is None


# ── 3. Span guard ────────────────────────────────────────────────────────

def test_a_sentinel_finish_date_returns_none():
    assert get_work_days_between('2026-01-09', '9999-12-31') is None


def test_a_hundred_year_span_is_still_counted():
    start, end = date(2000, 1, 3), date(2099, 12, 31)
    got = get_work_days_between(start, end, _cal(range(7)))
    assert got == (end - start).days + 1


# ── Gap semantics, as the docstrings now state ───────────────────────────

def test_add_work_days_walks_gaps_not_occupied_days():
    assert add_work_days('2026-08-17', 5, MON_FRI) == date(2026, 8, 24)
    assert add_work_days('2026-08-17', 4, MON_FRI) == date(2026, 8, 21)


def test_add_work_days_docstring_publishes_the_true_recipe():
    """The defect was the docstring, so the docstring is what this pins,
    together with the recipe it publishes."""
    assert 'EF = add_work_days(ES, D - 1)' in add_work_days.__doc__
    es, duration = date(2026, 8, 17), 5
    assert add_work_days(es, duration - 1, MON_FRI) == date(2026, 8, 21)


def test_subtract_work_days_docstring_publishes_the_true_recipe():
    assert 'subtract_work_days(LF, D - 1)' in subtract_work_days.__doc__
    lf, duration = date(2026, 8, 21), 5
    assert subtract_work_days(lf, duration - 1, MON_FRI) == date(2026, 8, 17)


# ── 4. Half-up rounding ──────────────────────────────────────────────────

@pytest.mark.parametrize('value,expected', [
    (0.5, 1),      # banker's rounding gave 0
    (1.5, 2),
    (2.5, 3),      # banker's rounding gave 2
    (3.5, 4),
    (0.4, 0),
    (0.6, 1),
    (2.0, 2),
    (None, 0),
])
def test_round_half_up(value, expected):
    assert _round_half_up(value) == expected


def test_half_day_durations_resolve_half_up():
    assert add_work_days('2026-08-17', 0.5, MON_FRI) == date(2026, 8, 18)
    assert add_work_days('2026-08-17', 2.5, MON_FRI) == date(2026, 8, 20)
    assert subtract_work_days('2026-08-21', 0.5, MON_FRI) == date(2026, 8, 20)
    assert subtract_work_days('2026-08-21', 2.5, MON_FRI) == date(2026, 8, 18)


# ── 5. Zero-day snap ─────────────────────────────────────────────────────

def test_add_zero_snaps_forward_off_a_non_working_anchor():
    assert add_work_days('2026-08-22', 0, MON_FRI) == date(2026, 8, 24)


def test_subtract_zero_snaps_backward_off_a_non_working_anchor():
    assert subtract_work_days('2026-08-22', 0, MON_FRI) == date(2026, 8, 21)


def test_zero_leaves_a_working_anchor_alone():
    assert add_work_days('2026-08-17', 0, MON_FRI) == date(2026, 8, 17)
    assert subtract_work_days('2026-08-17', 0, MON_FRI) == date(2026, 8, 17)


def test_zero_snap_crosses_a_run_of_holidays():
    cal = _cal([1, 2, 3, 4, 5], ['2026-08-24', '2026-08-25', '2026-08-26'])
    assert add_work_days('2026-08-22', 0, cal) == date(2026, 8, 27)
    assert subtract_work_days('2026-08-24', 0, cal) == date(2026, 8, 21)


# ── Parity with cpp-cpm-engine ───────────────────────────────────────────

def test_parity_with_the_cpm_engine_python_reference():
    """Defects 4 and 5 are defects because cpp-cpm-engine answers
    differently. Compared directly when the engine's python_reference
    directory is on sys.path (for example through PYTHONPATH); skipped
    visibly otherwise, never passed vacuously."""
    cpm = pytest.importorskip(
        'cpm', reason="cpp-cpm-engine's python_reference is not on sys.path")
    if not hasattr(cpm, 'add_work_days'):
        pytest.skip('the importable cpm module is not the engine reference')
    shapes = [
        ([1, 2, 3, 4, 5], []),
        ([1, 2, 3, 4, 5], ['2026-09-07', '2026-12-25']),
        ([1, 2, 3, 4, 5, 6], ['2026-09-07']),
        ([0, 1, 2, 3, 4, 5, 6], []),
        ([1, 2, 3, 4], ['2026-08-19']),
    ]
    ns = [0, 0.4, 0.5, 0.6, 1, 1.5, 2, 2.5, 3, 7, 10.5]
    mine_fns = {'add_work_days': add_work_days,
                'subtract_work_days': subtract_work_days}
    compared = 0
    for work_days, holidays in shapes:
        for day in range(1, 60):
            iso = (date(2026, 8, 1) + timedelta(days=day)).isoformat()
            for n in ns:
                for name, mine_fn in mine_fns.items():
                    mine = mine_fn(iso, n, _cal(work_days, holidays))
                    theirs = getattr(cpm, name)(
                        iso, n, {'work_days': list(work_days),
                                 'holidays': list(holidays)})
                    assert mine == theirs, (name, work_days, iso, n, mine, theirs)
                    compared += 1
    assert compared == len(shapes) * 59 * len(ns) * 2
