from pathlib import Path
from typing import Optional
from xdg_base_dirs import xdg_config_home, xdg_data_home

# Store the custom root directory
_custom_root: Optional[Path] = None


def set_custom_root(path: Optional[str | Path]) -> None:
    """Set a custom root directory for all app files."""
    global _custom_root
    _custom_root = Path(path) if path else None


def _app_directory(root: Path) -> Path:
    """Create and return the application directory."""
    if _custom_root is not None:
        directory = _custom_root
    else:
        directory = root / "bagels"

    directory.mkdir(exist_ok=True, parents=True)
    return directory


def data_directory() -> Path:
    """Return (possibly creating) the application data directory."""
    return _app_directory(xdg_data_home())


def config_directory() -> Path:
    """Return (possibly creating) the application config directory."""
    return _app_directory(xdg_config_home())


def config_file() -> Path:
    return config_directory() / "config.yaml"


def database_file() -> Path:
    return data_directory() / "db.db"


def yaml_accounts_path() -> Path:
    """Return path to accounts YAML file."""
    return data_directory() / "accounts.yaml"


def yaml_categories_path() -> Path:
    """Return path to categories YAML file."""
    return data_directory() / "categories.yaml"


def yaml_persons_path() -> Path:
    """Return path to persons YAML file."""
    return data_directory() / "persons.yaml"


def yaml_templates_path() -> Path:
    """Return path to templates YAML file."""
    return data_directory() / "templates.yaml"


def yaml_records_directory() -> Path:
    """Return path to records directory (creates if needed)."""
    records_dir = data_directory() / "records"
    records_dir.mkdir(exist_ok=True, parents=True)
    return records_dir


def backups_directory() -> Path:
    """Return path to backups directory (creates if needed)."""
    backups_dir = data_directory() / "backups"
    backups_dir.mkdir(exist_ok=True, parents=True)
    return backups_dir
