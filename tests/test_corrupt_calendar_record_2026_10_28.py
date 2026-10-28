"""A corrupt calendar record is P6's internal Standard (2026-10-28).

A CALENDAR record is corrupt when (a) its DaysOfWeek block serializes shift
slots finish-first, (f|HH:MM|s|HH:MM), AND (b) its clndr_type is not a legal
P6 token (CA_Base / CA_Rsrc / CA_Project); the record seen in real exports
says 'CT_Project'. P6 cannot bind such a record and schedules the activities
assigned to it on its internal Standard calendar: Monday to Friday, eight
hours a day, no exceptions. get_calendar_map now gives the record that
calendar, flags it p6_fallback, carries the calendar-corrupt-p6-fallback
ALERT on the entry (calendar_corrupt_fallbacks reads it back) and raises a
CalendarCorruptRecordWarning. The screen is cpp-cpm-engine's
decode_calendar_record, copied into the parser unchanged.

Finish-first slots alone are a legitimate export variant: a record with a
legal clndr_type decodes as declared, holidays included, as before.

The tests marked [discriminating] fail on v0.4.0, which read the corrupt
record as the Monday-to-Saturday week it declares. Every calendar string
below is built in this file; no real export is copied.
"""
import os
import sys
import tempfile
import warnings
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'scripts'))

import xer_parser  # noqa: E402
from xer_parser import (get_calendar_map, get_work_days_between,  # noqa: E402
                        duration_hours_to_days, calendar_shift_hours, parse_xer)

TAB = '\t'

# Six working days, Monday to Saturday, each two finish-first shifts
# 08:00-12:00 and 13:00-17:00, no exceptions.
_SIX_DAY_FINISH_FIRST = (
    '(0||CalendarData()('
    '(0||DaysOfWeek()('
    '(0||1()())'
    + ''.join(
        '(0||%d()((0||0(f|12:00|s|08:00)())(0||1(f|17:00|s|13:00)())))' % d
        for d in range(2, 8)) +
    '))'
    '(0||Exceptions()())))'
)

# The same week with one holiday: serial 46272 = Monday 2026-09-07 off.
_SIX_DAY_FINISH_FIRST_WITH_HOLIDAY = (
    '(0||CalendarData()('
    '(0||DaysOfWeek()('
    '(0||1()())'
    + ''.join(
        '(0||%d()((0||0(f|12:00|s|08:00)())(0||1(f|17:00|s|13:00)())))' % d
        for d in range(2, 8)) +
    '))'
    '(0||Exceptions()('
    '(0||0(d|46272)())'
    '))))'
)

# Monday to Saturday, start-first.
_SIX_DAY_START_FIRST = (
    '(0||CalendarData()((0||DaysOfWeek()((0||1()())'
    + ''.join(
        '(0||%d()((0||0(s|08:00|f|12:00)())(0||1(s|13:00|f|17:00)())))' % d
        for d in range(2, 8))
    + '))(0||Exceptions())(0||VIEW(ShowTotal|Y)())))'
)

# Monday to Friday, start-first.
_FIVE_DAY_START_FIRST = (
    '(0||CalendarData()((0||DaysOfWeek()((0||1()())'
    + ''.join(
        '(0||%d()((0||0(s|08:00|f|12:00)())(0||1(s|13:00|f|17:00)())))' % d
        for d in range(2, 7))
    + '(0||7()()))))(0||Exceptions())(0||VIEW(ShowTotal|Y)())))'
)

_FIELDS = ['clndr_id', 'clndr_name', 'clndr_type', 'day_hr_cnt',
           'week_hr_cnt', 'default_flag', 'clndr_data']


def _row(cid, name, ctype, blob, day_hr='8', week_hr='48'):
    return {'clndr_id': cid, 'clndr_name': name, 'clndr_type': ctype,
            'day_hr_cnt': day_hr, 'week_hr_cnt': week_hr,
            'default_flag': 'N', 'clndr_data': blob}


def _data(rows):
    return {'tables': {'CALENDAR': {'fields': list(_FIELDS),
                                    'records': rows}}}


