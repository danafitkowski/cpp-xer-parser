# Security Policy

`cpp-xer-parser` is used in production forensic delay analyses, EOT submissions, and expert-witness reports. Security defects — particularly any defect that could mislead a court — are treated as release-blocking.

Thank you for taking the time to report.

---

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | Yes                |
| < 0.1   | No                 |

The parser ships as `cpp-xer-parser` on GitHub. The most recent published version is always the supported reference; back-ports of security fixes to prior 0.1.x point releases are made on a best-effort basis.

---

## Reporting a vulnerability

Do **not** open a public GitHub issue for a suspected vulnerability.

Email `hello@criticalpathpartners.ca` with **the word `SECURITY` in the subject line**. Include:

- A description of the issue
- A minimal reproduction (parser version, Python version, OS, snippet, input)
- The forensic / operational impact you believe it has
- Whether you intend to publicly disclose, and on what timeline

You should expect an initial acknowledgement **within 72 hours**. A confirmed vulnerability will receive a triage plan within 7 days and a fix or mitigation timeline shortly after.

We will credit reporters in the release notes unless you ask to remain anonymous.

---

## What we consider a vulnerability

- **Forensic-correctness parse bug that could mislead a court.** Wrong field-count handling that silently drops records, calendar decoding that drops holidays without warning, BOM-detection failures that corrupt text, schema-drift detection that misses added/removed fields, generator output that P6 rejects on import after appearing valid, manifest hash mismatches, attribution leaks. The parser's whole value proposition is courtroom defensibility — these defects rank above conventional security bugs.
- **Information disclosure.** Path leaks through error messages, leakage of XER paths or contents through stack traces, leakage of customer-supplied schedule data through caches or logs, file-enumeration through user input on the CLI.
- **Denial of service.** Malformed XER inputs that exhaust memory or CPU, regex catastrophic-backtracking attacks against calendar data parsers, infinite loops in nested-paren decoding.
- **Supply-chain attack vectors.** The parser ships **zero third-party runtime dependencies** in production — a vendored or transitive dependency appearing in CI is itself a finding. Build-time arbitrary code execution, post-install scripts, CI secret exfiltration are in scope.

---

## What we do NOT consider a vulnerability

- **Performance degradation that does not affect correctness.** "It got 12% slower on a 50,000-activity XER" is not a security issue. Open a normal performance bug.
- **Style / lint issues.** Including pyflakes, black, and "best practice" complaints.
- **Citations that "could be worded better."** Citation defects are handled through the regular issue template, not the security channel.
- **Theoretical attacks** with no demonstrated reproduction against a current release.

---

## Disclosure policy

We follow a **90-day coordinated-disclosure timeline**:

1. **Day 0** — report received, reporter acknowledged within 72 hours.
2. **Day 0-7** — triage, severity assignment, fix plan.
3. **Day 7-60** — fix developed, tested against the full parser test suite plus any new regression test the reporter supplies.
4. **Day 60-90** — release coordinated with the reporter. Both sides agree a public-disclosure date.
5. **Day 90** — public disclosure (CHANGELOG entry, GitHub Security Advisory, optional CVE) regardless of whether all downstream consumers have upgraded. The parser is open-source; closed downstream consumers are responsible for their own patch windows.

If the issue is being actively exploited in the wild, we will compress the timeline and ship as soon as a fix is verified.

---

## No bug-bounty program

We do not currently run a paid bug-bounty program. We will credit reporters in the release notes and on the project README. If your employer requires a bounty as a condition of disclosure, please email anyway and we can discuss.

---

## Scope

In scope:

- `cpp-xer-parser` source on GitHub
- The bundled `scripts/xer_parser.py`, `scripts/validation.py`, and `scripts/config_profiles.py`
- `criticalpathpartners.ca` website to the extent it advertises parser behavior

Out of scope:

- Third-party clones, forks, or re-distributions
- Vendored copies of `xer_parser.py` shipped inside companion repos (those repos have their own security channel; report against the canonical upstream here)
- The closed CPP forensic skill suite — these have their own security channel; email `hello@criticalpathpartners.ca` and we will route.

---

*Last updated: 2026-05-16.*
