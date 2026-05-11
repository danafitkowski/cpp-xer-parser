# Contributing to `cpp-xer-parser`

Thank you for considering a contribution. This parser is the data-access foundation for an active forensic-scheduling consultancy and powers court-filed expert reports. Contributions are welcome and the bar is high.

---

## Quick rules

1. **Every commit must pass the existing tests.**
   ```bash
   python tests/test_xer_parser.py
   python tests/test_half_step.py
   ```
   Or with pytest:
   ```bash
   pip install pytest
   pytest tests/
   ```

2. **Run all tests before opening a PR.** CI runs the same suite on Ubuntu, macOS, and Windows across Python 3.10, 3.11, and 3.12.

3. **No real client XER files in tests.** Every fixture must be built synthetically in memory at test time. We deliberately ship no client data with this repo.

---

## Forensic-correctness rules

The parser is used in court. Sloppy contributions ship as evidence.

### Field-count discipline

Every `%R` row written by the generator must have exactly the same field count as the `%F` definition that precedes it. P6 silently refuses to import any XER whose `%R` field count diverges from `%F`. The generator already enforces this; any change that touches the writer must preserve the invariant.

### Encoding discipline

Default encoding is UTF-8. The parser auto-detects UTF-8 BOM and UTF-16 LE/BE BOM. The writer emits CRLF line endings by default. Both behaviors match what P6 itself does. Changes here must round-trip a real-world XER through parse → generate → parse without losing any bytes.

### Calendar decoding

The `clndr_data` field uses a nested-paren mini-language that varies between P6 versions and between large-program exports. The parser uses a balanced-paren walker as primary and a regex fallback for nested formats that the walker misses. Both paths must remain because some real-world XERs need both to capture every holiday.

### No truncation in user-facing output

`generate_summary` and `print_summary` are the user-facing surfaces. Neither must silently truncate a list ("top N", "first 30", "+ M more"). If a list is too long for the summary, slice it cleanly with an explicit `…N more (use get_table to retrieve full list)` annotation; never silently crop.

---

## Pull-request checklist

- [ ] All existing tests pass.
- [ ] New behavior is covered by a synthetic test fixture.
- [ ] No real client data appears in the diff (XER files, project names, activity IDs, dates earlier than 2026).
- [ ] The CHANGELOG entry under the next unreleased version describes the change.
- [ ] If you bumped the `_SKILL_VERSION` constant in `xer_parser.py`, the CHANGELOG matches.

---

## Style

- 4-space indentation. No tabs.
- Comments explain *why*, not *what*. The XER-format quirks in the parser header are the gold standard.
- Pure functions where possible.
- Performance-critical paths get a comment explaining the optimization.

---

## Reporting bugs

Open an issue at https://github.com/danafitkowski/cpp-xer-parser/issues.

A good bug report includes:

1. A minimal XER file that reproduces the issue (please redact any client data before sharing).
2. The expected output.
3. The observed output.
4. Python version (`python --version`).
5. Operating system.

Forensic-correctness bugs (silent wrong-answer paths, P6 import rejection, field-count drift) are treated as critical. We will publish a fix and a CHANGELOG entry. Performance regressions are handled in the next minor release.

---

## License

By contributing, you agree your contribution will be licensed under the MIT license that covers the project.

---

## Code of conduct

Be technically rigorous. Verify before asserting. Be courteous in code review. This parser is read by judges, opposing experts, and academics — its quality reflects on everyone who contributes.
