# Testing Patterns

**Analysis Date:** 2026-03-14

## Test Framework

**Runner:** pytest 8.3.1+
**Config:** `pyproject.toml`
**Assertion Library:** pytest built-in assertions

**Test Dependencies:**
```toml
[tool.uv.dev-dependencies]
    "pytest>=8.3.1",
    "syrupy>=4.6.1",        # For snapshot testing
    "pytest-xdist>=3.6.1",   # For parallel test execution
    "pytest-cov>=5.0.0",     # For coverage
    "pytest-textual-snapshot==1.0.0",  # For TUI snapshot testing
    "time-machine==2.16.0", # For time mocking
```

**Run Commands:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run tests in parallel
pytest -n auto

# Run specific test file
pytest tests/managers/test_utils.py

# Run with verbose output
pytest -v

# Run with snapshots
pytest
```

## Test File Organization

**Location:** `tests/`
- `tests/managers/` - Unit tests for business logic
- `tests/snapshot.py` - UI/integration tests
- `tests/__snapshots__/` - Generated snapshot files

**Naming Pattern:**
- Manager tests: `tests/managers/test_[module].py`
- Snapshot tests: `tests/snapshot.py`
- Snapshot files: `tests/__snapshots__/snapshot/[TestName].[test_name].svg`

**Structure:**
```
tests/
├── managers/
│   ├── test_utils.py
│   ├── test_account_balance.py
│   ├── test_record_template.py
│   ├── test_person.py
│   ├── test_category.py
│   ├── test_account.py
│   └── ...
├── snapshot.py
└── __snapshots__/
    └── snapshot/
        ├── TestAccounts.test_5_acc_screen.svg
        ├── TestTemplates.test_15_edit_template.svg
        └── ...
```

## Test Structure

**Unit Tests (Manager Tests):**
```python
@pytest.fixture(scope="function")
def engine():
    """Create a test-specific database engine."""
    return create_engine("sqlite:///:memory:")

@pytest.fixture(scope="function")
def setup_test_database(engine):
    """Create all tables in the test database."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def session(engine, setup_test_database):
    """Create a new session for a test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def test_data(session):
    """Create test accounts, categories, and people."""
    # Create test data
    account1 = Account(name="Account 1", beginningBalance=1000.0)
    account2 = Account(name="Account 2", beginningBalance=500.0)
    session.add_all([account1, account2])
    session.commit()

    return {
        "account1": account1,
        "account2": account2,
        # ... other test data
    }

def test_get_start_end_of_year():
    """Test year period calculations."""
    start, end = utils._get_start_end_of_year(0)
    assert start == datetime(2024, 1, 1, 0, 0, 0)
    assert end == datetime(2024, 12, 31, 23, 59, 59)
```

**Snapshot Tests:**
```python
class TestBasic:
    def test_1_welcome(self, snap_compare):
        assert snap_compare(App(**APP_PARAMS), terminal_size=SIZE_BASIC)

    def test_2_new_acc_welcome(self, snap_compare):
        async def r(pilot: Pilot):
            await pilot.press("a")  # add
            await pilot.press("t", "tab")  # name
            await pilot.press(*"123.45", "enter")  # value

        assert snap_compare(App(**APP_PARAMS), terminal_size=SIZE_BASIC, run_before=r)
```

## Mocking

**Time Mocking:** `time_machine` and `freezegun`
```python
import time_machine
from freezegun import freeze_time

@freeze_time("2024-02-15")
def test_get_start_end_of_month():
    """Test month period calculations."""
    start, end = utils._get_start_end_of_month(0)
    assert start == datetime(2024, 2, 1, 0, 0, 0)
    assert end == datetime(2024, 2, 29, 23, 59, 59)
```

**Database Mocking:** In-memory SQLite
```python
@pytest.fixture(scope="function")
def test_db():
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")

    # Create all tables
    Base.metadata.create_all(engine)

    # Create a new session factory bound to the engine
    accounts.Session = sessionmaker(bind=engine)

    yield engine

    # Clean up
    Base.metadata.drop_all(engine)
```

## Fixtures and Factories

**Database Fixtures:**
- `engine` - Test database engine
- `setup_test_database` - Table creation/cleanup
- `session` - Database session
- `test_data` - Pre-populated test entities

**Configuration Fixtures:**
- `CONFIG` - Global configuration object
- Custom root path for testing

**Snapshot Fixtures:**
- `snap_compare` - Snapshot comparison fixture
- `travel_to_hill_valley_time` - Time travel fixture

**Test Data Patterns:**
```python
def test_create_account(test_db):
    # Test data
    account_data = {
        "name": "Test Account",
        "description": "Test Description",
        "beginningBalance": 1000.0,
        "repaymentDate": 15,
        "hidden": False
    }

    # Create account
    new_account = accounts.create_account(account_data)

    # Assertions
    assert new_account is not None
    assert new_account.name == "Test Account"
    assert new_account.description == "Test Description"
    # ... more assertions
```

## Coverage

**Requirements:** Configured but no specific target enforced

**Coverage Configuration:**
```toml
[tool.coverage.run]
relative_files = true
```

**View Coverage:**
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html
```

## Test Types

**Unit Tests:**
- Location: `tests/managers/`
- Focus: Business logic, calculations, data manipulation
- Database: In-memory SQLite
- Time: Frozen to specific dates

**Integration Tests:**
- Location: `tests/snapshot.py`
- Focus: UI interactions, user workflows
- Framework: `pytest-textual-snapshot`
- Time: Travelled to consistent test time

**Database Tests:**
- SQLAlchemy model operations
- CRUD operations
- Relationship handling

**Async Tests:**
- Textual app interactions
- Async pilot controls

## Common Patterns

**Test Naming:**
```python
def test_[subject]_[scenario]():
    """Test description."""
```

**Async Testing:**
```python
async def r(pilot: Pilot):
    await pilot.press("a")  # add
    await pilot.press("t", "tab")  # name
    await pilot.press(*"123.45", "enter")  # value

assert snap_compare(App(**APP_PARAMS), terminal_size=SIZE_BASIC, run_before=r)
```

**Error Testing:**
```python
def test_invalid_configuration():
    with pytest.raises(ConfigurationError):
        # Invalid configuration that should raise error
        Config(invalid_field="invalid_value")
```

**Database Testing:**
```python
def test_get_all_accounts(test_db):
    # Create test data
    account_data1 = {"name": "Account 1", "beginningBalance": 1000.0}
    account_data2 = {"name": "Account 2", "beginningBalance": 500.0}

    # Create accounts
    accounts.create_account(account_data1)
    accounts.create_account(account_data2)

    # Test function
    all_accounts = accounts.get_all_accounts()

    # Assertions
    assert len(all_accounts) == 2
    assert all_accounts[0].name == "Account 1"
    assert all_accounts[1].name == "Account 2"
```

**Snapshot Testing:**
```python
def test_accounts_screen(snap_compare):
    assert snap_compare(
        App(**APP_PARAMS),
        terminal_size=SIZE_TEST,
        press=["a"],  # Press 'a' to show accounts
    )
```

---

*Testing analysis: 2026-03-14*