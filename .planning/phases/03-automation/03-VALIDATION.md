---
phase: 3
slug: automation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8.3.1 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/git/ tests/automation/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -x -q --ignore=tests/managers/test_utils.py` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/git/ tests/automation/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -x -q --ignore=tests/managers/test_utils.py`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-W0-01 | W0 | 0 | DATA-07 | unit | `uv run pytest tests/automation/test_hooks.py -x -q` | Wave 0 | ⬜ pending |
| 03-W0-02 | W0 | 0 | DATA-08, GIT-08 | unit | `uv run pytest tests/automation/test_startup.py -x -q` | Wave 0 | ⬜ pending |
| 03-W0-03 | W0 | 0 | GIT-02, GIT-07 | unit | `uv run pytest tests/git/test_operations.py -x -q` | Wave 0 | ⬜ pending |
| 03-W0-04 | W0 | 0 | GIT-03..GIT-06 | integration | `uv run pytest tests/cli/test_git.py -x -q` | Wave 0 | ⬜ pending |
| 03-W0-05 | W0 | 0 | CFG-01..CFG-05 | unit | `uv run pytest tests/test_git_config.py -x -q` | Wave 0 | ⬜ pending |
| 03-01-01 | 01 | 1 | CFG-01..CFG-05 | unit | `uv run pytest tests/test_git_config.py -x -q` | Wave 0 | ⬜ pending |
| 03-02-01 | 02 | 1 | DATA-07 | unit | `uv run pytest tests/automation/test_hooks.py -x -q` | Wave 0 | ⬜ pending |
| 03-03-01 | 03 | 2 | DATA-08, GIT-08 | unit | `uv run pytest tests/automation/test_startup.py -x -q` | Wave 0 | ⬜ pending |
| 03-04-01 | 04 | 2 | GIT-02, GIT-07 | unit | `uv run pytest tests/git/test_operations.py -x -q` | Wave 0 | ⬜ pending |
| 03-05-01 | 05 | 3 | GIT-03..GIT-06 | integration | `uv run pytest tests/cli/test_git.py -x -q` | Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/git/__init__.py` — package init
- [ ] `tests/git/test_operations.py` — covers GIT-02, GIT-07; use tmp git repo fixture
- [ ] `tests/automation/__init__.py` — package init
- [ ] `tests/automation/test_hooks.py` — covers DATA-07; mock export/commit functions
- [ ] `tests/automation/test_startup.py` — covers DATA-08, GIT-08; mock importer + pull
- [ ] `tests/cli/test_git.py` — covers GIT-03, GIT-04, GIT-05, GIT-06; use Click test runner + tmp git repo
- [ ] `tests/test_git_config.py` — covers CFG-01 through CFG-05

Reuse existing fixtures: `in_memory_db`, `temp_directory`, `sample_records` from `tests/conftest.py`.

Git repo fixture pattern:
```python
@pytest.fixture
def tmp_git_repo(tmp_path):
    from git import Repo
    repo = Repo.init(tmp_path)
    (tmp_path / "records").mkdir()
    return repo, tmp_path
```

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Auto-pull on startup with real remote | GIT-08 | Requires actual Git remote | Configure remote, make change on remote, restart app, verify import ran |
| TUI status indicator during background import | DATA-08 | Visual/interactive behavior | Start app with YAML changes, observe status widget |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
