from datetime import datetime
import re

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, event, select
from sqlalchemy.orm import relationship

from .database.db import Base


class Account(Base):
    __tablename__ = "account"

    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    deletedAt = Column(DateTime, nullable=True)

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=False)
    description = Column(String)
    beginningBalance = Column(Float, nullable=False)
    repaymentDate = Column(Integer)

    hidden = Column(Boolean, nullable=False, default=False)

    records = relationship(
        "Record", back_populates="account", foreign_keys="[Record.accountId]"
    )
    transferFromRecords = relationship(
        "Record",
        back_populates="transferToAccount",
        foreign_keys="[Record.transferToAccountId]",
    )
    splits = relationship("Split", back_populates="account")


def _slugify_name(value: str | None) -> str:
    text = (value or "account").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "account"


@event.listens_for(Account, "before_insert")
def receive_before_insert(mapper, connection, target):
    if target.slug:
        return

    base_slug = f"acc_{_slugify_name(target.name)}"
    slug = base_slug
    index = 2

    while connection.execute(select(Account.id).where(Account.slug == slug)).first():
        slug = f"{base_slug}_{index}"
        index += 1

    target.slug = slug
