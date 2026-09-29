"""Regression (2026-09-19): ``get_calendar_map`` entries carry default_flag.

A consumer that needs "the default calendar" reads ``default_flag`` off a
``get_calendar_map`` entry. Without the field it can only fall back, silently,
to "first calendar in the file", and a test that puts the default calendar
first in the table cannot tell the two apart.

Here the default calendar is SECOND, behind a seven-day calendar.
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'scripts'))

from xer_parser import get_calendar_map  # noqa: E402


def _data(records):
    return {'tables': {'CALENDAR': {
        'fields': ['clndr_id', 'clndr_name', 'day_hr_cnt', 'default_flag',
                   'clndr_data'],
        'records': records}}}


def test_entries_carry_default_flag_as_the_file_writes_it():
    cal_map = get_calendar_map(_data([
        {'clndr_id': 'SEVEN', 'clndr_name': 'Seven Day', 'day_hr_cnt': '8',
         'default_flag': 'N', 'clndr_data': ''},
        {'clndr_id': 'STD', 'clndr_name': 'Standard', 'day_hr_cnt': '8',
         'default_flag': 'Y', 'clndr_data': ''},
    ]))
    assert {cid: c['default_flag'] for cid, c in cal_map.items()} == {
        'SEVEN': 'N', 'STD': 'Y'}


def test_a_calendar_table_without_the_column_reads_as_not_default():
    cal_map = get_calendar_map({'tables': {'CALENDAR': {
        'fields': ['clndr_id', 'clndr_name', 'day_hr_cnt', 'clndr_data'],
        'records': [{'clndr_id': 'STD', 'clndr_name': 'Standard',
                     'day_hr_cnt': '8', 'clndr_data': ''}]}}})
    assert cal_map['STD']['default_flag'] == ''
