"""Regression (2026-09-29): the writer, the reader's overflow cells, the
generation table order and the schedule summary.

- WRITER. XER is tab-delimited and newline-terminated. generate_xer wrote a
  value containing a tab or a line break as it stood, so the tab added a
  phantom column and the line break split the row: 'Pour<TAB>slab' came back
  as task_name 'Pour' with status_code 'slab'. Every emitted token now has
  runs of tab/CR/LF collapsed to one space.
- READER. A %R row with more cells than its %F header lost the extra cells
  without a trace. They are kept under '__extra_<column>' keys.
- TABLE_ORDER spelled the resource-code assignment table RSRCCAT, a header no
  measured export writes (P6 writes RSRCRCAT), and carried a phantom
  RISKTYPES entry.
- SUMMARY. loe_count counted WBS summary rows as LOE; percent_complete counts
  milestones, so a work-only figure is added; critical_activities was cut at
  50 entries.

Every XER here is built in the test.
"""
import os
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(SCRIPT_DIR, '..', 'scripts')
sys.path.insert(0, SCRIPTS)

from xer_parser import (  # noqa: E402
    TABLE_ORDER,
    generate_summary,
    generate_xer,
    parse_xer,
)


def _round_trip(data):
    fd, path = tempfile.mkstemp(suffix='.xer')
    os.close(fd)
    try:
        generate_xer(data, path)
        with open(path, encoding='utf-8', newline='') as f:
            raw = f.read()
        return parse_xer(path), raw
    finally:
        os.remove(path)


def _task_table(records, fields=('task_id', 'task_name', 'status_code')):
    return {'tables': {'TASK': {'fields': list(fields), 'records': records}}}


# ── Writer: embedded delimiters ──────────────────────────────────────────

def test_a_tab_in_a_value_no_longer_shifts_the_row():
    parsed, _ = _round_trip(_task_table([
        {'task_id': '1', 'task_name': 'Pour\tslab', 'status_code': 'TK_NotStart'}]))
    rec = parsed['tables']['TASK']['records'][0]
    assert rec['task_name'] == 'Pour slab', rec
    assert rec['status_code'] == 'TK_NotStart', rec


def test_a_line_break_in_a_value_no_longer_splits_the_row():
    parsed, _ = _round_trip(_task_table([
        {'task_id': '1', 'task_name': 'Line one\nLine two', 'status_code': 'TK_Active'}]))
    recs = parsed['tables']['TASK']['records']
    assert len(recs) == 1, recs
    assert recs[0]['task_name'] == 'Line one Line two'
    assert recs[0]['status_code'] == 'TK_Active'


def test_carriage_returns_are_collapsed_too():
    parsed, raw = _round_trip(_task_table([
        {'task_id': '1', 'task_name': 'A\r\nB\rC', 'status_code': 'TK_Complete'}]))
    recs = parsed['tables']['TASK']['records']
    assert len(recs) == 1
    assert recs[0]['task_name'] == 'A B C', recs[0]
    assert recs[0]['status_code'] == 'TK_Complete'


def test_a_poisoned_row_does_not_disturb_the_rows_around_it():
    parsed, _ = _round_trip(_task_table([
        {'task_id': '1', 'task_name': 'first', 'status_code': 'TK_NotStart'},
        {'task_id': '2', 'task_name': 'tab\there\nand a break', 'status_code': 'TK_Active'},
        {'task_id': '3', 'task_name': 'third', 'status_code': 'TK_Complete'},
    ]))
    recs = parsed['tables']['TASK']['records']
    assert [r['task_id'] for r in recs] == ['1', '2', '3']
    assert [r['status_code'] for r in recs] == ['TK_NotStart', 'TK_Active', 'TK_Complete']


def test_clean_values_are_written_unchanged():
    parsed, raw = _round_trip(_task_table([
        {'task_id': '1', 'task_name': 'Mobilize  site (phase 1)', 'status_code': None}]))
    rec = parsed['tables']['TASK']['records'][0]
    assert rec['task_name'] == 'Mobilize  site (phase 1)'
    assert rec['status_code'] == ''
    assert '%R\t1\tMobilize  site (phase 1)\t\r\n' in raw


def test_a_tab_in_the_header_or_a_field_name_cannot_add_a_column():
    data = _task_table([{'task_id': '1', 'task\tname': 'x', 'status_code': 'y'}],
                       fields=('task_id', 'task\tname', 'status_code'))
    data['ermhdr'] = {'raw': ['ERMHDR', '24.12', '2026-09-29', 'Project',
                              'user\tname', 'Full Name', 'db', 'Project Management',
                              'CAD']}
    _, raw = _round_trip(data)
    lines = raw.split('\r\n')
    assert lines[0].count('\t') == 8, lines[0]
    f_line = next(line for line in lines if line.startswith('%F'))
    assert f_line == '%F\ttask_id\ttask name\tstatus_code', f_line


# ── Reader: cells beyond the header are kept ─────────────────────────────

