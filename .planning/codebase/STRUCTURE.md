# Codebase Structure

**Analysis Date:** 2026-03-14

## Directory Layout

```
[project-root]/
├── src/bagels/               # Main application source
│   ├── __main__.py          # CLI entry point
│   ├── app.py               # Main Textual app
│   ├── config.py            # Configuration management
│   ├── constants.py         # Application constants
│   ├── locations.py         # File and directory utilities
│   ├── manager.py           # Manager page controller
│   ├── home.py              # Home page controller
│   ├── themes.py            # Theme definitions
│   ├── textualrun.py        # Textual runtime utilities
│   ├── versioning.py        # Version management
│   ├── bagel.py             # Core data models
│   ├── forms/               # Form definitions and validation
│   ├── components/           # UI components
│   │   ├── modules/         # Feature-specific modules
│   │   ├── tplot/           # Plotting components
│   │   └── *.py             # Core widgets
│   ├── managers/            # Business logic managers
│   ├── models/              # Data models and database schema
│   │   └── database/        # Database setup and migrations
│   ├── migrations/          # Data migration utilities
│   ├── modals/              # Modal dialog components
│   ├── static/              # Static data files
│   ├── styles/              # CSS/TSS styling files
│   └── utils/               # Utility functions
├── tests/                   # Test suites
├── public/                  # Public assets
├── .planning/codebase/      # Generated documentation
└── pyproject.toml          # Project configuration
```

## Directory Purposes

**src/bagels/:**
- Purpose: Main application source code
- Contains: Core application logic, configuration, entry points
- Key files: `app.py`, `home.py`, `manager.py`, `config.py`

**src/bagels/components/:**
- Purpose: User interface components and widgets
- Contains: Reusable UI components, modules, visual elements
- Key files: `[src/bagels/components/bagel.py]`, modules for features

**src/bagels/managers/:**
- Purpose: Business logic and data coordination
- Contains: Domain-specific logic classes
- Key files: `[src/bagels/managers/accounts.py]`, `[src/bagels/managers/categories.py]`

**src/bagels/models/:**
- Purpose: Data models and database schema
- Contains: SQLAlchemy models, data structures
- Key files: `[src/bagels/models/account.py]`, `[src/bagels/models/record.py]`

**src/bagels/forms/:**
- Purpose: Form definitions and user input validation
- Contains: Form classes, validation rules
- Key files: `[src/bagels/forms/record_forms.py]`, `[src/bagels/forms/category_form.py]`

**src/bagels/modals/:**
- Purpose: Modal dialog components
- Contains: User dialog implementations
- Key files: Various modal dialog classes

**src/bagels/static/:**
- Purpose: Static data and default configurations
- Contains: Default categories, sample data
- Key files: `default_categories.yaml`

**src/bagels/styles/:**
- Purpose: Application styling and themes
- Contains: CSS/TSS files for visual styling
- Key files: `index.tcss`, theme-specific files

**tests/:**
- Purpose: Test suites and fixtures
- Contains: Unit tests, integration tests, snapshots
- Key files: Various test modules under managers

## Key File Locations

**Entry Points:**
- `[src/bagels/__main__.py]`: CLI entry point and argument parsing
- `[src/bagels/app.py]`: Main Textual application controller

**Configuration:**
- `[src/bagels/config.py]`: Configuration management and validation
- `[src/bagels/locations.py]`: File and directory utilities

**Core Logic:**
- `[src/bagels/home.py]`: Primary user interface controller
- `[src/bagels/manager.py]`: Management interface controller

**Testing:**
- `[tests/](file:///Users/thepbordin/Developer/Bagels/tests/)`: Test suites for managers and components

## Naming Conventions

**Files:**
- Classes: PascalCase (e.g., `Home.py`, `Manager.py`)
- Utilities: lowercase (e.g., `utils/format.py`)
- Components: descriptive names (e.g., `barchart.py`)

**Functions:**
- Public functions: snake_case (e.g., `load_config()`)
- Private functions: underscore prefix (e.g., `_create_default_categories()`)

**Variables:**
- Instance variables: snake_case (e.g., `filter`, `offset`)
- Constants: UPPER_SNAKE_CASE (e.g., `PAGES`)

**Types:**
- Classes: PascalCase (e.g., `Config`, `Account`)
- Methods: snake_case (e.g., `on_mount()`, `action_inc_offset()`)

## Where to Add New Code

**New Feature Module:**
- Primary code: `src/bagels/components/modules/`
- Tests: `tests/managers/`
- Styling: `src/bagels/styles/`

**New Data Model:**
- Model: `src/bagels/models/`
- Database: `src/bagels/models/database/`
- Manager: `src/bagels/managers/`

**New Form:**
- Form: `src/bagels/forms/`
- Validation: Built into form classes using Pydantic

**New Component:**
- Component: `src/bagels/components/`
- Dependencies: Import in specific modules only

## Special Directories

**src/bagels/components/tplot/:**
- Purpose: Custom plotting components using plotext
- Generated: No
- Committed: Yes - custom plotting implementations

**src/bagels/static/:**
- Purpose: Static data files and defaults
- Generated: No
- Committed: Yes - contains default categories and configuration

**tests/__snapshots__:**
- Purpose: Test snapshots for visual regression
- Generated: Yes - by pytest-textual-snapshot
- Committed: Yes - version-controlled test results

---

*Structure analysis: 2026-03-14*