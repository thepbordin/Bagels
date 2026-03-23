---
phase: 06
slug: skill-md-for-llm-cli-usage-documentation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual review — documentation-only phase |
| **Config file** | none |
| **Quick run command** | `test -f SKILL.md && echo "exists"` |
| **Full suite command** | `test -f SKILL.md && head -1 SKILL.md` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `test -f SKILL.md && echo "exists"`
- **After every plan wave:** Run `test -f SKILL.md && head -1 SKILL.md`
- **Before `/gsd:verify-work`:** File must exist and contain all documented commands
- **Max feedback latency:** 1 second

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | TBD | manual | `grep -c "bagels" SKILL.md` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements — this phase creates a single documentation file.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SKILL.md accuracy | TBD | Command docs must match actual CLI output | Run each documented command and compare output format |
| Workflow completeness | TBD | All four workflows must be present | Check SKILL.md contains all workflow sections from CONTEXT.md |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 1s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
