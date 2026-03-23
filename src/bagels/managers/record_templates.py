from sqlalchemy import select
from sqlalchemy.orm import joinedload, sessionmaker

from bagels.models.database.app import db_engine
from bagels.models.record_template import RecordTemplate

Session = sessionmaker(bind=db_engine)


# region c
def create_template(data):
    session = Session()
    try:
        new_template = RecordTemplate(**data)
        session.add(new_template)
        session.commit()
        stmt = (
            select(RecordTemplate)
            .options(
                joinedload(RecordTemplate.category),
                joinedload(RecordTemplate.account),
                joinedload(RecordTemplate.transferToAccount),
            )
            .where(RecordTemplate.id == new_template.id)
        )
        new_template = session.execute(stmt).unique().scalar_one()
        session.expunge(new_template)
        if new_template.account:
            session.expunge(new_template.account)
        if new_template.category:
            session.expunge(new_template.category)
        if new_template.transferToAccount:
            session.expunge(new_template.transferToAccount)
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
                joinedload(RecordTemplate.transferToAccount),
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
                joinedload(RecordTemplate.transferToAccount),
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
                joinedload(RecordTemplate.transferToAccount),
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
        return session.get(
            RecordTemplate,
            recordtemplate_id,
            options=[
                joinedload(RecordTemplate.category),
                joinedload(RecordTemplate.account),
                joinedload(RecordTemplate.transferToAccount),
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
            stmt = (
                select(RecordTemplate)
                .options(
                    joinedload(RecordTemplate.category),
                    joinedload(RecordTemplate.account),
                    joinedload(RecordTemplate.transferToAccount),
                )
                .where(RecordTemplate.id == recordtemplate_id)
            )
            recordtemplate = session.execute(stmt).unique().scalar_one()
            session.expunge(recordtemplate)
            if recordtemplate.account:
                session.expunge(recordtemplate.account)
            if recordtemplate.category:
                session.expunge(recordtemplate.category)
            if recordtemplate.transferToAccount:
                session.expunge(recordtemplate.transferToAccount)
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
            return True
        return False
    finally:
        session.close()
