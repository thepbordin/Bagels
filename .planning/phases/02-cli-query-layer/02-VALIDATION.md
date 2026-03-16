---
phase: 2
slug: cli-query-layer
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3+ |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `pytest tests/cli/ -v -k "test_" --tb=short` |
| **Full suite command** | `pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/cli/ -v -k "test_" --tb=short`
- **After every plan wave:** Run `pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | CLI-01 | unit | `pytest tests/cli/test_records.py -v` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | CLI-02 | unit | `pytest tests/cli/test_records.py -v` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | CLI-03 | unit | `pytest tests/cli/test_records.py -v` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | CLI-04 | unit | `pytest tests/cli/test_summary.py -v` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | CLI-05 | unit | `pytest tests/cli/test_summary.py -v` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | CLI-06 | unit | `pytest tests/cli/test_categories.py -v` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 2 | CLI-07 | unit | `pytest tests/cli/test_accounts.py -v` | ❌ W0 | ⬜ pending |
| 02-03-03 | 03 | 2 | CLI-08 | unit | `pytest tests/cli/test_persons.py -v` | ❌ W0 | ⬜ pending |
| 02-04-01 | 04 | 2 | CLI-09 | unit | `pytest tests/cli/test_spending.py -v` | ❌ W0 | ⬜ pending |
| 02-04-02 | 04 | 2 | CLI-10 | unit | `pytest tests/cli/test_trends.py -v` | ❌ W0 | ⬜ pending |
| 02-05-01 | 05 | 3 | LLM-01 | unit | `pytest tests/cli/test_llm.py -v` | ❌ W0 | ⬜ pending |
| 02-05-02 | 05 | 3 | LLM-02 | unit | `pytest tests/cli/test_llm.py -v` | ❌ W0 | ⬜ pending |
| 02-05-03 | 05 | 3 | LLM-03 | unit | `pytest tests/cli/test_llm.py -v` | ❌ W0 | ⬜ pending |
| 02-05-04 | 05 | 3 | LLM-04 | unit | `pytest tests/cli/test_llm.py -v` | ❌ W0 | ⬜ pending |
| 02-05-05 | 05 | 3 | LLM-05 | unit | `pytest tests/cli/test_llm.py -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/cli/conftest.py` — shared fixtures for CLI testing (CliRunner, test database, sample data)
- [ ] `tests/cli/test_records.py` — stubs for CLI-01, CLI-02, CLI-03
- [ ] `tests/cli/test_summary.py` — stubs for CLI-04, CLI-05
- [ ] `tests/cli/test_categories.py` — stubs for CLI-06
- [ ] `tests/cli/test_accounts.py` — stubs for CLI-07
- [ ] `tests/cli/test_persons.py` — stubs for CLI-08
- [ ] `tests/cli/test_spending.py` — stubs for CLI-09
- [ ] `tests/cli/test_trends.py` — stubs for CLI-10
- [ ] `tests/cli/test_llm.py` — stubs for LLM-01, LLM-02, LLM-03, LLM-04, LLM-05
- [ ] `tests/cli/test_output_formatters.py` — stubs for output formatting validation
- [ ] Update `tests/conftest.py` — add CLI-specific fixtures if needed

*Infrastructure Note: pytest 8.3+ and conftest.py already configured from Phase 1. Wave 0 adds CLI-specific test files and fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Table visual formatting | CLI-01, CLI-04 | Terminal width, borders, colors vary | Run `bagels records list --table` and verify readable output |
| Rich progress indicators | All | Visual feedback during queries | Run `bagels records list --limit 1000` and observe progress bar |
| YAML parseability by LLMs | LLM-01, LLM-02 | Requires external LLM validation | Run `bagels llm context --month 2026-03 | tee output.yaml` and validate YAML structure |

*All other behaviors have automated verification via Click CliRunner and output assertions.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
