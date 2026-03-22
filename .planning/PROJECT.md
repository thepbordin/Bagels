# Bagels

## What This Is

Bagels is a **Python terminal expense tracker** built on Textual TUI with SQLite storage. The v1 milestone transforms it from a binary database into a **Git-trackable, LLM-accessible** personal finance system with YAML data export and CLI query interface.

## Core Value

**Expense data that lives outside proprietary formats** — all financial data stored as human-readable, Git-tracked YAML files that can be queried via CLI and accessed by LLMs.

## Requirements

### Validated

- ✓ **TUI expense tracking** — Textual-based terminal interface for CRUD operations on expenses (existing)
- ✓ **Account management** — Multiple account tracking with beginning balances (existing)
- ✓ **Category system** — Hierarchical categories with Want/Need/Must nature (existing)
- ✓ **Records with splits** — Expense records with optional split-person tracking (existing)
- ✓ **Budget tracking** — Budget goals per category with progress visualization (existing)
- ✓ **SQLite persistence** — Local binary database storage (existing)

### Validated

- ✓ **TUI expense tracking** — Textual-based terminal interface for CRUD operations on expenses (existing)
- ✓ **Account management** — Multiple account tracking with beginning balances (existing)
- ✓ **Category system** — Hierarchical categories with Want/Need/Must nature (existing)
- ✓ **Records with splits** — Expense records with optional split-person tracking (existing)
- ✓ **Budget tracking** — Budget goals per category with progress visualization (existing)
- ✓ **SQLite persistence** — Local binary database storage (existing)
- ✓ **YAML data export layer** — Export all entities (accounts, categories, persons, records, templates) to human-readable YAML files — Phase 1
- ✓ **Git sync integration** — Auto-commit YAML changes to Git with descriptive messages — Phase 1
- ✓ **CLI query interface** — Query records, summaries, and spending via structured text commands — Phase 2
- ✓ **LLM context dump** — `bagels context` command for LLM-friendly financial snapshots — Phase 2
- ✓ **Data import/export commands** — Manual `bagels export` and `bagels import` for YAML sync — Phase 1
- ✓ **Dual-storage bidirectional sync** — SQLite ↔ YAML synchronization layer — Phase 1

### Active

- (None — all v1 milestone requirements addressed)

### Validated (Phase 5-7)

- ✓ **SQLite-only runtime** — Removed buggy Git/YAML sync; SQLite is sole runtime storage — Phase 5
- ✓ **LLM CLI documentation** — SKILL.md at repo root with full command reference and workflow patterns — Phase 6
- ✓ **Full CRUD CLI for all entities** — accounts, categories, persons, records, templates all have list/show/add/update/delete via CLI with --format/-f, --force, --cascade — Phase 7

### Out of Scope

- **Multi-user support** — Single-user application by design
- **Cloud sync service** — Git-based backup only, no centralized server
- **Web interface** — Planned for v3, not v1
- **LLM intelligence features** — Auto-categorization, smart comments, suggestions planned for v2
- **Real-time collaboration** — Git handles async merging, no real-time features

## Context

**Current State (from codebase map):**
- Python 3.13, Textual 1.0 TUI framework, SQLAlchemy 2.0 ORM
- Data stored in `~/.local/share/bagels/db.db` (binary SQLite, not Git-trackable)
- Models: Account, Category, Record, Split, Person, RecordTemplate
- Configuration in `~/.config/bagels/config.yaml`

**Evolution Goal:**
Transform from opaque binary database to transparent, version-controlled YAML files that enable:
1. **Git-based backup and sync** across devices
2. **Diffable financial history** with merge conflict resolution
3. **LLM-accessible data** via structured CLI query interface
4. **Offline-first workflow** with optional remote Git push

**Technical Constraints:**
- Must maintain backward compatibility with existing TUI interface
- SQLite remains runtime engine for performance
- YAML is canonical source of truth for Git tracking
- Bidirectional sync: YAML → SQLite on load, SQLite → YAML on save

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **YAML format for data** | Human-readable, diffable, Git-friendly, supports comments | ✓ Implemented in Phase 1 |
| **Monthly record grouping** | Keeps files manageable, natural expense boundary, aligns with budgets | ✓ Implemented in Phase 1 |
| **Slug-based IDs** (`r_2026-03-14_001`) | Stable, human-readable, mergeable, no UUID conflicts | ✓ Implemented in Phase 1 |
| **Last-write-wins conflict resolution** | Let Git handle merge conflicts naturally with markers | ✓ Implemented in Phase 1 |
| **SQLite as runtime engine** | Preserve TUI performance, YAML for Git tracking only | ✓ Architecture decision |
| **CLI as LLM interface** | Text-only, structured output, no interactive prompts in query mode | ✓ Implemented in Phase 2 |
| **Shared query infrastructure** | Centralized formatting/filtering for consistency across all commands | ✓ Implemented in Phase 2 |

---
*Last updated: 2026-03-23 after Phase 7 (Full CRUD CLI for all entities)*
