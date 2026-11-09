"""Use the installed package the way a caller does: write a small schedule,
parse it, validate it and run the command line on it. Run from outside the
repository, so the package is the installed copy, not scripts/."""
import os
import subprocess
import sys
import tempfile

import cpp_xer_parser as p
import cpp_xer_parser.xer_parser as x

assert not os.path.isdir(os.path.join(os.getcwd(), "scripts")), "run from outside the repo"
assert x.__file__.startswith(sys.prefix), x.__file__
assert x._VALIDATION_AVAILABLE
assert x.get_profile.__module__ == "cpp_xer_parser.config_profiles"

T = "\t"
rows = [
    ["ERMHDR", "24.12", "2026-01-05", "Project", "admin", "Test", "db", "Project Management", "CAD"],
    ["%T", "PROJECT"], ["%F", "proj_id", "proj_short_name", "clndr_id", "plan_start_date"],
    ["%R", "P1", "SMOKE", "C1", "2026-01-05 08:00"],
    ["%T", "CALENDAR"], ["%F", "clndr_id", "clndr_name", "day_hr_cnt", "default_flag", "clndr_data"],
    ["%R", "C1", "5-Day", "8", "Y", ""],
    ["%T", "TASK"], ["%F", "task_id", "task_code", "task_name", "proj_id", "clndr_id",
                     "task_type", "status_code", "target_drtn_hr_cnt"],
    ["%R", "T1", "A1000", "Start", "P1", "C1", "TT_Task", "TK_NotStart", "40"],
    ["%E"],
]
path = os.path.join(tempfile.mkdtemp(), "smoke.xer")
with open(path, "w", encoding="utf-8", newline="") as f:
    f.write("\r\n".join(T.join(r) for r in rows) + "\r\n")

data = p.parse_xer(path)
assert len(p.get_table(data, "TASK")) == 1
report = p.validate_schedule(data)
assert report is not None
out = subprocess.run([os.path.join(os.path.dirname(sys.executable), "cpp-xer-parser"),
                      "parse", path], capture_output=True, text=True, check=True).stdout
assert "TASK: 1 records" in out, out
print("cpp_xer_parser", p.__version__, "installed, parsed, validated")
