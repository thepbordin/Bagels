# Coding Conventions

**Analysis Date:** 2026-03-14

## Language

**Primary Language:** Python 3.13

**Package Manager:** UV (modern Python package manager)

## Project Structure

**Main Source Directory:** `src/bagels/`

**Test Directory:** `tests/`

**Configuration Files:**
- `pyproject.toml` - Project configuration and dependencies
- `.pre-commit-config.yaml` - Code quality hooks
- `.env` files (not analyzed - contains secrets)

## Naming Patterns

**Classes:** PascalCase
```python
class Home(Static):
    pass

class Account(Base):
    pass

class Config(BaseModel):
    pass
```

**Functions & Methods:** snake_case
```python
def load_config():
    pass

def get_start_end_of_period():
    pass

def create_account():
    pass
```

**Variables & Attributes:** snake_case
```python
first_day_of_week = 6
default_theme = "tokyo-night"
beginningBalance = 1000.0
```

**Constants:** UPPER_SNAKE_CASE (limited use in codebase)

**Files & Modules:** snake_case
```python
account.py
home.py
test_utils.py
```

## Code Style

**Formatter:** Ruff (configured in `pyproject.toml`)
```toml
[tool.ruff.lint]
select = ["E", "F"]
ignore = ["E402", "E501"]
exclude = ["**/tests/**"]
```

**Pre-commit Hooks:**
- Ruff linter with auto-fix
- Ruff formatter
- Conventional commit message validation

**Line Length:** Not strictly enforced (E501 ignored)

**Imports:**
- Standard library imports first
- Third-party imports second
- Local imports third
- Grouped logically

**Type Hints:**
- Extensively used throughout the codebase
- `from typing import Any, Literal`
- Uses Pydantic for data validation and configuration

## Import Organization

**Order:**
1. Standard library imports
2. Third-party imports
3. Local imports

**Path Structure:**
```python
from bagels.config import CONFIG
from bagels.models.account import Account
from bagels.managers import utils
```

**No relative imports** - all imports use absolute paths from project root

## Error Handling

**Exception Patterns:**
```python
try:
    CONFIG = Config()
except ValidationError as e:
    error_messages = []
    for error in e.errors():
        field = error["loc"]
        field_path = ".".join(str(x) for x in field)
        error_messages.append(f"Invalid configuration in field '{field_path}'")
    raise ConfigurationError("\n\n".join(error_messages))
```

**Custom Exceptions:**
```python
class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass
```

## Configuration Management

**Pydantic Models:** Used for configuration validation
```python
class Defaults(BaseModel):
    period: Literal["day", "week", "month", "year"] = "week"
    first_day_of_week: int = Field(ge=0, le=6, default=6)

class Config(BaseModel):
    hotkeys: Hotkeys = Hotkeys()
    symbols: Symbols = Symbols()
    defaults: Defaults = Defaults()
    state: State = State()
```

## Database Models

**SQLAlchemy Models:**
- Uses declarative base pattern
- Automatic timestamp fields (`createdAt`, `updatedAt`, `deletedAt`)
- Relationships defined explicitly

```python
class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    beginningBalance = Column(Float, nullable=False)
    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    updatedAt = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
```

## Function Design

**Parameters:**
- Named parameters with type hints
- Optional parameters with defaults
- Consistent parameter ordering

**Return Values:**
- Explicit return types
- Consistent return patterns
- `None` for void functions when appropriate

## Comments

**Docstrings:**
- Used for functions and classes
- Brief but descriptive
- Shows patterns in complex logic

**Inline Comments:**
- Used sparingly
- Explains "why" not "what"
- Clear and concise

## Testing Conventions

**Test Location:** `tests/managers/` and `tests/snapshot.py`

**Test Naming:** `test_[description].py`

**Function Naming:** `test_[scenario]()`

**Fixtures:** Extensively used for test setup

## Special Patterns

**Configuration Merging:** Default configuration merged with user configuration

**Time Travel:** Uses `time_machine` for consistent test timing

**Snapshot Testing:** Uses `pytest-textual-snapshot` for UI testing

---

*Convention analysis: 2026-03-14*