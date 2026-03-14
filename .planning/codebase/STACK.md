# Technology Stack

**Analysis Date:** 2026-03-14

## Languages

**Primary:**
- Python 3.13 - Core application logic, CLI interface, data models

**Secondary:**
- N/A - Python is the only programming language used

## Runtime

**Environment:**
- Python 3.13+ (runtime requirement)

**Package Manager:**
- UV - Package dependency management and build system
- Lockfile: `uv.lock` present

## Frameworks

**Core:**
- Textual 1.0 - Terminal user interface (TUI) framework
- Click 8.0 - Command-line interface framework
- Rich 13.0 - Terminal formatting and console output

**Testing:**
- pytest 8.3.1 - Unit and integration testing
- pytest-cov 5.0.0 - Test coverage
- pytest-xdist 3.6.1 - Parallel test execution
- pytest-textual-snapshot 1.0.0 - TUI snapshot testing

**Build/Dev:**
- Hatchling - Build backend
- Ruff 0.9.1 - Code linting (select E, F)
- Pre-commit 4.0.1 - Git hooks
- Textual-dev 1.6.1 - TUI development tools

## Key Dependencies

**Critical:**
- SQLAlchemy 2.0 - Database ORM and SQLite integration
- Pydantic 2.0 - Data validation and configuration models
- Textual 1.0 - Terminal UI framework
- Click 8.0 - CLI framework

**Infrastructure:**
- YAML 6.0 - Configuration file format
- Rich 13.0 - Terminal formatting and progress bars
- Requests 2.0 - HTTP client for PyPI version checking
- SQLite3 - Local database storage

## Configuration

**Environment:**
- Local YAML configuration (`~/.config/bagels/config.yaml`)
- Environment variable validation through Pydantic
- Cross-platform config file detection and management

**Build:**
- `pyproject.toml` using hatchling build backend
- Package entry point: `bagels = "bagels.__main__:cli"`

## Platform Requirements

**Development:**
- Python 3.13+
- UV package manager
- Textual TUI development environment

**Production:**
- Python 3.13+ runtime
- SQLite-compatible filesystem (no external database required)
- Terminal environment with ANSI color support

---

*Stack analysis: 2026-03-14*
```