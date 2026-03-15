import logging
import threading

from sqlalchemy import select
from sqlalchemy.orm import joinedload, sessionmaker

from bagels.models.database.app import db_engine
from bagels.models.record_template import RecordTemplate

Session = sessionmaker(bind=db_engine)

logger = logging.getLogger(__name__)


def _trigger_entity_export() -> None:
    """Export templates YAML in a background daemon thread."""
    try:
        import bagels.config as config_mod

        if config_mod.CONFIG is None:
            return

        from bagels.export.exporter import export_templates
        from bagels.locations import data_directory
        from bagels.models.database.app import db_engine as _engine
        from sqlalchemy.orm import sessionmaker as _sessionmaker

        _Session = _sessionmaker(bind=_engine)
        session = _Session()
        try:
            filepath = export_templates(session, data_directory())
        finally:
            session.close()

        cfg = config_mod.CONFIG
        if not getattr(getattr(cfg, "git", None), "enabled", False):
            return
        if not getattr(cfg.git, "auto_commit", False):
            return

        from bagels.git.operations import auto_commit_yaml

        auto_commit_yaml(filepath, "chore(templates): sync templates yaml")
    except Exception:
        logger.exception("Auto-export hook failed for templates")


# region c
def create_template(data):
    session = Session()
    try:
        new_template = RecordTemplate(**data)
        session.add(new_template)
        session.commit()
        session.refresh(new_template)
        session.expunge(new_template)
        t = threading.Thread(target=_trigger_entity_export, daemon=True)
        t.start()
        return new_template
    finally:
        session.close()


def create_template_from_record(record):
    data = {}
    for x in ["label", "amount", "accountId", "categoryId", "isIncome"]:
        data[x] = record[x]

    return create_template(data)


# region r
def get_all_templates():
    session = Session()
    try:
        stmt = (
            select(RecordTemplate)
            .options(
                joinedload(RecordTemplate.category),
                joinedload(RecordTemplate.account),
            )
            .order_by(RecordTemplate.order)
        )
        return session.scalars(stmt).all()
    finally:
        session.close()


def get_record_templates():
    session = Session()
    try:
        stmt = (
            select(RecordTemplate)
            .options(
                joinedload(RecordTemplate.category),
                joinedload(RecordTemplate.account),
            )
            .filter(RecordTemplate.isTransfer == False)  # noqa: E712
            .order_by(RecordTemplate.order)
        )
        return session.scalars(stmt).all()
    finally:
        session.close()


def get_transfer_templates():
    session = Session()
    try:
        stmt = (
            select(RecordTemplate)
            .options(
                joinedload(RecordTemplate.category),
                joinedload(RecordTemplate.account),
            )
            .filter(RecordTemplate.isTransfer)
            .order_by(RecordTemplate.order)
        )
        return session.scalars(stmt).all()
    finally:
        session.close()


def get_template_by_id(recordtemplate_id) -> RecordTemplate:
    session = Session()
    try:
        select(RecordTemplate).options(
            joinedload(RecordTemplate.category),
            joinedload(RecordTemplate.account),
        )
        return session.get(
            RecordTemplate,
            recordtemplate_id,
            options=[
                joinedload(RecordTemplate.category),
                joinedload(RecordTemplate.account),
            ],
        )
    finally:
        session.close()


def get_adjacent_template(recordtemplate_id, direction):
    session = Session()
    try:
        recordtemplate = session.get(RecordTemplate, recordtemplate_id)
        if not recordtemplate:
            return -1

        current_order = recordtemplate.order
        if direction == "next":
            stmt = select(RecordTemplate).filter(
                RecordTemplate.order == current_order + 1
            )
        else:  # direction == "previous"
            stmt = select(RecordTemplate).filter(
                RecordTemplate.order == current_order - 1
            )

        adjacent_template = session.scalars(stmt).first()
        if adjacent_template:
            return adjacent_template.id
        return -1
    finally:
        session.close()


# region u
def update_template(recordtemplate_id, data):
    session = Session()
    try:
        recordtemplate = session.get(RecordTemplate, recordtemplate_id)
        if recordtemplate:
            for key, value in data.items():
                setattr(recordtemplate, key, value)
            session.commit()
            session.refresh(recordtemplate)
            session.expunge(recordtemplate)
            t = threading.Thread(target=_trigger_entity_export, daemon=True)
            t.start()
        return recordtemplate
    finally:
        session.close()


def swap_template_order(recordtemplate_id, direction="next"):
    session = Session()
    try:
        recordtemplate = session.get(RecordTemplate, recordtemplate_id)

        if recordtemplate:
            current_order = recordtemplate.order
            if direction == "next":
                stmt = select(RecordTemplate).filter(
                    RecordTemplate.order == current_order + 1
                )
            else:  # direction == "previous"
                stmt = select(RecordTemplate).filter(
                    RecordTemplate.order == current_order - 1
                )

            swap_template = session.scalars(stmt).first()
            if swap_template:
                # Use negative order values to avoid unique constraint violations
                recordtemplate.order = -current_order
                session.flush()

                swap_template.order = -swap_template.order
                session.flush()

                recordtemplate.order = -swap_template.order
                swap_template.order = current_order
                session.commit()
                session.refresh(recordtemplate)
                session.expunge(recordtemplate)
        return recordtemplate
    finally:
        session.close()


# region d
def delete_template(recordtemplate_id):
    session = Session()
    try:
        recordtemplate = session.get(RecordTemplate, recordtemplate_id)
        if recordtemplate:
            # Get all templates with higher order
            stmt = (
                select(RecordTemplate)
                .filter(RecordTemplate.order > recordtemplate.order)
                .order_by(RecordTemplate.order)
            )
            templates = session.scalars(stmt).all()

            # First update all orders to temporary negative values
            for i, template in enumerate(templates):
                template.order = -(i + 1)
            session.flush()

            # Delete the target template
            session.delete(recordtemplate)
            session.flush()

            # Then update to final values
            for i, template in enumerate(templates):
                template.order = recordtemplate.order + i

            session.commit()
            t = threading.Thread(target=_trigger_entity_export, daemon=True)
            t.start()
            return True
        return False
    finally:
        session.close()
