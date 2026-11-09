"""cpp-xer-parser, installed: ``pip install cpp-xer-parser``.

The package is the repository's scripts/ directory. Everything the parser
offers is in ``cpp_xer_parser.xer_parser``; the names below are the ones
most callers need::

    from cpp_xer_parser import parse_xer, get_table, print_summary

A plain clone does not import this file: it puts scripts/ on sys.path and
imports ``xer_parser`` directly, as the README's quick start shows.
"""
from .xer_parser import (  # noqa: F401
    build_activity_code_map,
    build_predecessor_map,
    build_resource_map,
    build_udf_map,
    build_wbs_map,
    compute_half_step_xer,
    generate_summary,
    generate_xer,
    get_calendar_map,
    get_fields,
    get_table,
    get_work_days_between,
    parse_xer,
    print_summary,
    validate_schedule,
)

__version__ = '0.6.1'

__all__ = [
    'parse_xer', 'get_table', 'get_fields', 'get_calendar_map',
    'get_work_days_between', 'build_wbs_map', 'build_resource_map',
    'build_predecessor_map', 'build_activity_code_map', 'build_udf_map',
    'generate_summary', 'print_summary', 'generate_xer',
    'compute_half_step_xer', 'validate_schedule', '__version__',
]
