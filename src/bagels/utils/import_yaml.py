"""
Backward-compatible YAML import utilities.

Historically these helpers accepted unwrapped entity maps and returned a single
processed count. New importer functions use wrapped payloads and return
(imported_count, updated_count). This module bridges both interfaces.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sqlite3

from sqlalchemy.orm import Session

from bagels.importer.importer import (
    create_backup as _create_backup,
    import_accounts_from_yaml as _import_accounts_from_yaml,
    import_categories_from_yaml as _import_categories_from_yaml,
    import_persons_from_yaml as _import_persons_from_yaml,
    import_records_from_yaml as _import_records_from_yaml,
    import_templates_from_yaml as _import_templates_from_yaml,
)


def _wrap_entity_data(yaml_data: dict, entity_key: str) -> dict:
    if not isinstance(yaml_data, dict):
        return {entity_key: {}}
    if entity_key in yaml_data:
        return yaml_data
    return {entity_key: yaml_data}


def _create_session_backup(
    session: Session, backup_dir: str | None = None
) -> Path | None:
    if not backup_dir:
        return None

    backup_root = Path(backup_dir)
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_path = (
        backup_root / f"backup_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.db"
    )

    try:
        dbapi_conn = session.connection().connection
        if hasattr(dbapi_conn, "dbapi_connection"):
            dbapi_conn = dbapi_conn.dbapi_connection

        dest = sqlite3.connect(backup_path)
        try:
            dbapi_conn.backup(dest)
        finally:
            dest.close()
        return backup_path
    except Exception:
        # Fallback: best-effort default backup behavior
        try:
            return _create_backup()
        except Exception:
            return None


def create_backup() -> Path:
    return _create_backup()


def import_accounts_from_yaml(
    yaml_data: dict, session: Session, backup_dir: str | None = None
) -> int:
    _create_session_backup(session, backup_dir)
    imported, updated = _import_accounts_from_yaml(
        _wrap_entity_data(yaml_data, "accounts"), session
    )
    return imported + updated


def import_categories_from_yaml(
    yaml_data: dict, session: Session, backup_dir: str | None = None
) -> int:
    _create_session_backup(session, backup_dir)
    imported, updated = _import_categories_from_yaml(
        _wrap_entity_data(yaml_data, "categories"), session
    )
    return imported + updated


def import_records_from_yaml(
    yaml_data: dict, session: Session, backup_dir: str | None = None
) -> int:
    _create_session_backup(session, backup_dir)
    imported, updated = _import_records_from_yaml(
        _wrap_entity_data(yaml_data, "records"), session
    )
    return imported + updated


def import_persons_from_yaml(
    yaml_data: dict, session: Session, backup_dir: str | None = None
) -> int:
    _create_session_backup(session, backup_dir)
    imported, updated = _import_persons_from_yaml(
        _wrap_entity_data(yaml_data, "persons"), session
    )
    return imported + updated


def import_templates_from_yaml(
    yaml_data: dict, session: Session, backup_dir: str | None = None
) -> int:
    _create_session_backup(session, backup_dir)
    imported, updated = _import_templates_from_yaml(
        _wrap_entity_data(yaml_data, "templates"), session
    )
    return imported + updated


__all__ = [
    "create_backup",
    "import_accounts_from_yaml",
    "import_categories_from_yaml",
    "import_records_from_yaml",
    "import_persons_from_yaml",
    "import_templates_from_yaml",
]
