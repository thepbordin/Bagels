# Architecture

**Analysis Date:** 2026-03-14

## Pattern Overview

**Overall:** Textual TUI (Terminal User Interface) Application with MVC-like Architecture

**Key Characteristics:**
- Textual-based terminal UI framework
- MVC-style separation with Models, Views (Components), Controllers (Home/Manager)
- SQLite database with SQLAlchemy ORM
- Configuration-driven behavior with YAML config files
- Modular component-based UI architecture

## Layers

**Presentation Layer (Components):**
- Purpose: UI components and user interface
- Location: `src/bagels/components/`
- Contains: Widget classes, UI modules, visual components
- Depends on: Textual framework, app configuration
- Used by: Home and Manager pages

**Application Logic Layer (Controllers/Pages):**
- Purpose: Main page controllers and application flow
- Location: `src/bagels/home.py`, `src/bagels/manager.py`, `src/bagels/app.py`
- Contains: Page logic, user interaction handlers, workflow orchestration
- Depends on: Components, Managers, Configuration
- Used by: Main App class

**Business Logic Layer (Managers):**
- Purpose: Business logic and data coordination
- Location: `src/bagels/managers/`
- Contains: Business rules, data processing, application-specific logic
- Depends on: Models, Database
- Used by: Home, Manager, and Components

**Data Layer (Models):**
- Purpose: Data models and database schema
- Location: `src/bagels/models/`
- Contains: SQLAlchemy models, data structures, validation
- Depends on: Database engine
- Used by: Managers, Controllers

**Persistence Layer (Database):**
- Purpose: Data persistence and storage
- Location: `src/bagels/models/database/`
- Contains: Database setup, migrations, session management
- Depends on: SQLite, SQLAlchemy
- Used by: Models

## Data Flow

**Application Startup:**
1. CLI entry point in `__main__.py` loads configuration
2. Initializes database through `init_db()`
3. Creates main `App` instance and runs it

**User Interaction Flow:**
1. User interacts with UI components
2. Components trigger actions in Home/Manager controllers
3. Controllers call business logic through Managers
4. Managers interact with Models for data operations
5. Models handle database persistence
6. Results flow back to update UI components

**Configuration Flow:**
1. Configuration loaded from YAML file in `config.py`
2. Applied globally via CONFIG singleton
3. Components and controllers access configuration via CONFIG object
4. Runtime state changes written back to YAML

## Key Abstractions

**App Abstraction:**
- Purpose: Main application controller and Textual app base
- Examples: `[src/bagels/app.py]`
- Pattern: Singleton pattern with reactive properties

**Page Abstractions:**
- Home Page: Primary data display and interaction
- Manager Page: Configuration and management interface
- Pattern: Composition of modular components

**Manager Pattern:**
- Purpose: Business logic coordination
- Examples: `[src/bagels/managers/accounts.py]`, `[src/bagels/managers/categories.py]`
- Pattern: Separate manager classes for different domains

**Component Pattern:**
- Purpose: Reusable UI widgets and modules
- Examples: `[src/bagels/components/modules/records.py]`, `[src/bagels/components/barchart.py]`
- Pattern: Textual widget composition

## Entry Points

**Main Entry Point:**
- Location: `[src/bagels/__main__.py]`
- Triggers: CLI commands, application startup
- Responsibilities: Argument parsing, configuration loading, database initialization, app creation

**App Entry Point:**
- Location: `[src/bagels/app.py]`
- Triggers: Application lifecycle management
- Responsibilities: Textual app setup, theme management, command palette, page navigation

**Home Entry Point:**
- Location: `[src/bagels/home.py]`
- Triggers: Primary user interface interaction
- Responsibilities: Records display, filtering, account management

**Manager Entry Point:**
- Location: `[src/bagels/manager.py]`
- Triggers: Configuration and management tasks
- Responsibilities: Budget management, categories, people, spending insights

## Error Handling

**Strategy:** Layered error handling with graceful degradation

**Patterns:**
- Configuration validation with helpful error messages
- Database error handling and fallbacks
- Component-level error states and user feedback
- Global exception handling for critical failures

## Cross-Cutting Concerns

**Logging:** Textual framework logging with conditional output
**Validation:** Pydantic models for configuration, SQLAlchemy for data constraints
**Authentication:** Not applicable - single-user application
**Theme Management:** CSS-based theming with runtime switching

---

*Architecture analysis: 2026-03-14*