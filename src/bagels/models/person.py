from datetime import datetime
import re

from sqlalchemy import Column, DateTime, Integer, String, event, select
from sqlalchemy.orm import relationship

from .database.db import Base


class Person(Base):
    __tablename__ = "person"

    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    deletedAt = Column(DateTime, nullable=True)

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=True)
    name = Column(String)

    splits = relationship("Split", back_populates="person")


def _slugify_name(value: str | None) -> str:
    text = (value or "person").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "person"


@event.listens_for(Person, "before_insert")
def receive_before_insert(mapper, connection, target):
    if target.slug:
        return

    base_slug = f"person_{_slugify_name(target.name)}"
    slug = base_slug
    index = 2

    while connection.execute(select(Person.id).where(Person.slug == slug)).first():
        slug = f"{base_slug}_{index}"
        index += 1

    target.slug = slug
