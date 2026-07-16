from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    event,
    text,
)
from sqlalchemy.orm import relationship, validates

import bagels.config as _config

from .database.db import Base


class Record(Base):
    __tablename__ = "record"

    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=True)
    label = Column(String, nullable=False)
    amount = Column(Float, CheckConstraint("amount > 0"), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.now)
    accountId = Column(Integer, ForeignKey("account.id"), nullable=False)
    categoryId = Column(Integer, ForeignKey("category.id"), nullable=True)
    personId = Column(Integer, ForeignKey("person.id"), nullable=True)

    tags = Column(String, nullable=True)  # unimplemented
    isInProgress = Column(Boolean, nullable=False, default=False)  # unimplemented

    # if record adds money to account
    isIncome = Column(Boolean, nullable=False, default=False)
    # if record is transfer to this account
    isTransfer = Column(
        Boolean,
        CheckConstraint("(isTransfer = FALSE) OR (isIncome = FALSE)"),
        nullable=False,
        default=False,
    )
    transferToAccountId = Column(Integer, ForeignKey("account.id"), nullable=True)

    account = relationship(
        "Account", foreign_keys=[accountId], back_populates="records"
    )
    category = relationship("Category", back_populates="records")
    person = relationship("Person")
    transferToAccount = relationship(
        "Account",
        foreign_keys=[transferToAccountId],
        back_populates="transferFromRecords",
    )
    splits = relationship(
        "Split", back_populates="record", cascade="all, delete-orphan"
    )

    @validates("amount")
    def validate_amount(self, key, value):
        if value is not None:
            return round(value, _config.CONFIG.defaults.round_decimals)
        return value


@event.listens_for(Record, "before_insert")
def _record_before_insert(mapper, connection, target):
    """Auto-generate slug for records created via any path (TUI, CLI, batch)."""
    if target.slug:
        return

    # Determine the record date
    record_date = target.date
    if record_date is None:
        record_date = datetime.now()
    if isinstance(record_date, datetime):
        record_date = record_date.date()

    date_str = record_date.strftime("%Y-%m-%d")
    prefix = f"r_{date_str}_"

    # Find next sequence for this date by querying committed records in the DB.
    result = connection.execute(
        text("SELECT slug FROM record WHERE slug LIKE :prefix"),
        {"prefix": f"{prefix}%"},
    )
    sequences = []
    for row in result:
        slug_val = row[0]
        if slug_val:
            try:
                seq = int(slug_val.split("_")[-1])
                sequences.append(seq)
            except (ValueError, IndexError):
                pass

    # Also check slugs already assigned to other pending objects in the same
    # session flush — they are not yet in the DB so the SQL above won't find them.
    session = target._sa_instance_state.session
    if session is not None:
        for pending in session.new:
            if pending is target:
                continue
            if (
                isinstance(pending, Record)
                and pending.slug
                and pending.slug.startswith(prefix)
            ):
                try:
                    seq = int(pending.slug.split("_")[-1])
                    sequences.append(seq)
                except (ValueError, IndexError):
                    pass

    next_seq = max(sequences) + 1 if sequences else 1
    target.slug = f"r_{date_str}_{next_seq:03d}"
