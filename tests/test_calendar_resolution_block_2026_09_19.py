"""``calendar_resolution_block``: the disclosure every pipeline publishes.

``resolve_task_calendars`` reports on every TASK row in the file. A consumer
schedules only some of them (one project, no LOE / WBS summaries, ...), and
what it must disclose is what happened to THOSE activities. This builds that
block - the shape cpp-critical-path-validator publishes as
``calendar_resolution`` - for consumers to share rather than copy.
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, '..', 'scripts'))

from xer_parser import calendar_resolution_block, resolve_task_calendars  # noqa: E402


def _data():
    def task(tid, code, proj, clndr):
        return {'task_id': tid, 'task_code': code, 'task_name': 'Neutral ' + code,
                'proj_id': proj, 'clndr_id': clndr}
    return {'tables': {
        'PROJECT': {'fields': ['proj_id', 'clndr_id'], 'records': [
            {'proj_id': 'P1', 'clndr_id': 'STD'},
            {'proj_id': 'P2', 'clndr_id': ''}]},
        'CALENDAR': {'fields': ['clndr_id', 'clndr_name', 'default_flag'], 'records': [
            {'clndr_id': 'STD', 'clndr_name': 'Standard', 'default_flag': 'N'}]},
        'TASK': {'fields': ['task_id', 'task_code', 'task_name', 'proj_id', 'clndr_id'],
                 'records': [
                     task('1', 'A', 'P1', ''),          # blank -> project calendar
                     task('2', 'B', 'P1', 'STD'),       # explicit
                     task('3', 'C', 'P1', 'GHOST'),     # names an undeclared calendar
                     task('4', 'D', 'P2', ''),          # blank, nothing to fall back on
                 ]},
    }}


def test_every_row_is_reported_when_nothing_is_filtered():
    block = calendar_resolution_block(resolve_task_calendars(_data()))
    assert block == {
        'resolved_by_fallback_count': 1,
        'fallback_calendars': [{'clndr_id': 'STD', 'clndr_name': 'Standard',
                                'tier': 'project', 'task_count': 1}],
        'unresolved_count': 2,
        'unresolved': [
            {'task_code': 'C', 'task_name': 'Neutral C', 'clndr_id': 'GHOST',
             'reason': 'undeclared'},
            {'task_code': 'D', 'task_name': 'Neutral D', 'clndr_id': '',
             'reason': 'blank'}],
    }


def test_keep_limits_the_block_to_the_activities_a_pipeline_schedules():
    block = calendar_resolution_block(
        resolve_task_calendars(_data()), keep=lambda row: row['proj_id'] == 'P1')
    assert block['resolved_by_fallback_count'] == 1
    assert [u['task_code'] for u in block['unresolved']] == ['C']


def test_an_activity_without_a_code_is_named_by_its_task_id():
    data = _data()
    data['tables']['TASK']['records'][3]['task_code'] = ''
    block = calendar_resolution_block(resolve_task_calendars(data))
    assert [u['task_code'] for u in block['unresolved']] == ['C', '4']


def test_a_file_with_every_calendar_declared_is_an_empty_block():
    data = _data()
    data['tables']['TASK']['records'] = data['tables']['TASK']['records'][1:2]
    assert calendar_resolution_block(resolve_task_calendars(data)) == {
        'resolved_by_fallback_count': 0, 'fallback_calendars': [],
        'unresolved_count': 0, 'unresolved': []}
