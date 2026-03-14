---
phase: 01
slug: foundation
status: revised
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
revised: 2026-03-14
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.1 |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `pytest tests/export/ tests/import/ -v` |
| **Full suite command** | `pytest tests/ -v --cov=src/bagels` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/export/ tests/import/ -v`
- **After every plan wave:** Run `pytest tests/ -v --cov=src/bagels`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | DATA-01 | unit | `pytest tests/export/test_accounts.py -x -v` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | DATA-02 | unit | `pytest tests/export/test_categories.py -x -v` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | DATA-03 | unit | `pytest tests/export/test_persons.py -x -v` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | DATA-04 | unit | `pytest tests/export/test_templates.py -x -v` | ❌ W0 | ⬜ pending |
| 01-01b-01 | 01b | 1 | DATA-05 | unit | `pytest tests/export/test_records.py -x -v` | ❌ W0 | ⬜ pending |
| 01-01b-02 | 01b | 1 | FMT-02 | unit | `pytest tests/export/test_slug_generator.py -x -v` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | DATA-06 | unit | `pytest tests/import/test_validator.py -x -v` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | DATA-06 | unit | `pytest tests/import/test_import.py -x -v` | ❌ W0 | ⬜ pending |
| 01-05-01 | 05 | 4 | GIT-01 | integration | `pytest tests/integration/test_git.py -x -v` | ❌ W0 | ⬜ pending |
| 01-05-02 | 05 | 4 | CMD-01 | integration | `python -c "from bagels.cli.export import export_command"` | ❌ W0 | ⬜ pending |
| 01-05-03 | 05 | 4 | CMD-02 | integration | `python -c "from bagels.cli.import import import_command"` | ❌ W0 | ⬜ pending |
| 01-05-04 | 05 | 4 | CMD-03 | integration | `python -c "from bagels.cli.init import init_command"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Wave 0 is **NOT REQUIRED** for this phase because:

1. **TDD Approach**: Plans 01, 01b, and 03 use TDD methodology where tests are created in RED phase (functions don't exist yet)
2. **Test File Creation**: The tasks themselves create the test files as part of implementation
3. **Verification Strategy**: Each task includes `<automated>` verification commands that will fail as expected in RED phase

**Validation Strategy Instead of Wave 0**:
- Plan 01 (Task 1): Creates `tests/conftest.py` with shared fixtures
- Plan 01 (Tasks 2-5): Creates 4 entity test files (accounts, categories, persons, templates)
- Plan 01b (Tasks 1-2): Creates 2 test files (records, slug_generator)
- Plan 03 (Tasks 1-2): Creates 2 import test files (validator, import)
- Total: 8 test files created across Plans 01, 01b, 03

**Nyquist Compliance**: Phase is nyquist_compliant: false because Wave 0 test stubs are not pre-created. However, all tasks have automated verification commands, and the TDD approach ensures test coverage through the RED→GREEN→REFACTOR cycle.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Git repository initialization in user's home directory | GIT-01 | Requires filesystem access to ~/.local/share/bagels | Run `bagels init`, verify `.git` directory created in data folder |
| Backup file creation before import | DATA-06 | Requires checking backup directory exists | Run `bagels import`, check ~/.local/share/bagels/backups/ for timestamped backup |
| CLI command user interaction | CMD-01, CMD-02, CMD-03 | Requires human verification of progress bars and error messages | Run commands, verify UX is acceptable (Task 5 checkpoint in Plan 05) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands (TDD approach)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 not required: TDD approach with test creation in tasks
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter (remains false - TDD approach without Wave 0)

**Approval:** pending
**Revision Note:** Wave 0 not required due to TDD methodology. All tasks have automated verification. Nyquist compliance flag reflects intentional design choice.