def _map(rows):
    """get_calendar_map on the rows, with the warnings it raised."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        cal_map = get_calendar_map(_data(rows))
    # getattr: the pins below also run on v0.4.0, which has no such class.
    cls = getattr(xer_parser, 'CalendarCorruptRecordWarning', None)
    corrupt = [w for w in caught if cls and issubclass(w.category, cls)]
    return cal_map, corrupt


def test_a_corrupt_record_is_p6s_internal_standard():
    # [discriminating] v0.4.0 read it as the Monday-to-Saturday week it declares.
    cm, fired = _map([_row('9001', 'Six Day Site Works', 'CT_Project',
                           _SIX_DAY_FINISH_FIRST)])
    entry = cm['9001']
    assert entry['work_days'] == [1, 2, 3, 4, 5], entry['work_days']
    assert entry['work_day_names'] == ['Monday', 'Tuesday', 'Wednesday',
                                       'Thursday', 'Friday']
    assert entry['holidays'] == [] and entry['special_workdays'] == []
    assert entry['exceptions'] == []
    assert entry['hours_per_day'] == 8.0
    assert entry['hours_per_week'] == 40.0
    assert entry['p6_fallback'] is True
    assert not entry.get('empty_record')
    assert entry['raw'] == _SIX_DAY_FINISH_FIRST
    assert entry['clndr_name'] == 'Six Day Site Works'
    assert entry['default_flag'] == 'N'
    assert len(fired) == 1, 'CalendarCorruptRecordWarning must fire once'
    assert "'CT_Project'" in str(fired[0].message)


def test_the_alert_names_the_calendar_its_type_and_the_declared_week():
    # [discriminating] calendar_corrupt_fallbacks is new.
    cm, _ = _map([_row('9001', 'Six Day Site Works', 'CT_Project',
                       _SIX_DAY_FINISH_FIRST)])
    alerts = xer_parser.calendar_corrupt_fallbacks(cm)
    assert len(alerts) == 1
    a = alerts[0]
    assert a['severity'] == 'ALERT'
    assert a['context'] == 'calendar-corrupt-p6-fallback'
    assert a['message'].startswith(
        'FORENSIC FINDING: calendar 9001 (Six Day Site Works)')
    assert "clndr_type field holds 'CT_Project'" in a['message']
    assert 'Mon-Fri, 8 h/day, NO exceptions' in a['message']
    assert '6 working day(s)/week at 8 h/day' in a['message']
    # A copy: changing it does not change the map.
    a['message'] = ''
    assert xer_parser.calendar_corrupt_fallbacks(cm)[0]['message']


def test_a_corrupt_record_works_eight_hours_whatever_it_declares():
    # [discriminating] 40 hours on a row declaring 10 is five days, as P6
    # schedules it, not four.
    cm, _ = _map([_row('9001', 'Six Day Site Works', 'CT_Project',
                       _SIX_DAY_FINISH_FIRST, day_hr='10', week_hr='60')])
    assert cm['9001']['hours_per_day'] == 8.0
    assert cm['9001']['hours_per_week'] == 40.0
    assert duration_hours_to_days(40, cm['9001']) == 5.0
    # Its hours were not taken from shifts, so it is not listed there.
    assert calendar_shift_hours(cm) == []


def test_a_corrupt_record_counts_no_saturdays():
    # [discriminating] Monday 2 Nov to Saturday 14 Nov 2026: ten weekdays and
    # two Saturdays.
    cm, _ = _map([_row('9001', 'Six Day Site Works', 'CT_Project',
                       _SIX_DAY_FINISH_FIRST),
                  _row('9002', 'Six Day', 'CA_Project', _SIX_DAY_FINISH_FIRST)])
    span = (datetime(2026, 11, 2), datetime(2026, 11, 14))
    assert get_work_days_between(*span, cm['9001']) == 10
    assert get_work_days_between(*span, cm['9002']) == 12


def test_finish_first_slots_with_a_legal_type_decode_as_declared():
    for legal in ('CA_Base', 'CA_Rsrc', 'CA_Project'):
        cm, fired = _map([_row('9002', 'Standard Six Day', legal,
                               _SIX_DAY_FINISH_FIRST_WITH_HOLIDAY)])
        entry = cm['9002']
        assert not entry.get('p6_fallback'), legal
        assert entry['work_days'] == [1, 2, 3, 4, 5, 6], legal
        assert entry['holidays'] == ['2026-09-07'], legal
        assert entry['hours_per_day'] == 8.0, legal
        assert 'corrupt_record_alert' not in entry, legal
        assert fired == [], legal


def test_an_illegal_type_on_start_first_slots_decodes_as_declared():
    # Both conjuncts are needed: the type alone is not the corruption.
    cm, fired = _map([_row('9003', 'Six Day', 'CT_Project',
                           _SIX_DAY_START_FIRST)])
    assert cm['9003']['work_days'] == [1, 2, 3, 4, 5, 6]
    assert not cm['9003'].get('p6_fallback')
    assert fired == []


def test_finish_first_slots_with_no_type_take_the_fallback():
    # [discriminating] A blank or missing clndr_type is not a legal token, so
    # it fails conjunct (b), as in the engine. A genuine export writes it.
    for row in (_row('9004', 'Untyped', '', _SIX_DAY_FINISH_FIRST),
                {k: v for k, v in _row('9004', 'Untyped', '',
                                       _SIX_DAY_FINISH_FIRST).items()
                 if k != 'clndr_type'}):
        cm, fired = _map([row])
        assert cm['9004']['work_days'] == [1, 2, 3, 4, 5]
        assert cm['9004']['p6_fallback'] is True
        assert len(fired) == 1


def test_a_clean_record_is_unchanged_and_silent():
    cm, fired = _map([_row('101', 'Five Day', 'CA_Base',
                           _FIVE_DAY_START_FIRST, week_hr='40')])
    assert cm['101']['work_days'] == [1, 2, 3, 4, 5]
    assert cm['101']['hours_per_day'] == 8.0
    assert not cm['101'].get('p6_fallback')
    assert 'corrupt_record_alert' not in cm['101']
    assert fired == []


def test_an_empty_record_is_not_a_corrupt_record():
    cm, fired = _map([_row('E1', 'Empty', 'CA_Base', '', day_hr='10')])
    assert cm['E1']['empty_record'] is True and cm['E1']['p6_fallback'] is True
    assert cm['E1']['declared_hours_per_day'] == 10.0
    assert 'corrupt_record_alert' not in cm['E1']
    assert fired == []


def test_only_the_corrupt_record_in_a_file_falls_back():
    # [discriminating]
    cm, fired = _map([
        _row('9001', 'Six Day Site Works', 'CT_Project', _SIX_DAY_FINISH_FIRST),
        _row('9002', 'Standard Six Day', 'CA_Base',
             _SIX_DAY_FINISH_FIRST_WITH_HOLIDAY),
        _row('101', 'Five Day', 'CA_Base', _FIVE_DAY_START_FIRST, week_hr='40'),
    ])
    assert cm['9001'].get('p6_fallback') is True
    assert not cm['9002'].get('p6_fallback')
    assert not cm['101'].get('p6_fallback')
    alerts = xer_parser.calendar_corrupt_fallbacks(cm)
    assert len(alerts) == 1 and 'calendar 9001' in alerts[0]['message']
    assert len(fired) == 1


def test_a_corrupt_record_read_from_an_xer_file():
    # [discriminating] End to end through parse_xer.
    lines = ['ERMHDR\t24.12\t2026-10-28\tProject\tuser\tUser\tdb\tProject Management\tUSD',
             '%T\tCALENDAR', '%F\t' + TAB.join(_FIELDS)]
    for r in (_row('9001', 'Six Day Site Works', 'CT_Project', _SIX_DAY_FINISH_FIRST),
              _row('9002', 'Six Day', 'CA_Project', _SIX_DAY_FINISH_FIRST)):
        lines.append('%R\t' + TAB.join(r[f] for f in _FIELDS))
    lines.append('%E')
    fd, path = tempfile.mkstemp(suffix='.xer')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            data = parse_xer(path)
    finally:
        os.unlink(path)
    cm, fired = _map(data['tables']['CALENDAR']['records'])
    assert cm['9001']['work_days'] == [1, 2, 3, 4, 5]
    assert cm['9002']['work_days'] == [1, 2, 3, 4, 5, 6]
    assert len(fired) == 1


class _Skip(Exception):
    pass


def test_the_screen_is_the_engines_decoder():
    """Compared with cpp-cpm-engine's decode_calendar_record when the
    engine's python_reference directory is on sys.path; skipped visibly
    otherwise, never passed vacuously."""
    try:
        import cpm
    except ImportError:
        cpm = None
    if cpm is None or not hasattr(cpm, 'decode_calendar_record'):
        reason = "cpp-cpm-engine's python_reference is not on sys.path"
        if 'pytest' in sys.modules:
            sys.modules['pytest'].skip(reason)
        raise _Skip(reason)
    cases = [
        ('9001', 'Six Day Site Works', 'CT_Project', _SIX_DAY_FINISH_FIRST),
        ('9002', 'Standard Six Day', 'CA_Base', _SIX_DAY_FINISH_FIRST_WITH_HOLIDAY),
        ('9003', 'Six Day', 'CT_Project', _SIX_DAY_START_FIRST),
        ('9004', 'Untyped', '', _SIX_DAY_FINISH_FIRST),
        ('101', 'Five Day', 'CA_Base', _FIVE_DAY_START_FIRST),
        ('E1', 'Empty', 'CA_Base', ''),
    ]
    for cid, name, ctype, blob in cases:
        mine_alerts, theirs_alerts = [], []
        mine = xer_parser.decode_calendar_record(cid, name, blob, mine_alerts,
                                                 clndr_type=ctype)
        theirs = cpm.decode_calendar_record(cid, name, blob, theirs_alerts,
                                            clndr_type=ctype)
        assert mine == theirs, (cid, mine, theirs)
        assert mine_alerts == theirs_alerts, cid
        assert xer_parser.decode_clndr_data(blob, ctype) == \
            cpm.decode_clndr_data(blob, ctype), cid


if __name__ == '__main__':
    tests = [f for name, f in list(globals().items())
             if name.startswith('test_') and callable(f)]
    failed = skipped = 0
    for t in tests:
        try:
            t()
            print(f'ok  {t.__name__}')
        except _Skip as e:
            print(f'SKIP {t.__name__}: {e}')
            skipped += 1
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
    print(f'{len(tests) - skipped} / {len(tests)} passed, {skipped} skipped')
