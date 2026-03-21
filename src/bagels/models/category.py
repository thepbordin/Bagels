from datetime import datetime
from enum import Enum
import re

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    event,
    select,
)
from sqlalchemy.orm import relationship, validates

from .database.db import Base


class Nature(Enum):
    WANT = "Want"
    NEED = "Need"
    MUST = "Must"

    def __str__(self):
        return self.value


class Category(Base):
    __tablename__ = "category"

    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    deletedAt = Column(DateTime, nullable=True)

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=True)
    parentCategoryId = Column(Integer, ForeignKey("category.id"), nullable=True)
    name = Column(String, nullable=False)
    nature = Column(SQLEnum(Nature), nullable=False)
    color = Column(String, nullable=False, default="#808080")

    records = relationship("Record", back_populates="category")
    parentCategory = relationship(
        "Category", back_populates="subCategories", remote_side=[id]
    )
    subCategories = relationship(
        "Category", back_populates="parentCategory", remote_side=[parentCategoryId]
    )

    @validates("nature")
    def validate_nature(self, key, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            mapping = {
                "expense": Nature.NEED,
                "income": Nature.WANT,
                "need": Nature.NEED,
                "want": Nature.WANT,
                "must": Nature.MUST,
            }
            return mapping.get(normalized, Nature.NEED)
        return value

    @validates("color")
    def validate_color(self, key, value):
        return value or "#808080"


def _slugify_name(value: str | None) -> str:
    text = (value or "category").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "category"


@event.listens_for(Category, "before_insert")
def receive_before_insert(mapper, connection, target):
    if target.slug:
        return

    base_slug = f"cat_{_slugify_name(target.name)}"
    slug = base_slug
    index = 2

    while connection.execute(select(Category.id).where(Category.slug == slug)).first():
        slug = f"{base_slug}_{index}"
        index += 1

    target.slug = slug