def test_cells_beyond_the_header_are_kept_under_extra_keys():
    xer = ('ERMHDR\t24.12\t2026-09-29\tProject\tu\tU\tdb\tProject Management\tCAD\r\n'
           '%T\tTASK\r\n'
           '%F\ttask_id\ttask_code\r\n'
           '%R\t1\tA100\tstray\tsecond stray\r\n'
           '%R\t2\tA200\r\n'
           '%E\r\n')
    fd, path = tempfile.mkstemp(suffix='.xer')
    os.close(fd)
    try:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(xer)
        recs = parse_xer(path)['tables']['TASK']['records']
    finally:
        os.remove(path)
    assert recs[0] == {'task_id': '1', 'task_code': 'A100',
                       '__extra_2': 'stray', '__extra_3': 'second stray'}, recs[0]
    assert recs[1] == {'task_id': '2', 'task_code': 'A200'}, recs[1]


# ── TABLE_ORDER ──────────────────────────────────────────────────────────

def test_table_order_names_the_table_p6_writes():
    assert 'RSRCRCAT' in TABLE_ORDER
    assert 'RSRCCAT' not in TABLE_ORDER
    assert 'RISKTYPES' not in TABLE_ORDER
    assert len(TABLE_ORDER) == len(set(TABLE_ORDER)) == 39


def test_rsrcrcat_is_written_in_its_slot():
    data = {'tables': {
        'MEMOTYPE': {'fields': ['memo_type_id'], 'records': [{'memo_type_id': '1'}]},
        'RSRCRCAT': {'fields': ['rsrc_id'], 'records': [{'rsrc_id': '1'}]},
        'RCATVAL': {'fields': ['rsrc_catg_id'], 'records': [{'rsrc_catg_id': '1'}]},
        'ZZCUSTOM': {'fields': ['x'], 'records': [{'x': '1'}]},
    }}
    _, raw = _round_trip(data)
    order = [line.split('\t')[1] for line in raw.split('\r\n') if line.startswith('%T')]
    assert order == ['RCATVAL', 'RSRCRCAT', 'MEMOTYPE', 'ZZCUSTOM'], order


# ── Summary ──────────────────────────────────────────────────────────────

def _summary_data(tasks):
    return {'tables': {
        'TASK': {'records': tasks},
        'CALENDAR': {'records': [
            {'clndr_id': 'C1', 'clndr_name': 'Std', 'day_hr_cnt': '8',
             'clndr_data': ''}]},
    }}


def _task(code, task_type, status, float_hr='40'):
    return {'task_id': code, 'task_code': code, 'task_name': code,
            'task_type': task_type, 'status_code': status, 'clndr_id': 'C1',
            'total_float_hr_cnt': float_hr}


def _mixed():
    return _summary_data([
        _task('A', 'TT_Task', 'TK_Complete'),
        _task('B', 'TT_Task', 'TK_Complete'),
        _task('C', 'TT_Task', 'TK_Active'),
        _task('D', 'TT_Rsrc', 'TK_NotStart'),
        _task('M1', 'TT_Mile', 'TK_Complete'),
        _task('M2', 'TT_FinMile', 'TK_Complete'),
        _task('L1', 'TT_LOE', 'TK_Active'),
        _task('W1', 'TT_WBS', 'TK_Complete'),
        _task('W2', 'TT_WBS', 'TK_NotStart'),
    ])


def test_loe_and_wbs_summary_rows_are_counted_separately():
    sm = generate_summary(_mixed())['schedule_metrics']
    assert sm['loe_count'] == 1, sm['loe_count']
    assert sm['wbs_count'] == 2, sm.get('wbs_count')
    assert sm['total_including_loe'] == 9


def test_percent_complete_counts_milestones_and_work_only_does_not():
    sm = generate_summary(_mixed())['schedule_metrics']
    # 4 work tasks + 2 milestones; complete = 2 work + 2 milestones.
    assert sm['total_activities'] == 6
    assert sm['percent_complete'] == 66.7
    assert sm['work_task_count'] == 4
    assert sm['complete_work'] == 2
    assert sm['percent_complete_work'] == 50.0


def test_work_only_completion_is_zero_when_there_is_no_work():
    sm = generate_summary(_summary_data([
        _task('M1', 'TT_Mile', 'TK_Complete')]))['schedule_metrics']
    assert sm['work_task_count'] == 0
    assert sm['percent_complete_work'] == 0


def test_every_critical_activity_is_listed():
    tasks = [_task('T%03d' % i, 'TT_Task', 'TK_NotStart', float_hr='0')
             for i in range(60)]
    cp = generate_summary(_summary_data(tasks))['critical_path']
    assert cp['critical_by_float_zero'] == 60
    assert len(cp['critical_activities']) == 60, len(cp['critical_activities'])
    assert 'note' not in cp


def test_print_summary_names_wbs_rows_and_work_only_completion():
    import io
    from contextlib import redirect_stdout
    from xer_parser import print_summary
    buf = io.StringIO()
    with redirect_stdout(buf):
        print_summary(_mixed())
    out = buf.getvalue()
    assert '(excl. 1 LOE, 2 WBS summary)' in out, out
    assert 'Work-task completion: 2/4 (50.0%, excl. milestones)' in out, out
