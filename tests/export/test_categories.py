"""
Tests for category export to YAML format (TDD - RED phase).

These tests define the expected behavior for exporting Category entities
from SQLite to human-readable YAML files with recursive parent-child structure.
"""

import pytest
from pathlib import Path
import yaml

from bagels.models.category import Category, Nature


class TestCategoryExport:
    """Test suite for category export functionality."""

    def test_export_single_category_without_parent(self, in_memory_db, temp_directory):
        """
        Test exporting a single category without parent to YAML.

        Given: Category(name="Groceries", parent=None)
        When: export_category_to_yaml(category, temp_dir)
        Then: YAML contains category with slug key
        And: parent field is null
        """
        # Arrange
        category = Category(
            name="Groceries", parentCategoryId=None, nature=Nature.NEED, color="#FF5733"
        )
        in_memory_db.add(category)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_category_to_yaml

        result_path = export_category_to_yaml(category, temp_directory)

        # Verify file exists
        assert result_path == temp_directory / "categories.yaml"
        assert result_path.exists()

        # Verify YAML structure
        with open(result_path, "r") as f:
            data = yaml.safe_load(f)

        assert "categories" in data
        assert len(data["categories"]) == 1

        # Category should be keyed by slug
        category_slug = category.slug
        assert category_slug in data["categories"]

        exported_category = data["categories"][category_slug]
        assert exported_category["name"] == "Groceries"
        assert exported_category["parentSlug"] is None
        assert exported_category["nature"] == "Need"
        assert exported_category["color"] == "#FF5733"

    def test_export_category_with_parent_child_relationship(
        self, in_memory_db, temp_directory
    ):
        """
        Test exporting categories with parent-child relationship.

        Given: Parent category "Food" with child "Groceries"
        When: export_categories_to_yaml(session, temp_dir)
        Then: YAML contains both categories
        And: Child category has parentSlug reference
        And: Structure preserves hierarchy
        """
        # Arrange
        parent = Category(
            name="Food", parentCategoryId=None, nature=Nature.NEED, color="#FF5733"
        )
        in_memory_db.add(parent)
        in_memory_db.flush()  # Get parent ID

        child = Category(
            name="Groceries",
            parentCategoryId=parent.id,
            nature=Nature.NEED,
            color="#FF5733",
        )
        in_memory_db.add(child)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_categories_to_yaml

        result_path = export_categories_to_yaml(in_memory_db, temp_directory)

        # Verify file exists
        assert result_path.exists()

        # Verify YAML structure
        with open(result_path, "r") as f:
            data = yaml.safe_load(f)

        assert "categories" in data
        assert len(data["categories"]) == 2

        # Verify parent has no parentSlug
        assert data["categories"][parent.slug]["parentSlug"] is None

        # Verify child has parentSlug reference
        assert data["categories"][child.slug]["parentSlug"] == parent.slug
        # No integer IDs
        assert "parentCategoryId" not in data["categories"][child.slug]
        assert "id" not in data["categories"][child.slug]

    def test_export_nested_category_tree(self, in_memory_db, temp_directory):
        """
        Test exporting 3-level category hierarchy.

        Given: 3-level hierarchy: Expenses → Food → Groceries
        When: Exported to YAML
        Then: All 3 levels exported
        And: parentSlug references use slugs (not IDs)
        And: Structure allows reconstruction of tree
        """
        # Arrange
        level1 = Category(
            name="Expenses", parentCategoryId=None, nature=Nature.NEED, color="#FF0000"
        )
        in_memory_db.add(level1)
        in_memory_db.flush()

        level2 = Category(
            name="Food", parentCategoryId=level1.id, nature=Nature.NEED, color="#FF5733"
        )
        in_memory_db.add(level2)
        in_memory_db.flush()

        level3 = Category(
            name="Groceries",
            parentCategoryId=level2.id,
            nature=Nature.NEED,
            color="#FF5733",
        )
        in_memory_db.add(level3)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_categories_to_yaml

        result_path = export_categories_to_yaml(in_memory_db, temp_directory)

        # Verify all levels present
        with open(result_path, "r") as f:
            data = yaml.safe_load(f)

        assert len(data["categories"]) == 3

        # Verify hierarchy via parentSlug
        assert data["categories"][level1.slug]["parentSlug"] is None
        assert data["categories"][level2.slug]["parentSlug"] == level1.slug
        assert data["categories"][level3.slug]["parentSlug"] == level2.slug

        # Verify no integer IDs
        for category_data in data["categories"].values():
            assert "id" not in category_data
            assert "parentCategoryId" not in category_data

    def test_export_multiple_root_categories(self, in_memory_db, temp_directory):
        """
        Test exporting multiple root categories with different children.

        Given: 3 root categories with different children
        When: Exported to YAML
        Then: All root categories present
        And: Children correctly reference parents
        """
        # Arrange
        root1 = Category(
            name="Housing", parentCategoryId=None, nature=Nature.MUST, color="#00FF00"
        )
        in_memory_db.add(root1)
        in_memory_db.flush()

        child1 = Category(
            name="Rent", parentCategoryId=root1.id, nature=Nature.MUST, color="#00FF00"
        )
        in_memory_db.add(child1)
        in_memory_db.flush()

        root2 = Category(
            name="Transportation",
            parentCategoryId=None,
            nature=Nature.NEED,
            color="#0000FF",
        )
        in_memory_db.add(root2)
        in_memory_db.flush()

        child2 = Category(
            name="Gas", parentCategoryId=root2.id, nature=Nature.NEED, color="#0000FF"
        )
        in_memory_db.add(child2)
        in_memory_db.flush()

        root3 = Category(
            name="Entertainment",
            parentCategoryId=None,
            nature=Nature.WANT,
            color="#FF00FF",
        )
        in_memory_db.add(root3)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_categories_to_yaml

        result_path = export_categories_to_yaml(in_memory_db, temp_directory)

        # Verify all roots and children present
        with open(result_path, "r") as f:
            data = yaml.safe_load(f)

        assert len(data["categories"]) == 5  # 3 roots + 2 children

        # Verify root categories have null parentSlug
        for root in [root1, root2, root3]:
            assert data["categories"][root.slug]["parentSlug"] is None

        # Verify children reference correct parents
        assert data["categories"][child1.slug]["parentSlug"] == root1.slug
        assert data["categories"][child2.slug]["parentSlug"] == root2.slug

    def test_export_category_with_metadata(self, in_memory_db, temp_directory):
        """
        Test exporting category with timestamps.

        Given: Category with createdAt and updatedAt
        When: Exported to YAML
        Then: Timestamps in ISO format
        And: All fields exported including nature and color
        """
        # Arrange
        category = Category(
            name="Test Category",
            parentCategoryId=None,
            nature=Nature.WANT,
            color="#ABCDEF",
        )
        in_memory_db.add(category)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_category_to_yaml

        result_path = export_category_to_yaml(category, temp_directory)

        # Verify all fields
        with open(result_path, "r") as f:
            data = yaml.safe_load(f)

        exported = data["categories"][category.slug]
        assert exported["name"] == "Test Category"
        assert exported["nature"] == "Want"
        assert exported["color"] == "#ABCDEF"
        assert exported["parentSlug"] is None
        assert "createdAt" in exported
        assert "updatedAt" in exported
        # Verify ISO format
        assert "T" in exported["createdAt"]
        assert "T" in exported["updatedAt"]
