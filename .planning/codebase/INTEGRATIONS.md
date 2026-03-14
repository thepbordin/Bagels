# External Integrations

**Analysis Date:** 2026-03-14

## APIs & External Services

**Version Management:**
- PyPI (Python Package Index) - Version checking and updates
  - SDK/Client: `requests` library
  - Endpoint: `https://pypi.org/pypi/bagels/json`
  - Purpose: Automatic version checking and update notifications

**Data Import:**
- Actual Budget (import functionality)
  - SDK/Client: `sqlite3` for database reading
  - Purpose: Migration from Actual Budget SQLite databases
  - Endpoint: Local SQLite file reading

## Data Storage

**Databases:**
- SQLite - Local database storage
  - Connection: Local file-based database
  - Client: SQLAlchemy 2.0 ORM
  - Location: `~/.config/bagels/bagels.db`

**File Storage:**
- Local filesystem - Configuration and data files
- YAML format for configuration and default categories

**Caching:**
- None detected - No external caching services

## Authentication & Identity

**Auth Provider:**
- Custom implementation - No external authentication
  - Implementation: Local file-based configuration

## Monitoring & Observability

**Error Tracking:**
- None detected - No external error tracking service

**Logs:**
- Local console output via Rich library
- No external logging services

## CI/CD & Deployment

**Hosting:**
- GitHub - Code repository (primary hosting)
- GitHub Pages - Documentation

**CI Pipeline:**
- GitHub Actions - Automated testing and deployment
- Pre-commit hooks - Code quality enforcement

## Environment Configuration

**Required env vars:**
- None required - All configuration through local files

**Secrets location:**
- No external secrets required
- Configuration stored in local YAML files

## Webhooks & Callbacks

**Incoming:**
- None detected - No webhook endpoints

**Outgoing:**
- HTTP requests to PyPI - Version checking
- No other outgoing API calls detected

## Migration Support

**Supported Import Formats:**
- Actual Budget SQLite databases
  - Implementation: Migration script in `src/bagels/migrations/`
  - Features: Category and record import functionality

---

*Integration audit: 2026-03-14*
```