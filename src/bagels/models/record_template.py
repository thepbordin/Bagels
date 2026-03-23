from datetime import datetime
import re

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
    func,
    select,
)
from sqlalchemy.orm import relationship, synonym, validates

import bagels.config as _config

from .database.db import Base


class RecordTemplate(Base):
    __tablename__ = "record_template"

    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=True)
    label = Column(String, nullable=False)
    amount = Column(Float, CheckConstraint("amount > 0"), nullable=False)
    accountId = Column(Integer, ForeignKey("account.id"), nullable=False)
    categoryId = Column(Integer, ForeignKey("category.id"), nullable=True)

    order = Column(Integer, nullable=False, unique=True)
    ordinal = synonym("order")

    isIncome = Column(Boolean, nullable=False, default=False)
    isTransfer = Column(
        Boolean,
        CheckConstraint("(isTransfer = FALSE) OR (isIncome = FALSE)"),
        nullable=False,
        default=False,
    )
    transferToAccountId = Column(Integer, ForeignKey("account.id"), nullable=True)

    account = relationship("Account", foreign_keys=[accountId])
    category = relationship("Category", foreign_keys=[categoryId])
    transferToAccount = relationship("Account", foreign_keys=[transferToAccountId])

    def to_dict(self) -> dict:
        """Creates a dictionary object to feed into create_record."""
        return {
            "label": self.label,
            "amount": self.amount,
            "accountId": self.accountId,
            "categoryId": self.categoryId,
            "isIncome": self.isIncome,
            "isTransfer": self.isTransfer,
            "transferToAccountId": self.transferToAccountId,
        }

    @validates("order")
    def validate_order(self, key, order):
        if order is None:
            raise ValueError("Order cannot be null.")
        return order

    @validates("amount")
    def validate_amount(self, key, value):
        if value is not None:
            return round(value, _config.CONFIG.defaults.round_decimals)
        return value


@event.listens_for(RecordTemplate, "before_insert")
def receive_before_insert(mapper, connection, target):
    if target.order is None:
        counter_key = "record_template_order_counter"
        next_order = connection.info.get(counter_key)
        if next_order is None:
            max_order = connection.execute(
                select(func.max(RecordTemplate.order))
            ).scalar_one_or_none()
            next_order = max_order or 0
        next_order += 1
        connection.info[counter_key] = next_order
        target.order = next_order
    if target.slug:
        return

    label = (target.label or "template").strip().lower()
    label = re.sub(r"[^a-z0-9]+", "_", label).strip("_") or "template"
    base_slug = f"tpl_{label}"
    slug = base_slug
    index = 2

    while connection.execute(
        select(RecordTemplate.id).where(RecordTemplate.slug == slug)
    ).first():
        slug = f"{base_slug}_{index}"
        index += 1

    target.slug = slug
