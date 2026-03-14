"""
Tests for record template export to YAML format (TDD - RED phase).

These tests define the expected behavior for exporting RecordTemplate entities
from SQLite to human-readable YAML files with relationship references.
"""

import pytest
from pathlib import Path
import yaml

from bagels.models.record_template import RecordTemplate


class TestTemplateExport:
    """Test suite for record template export functionality."""

    def test_export_single_template(self, in_memory_db, temp_directory, sample_account, sample_category):
        """
        Test exporting a single template to YAML.

        Given: RecordTemplate with label, amount, accountId, categoryId
        When: export_template_to_yaml(template, temp_dir)
        Then: YAML contains template with slug key
        And: All fields exported
        And: Foreign keys reference slugs (accountSlug, categorySlug)
        """
        # Arrange
        template = RecordTemplate(
            label="Monthly Rent",
            amount=1500.0,
            accountId=sample_account.id,
            categoryId=sample_category.id,
            isIncome=False,
            isTransfer=False
        )
        in_memory_db.add(template)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_template_to_yaml

        result_path = export_template_to_yaml(template, temp_directory)

        # Verify file exists
        assert result_path == temp_directory / "templates.yaml"
        assert result_path.exists()

        # Verify YAML structure
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        assert "templates" in data
        assert len(data["templates"]) == 1

        # Template should be keyed by slug
        template_slug = template.slug
        assert template_slug in data["templates"]

        exported_template = data["templates"][template_slug]
        assert exported_template["label"] == "Monthly Rent"
        assert exported_template["amount"] == 1500.0
        assert exported_template["accountSlug"] == sample_account.slug
        assert exported_template["categorySlug"] == sample_category.slug
        assert exported_template["isIncome"] is False
        assert exported_template["isTransfer"] is False
        # No integer IDs
        assert "accountId" not in exported_template
        assert "categoryId" not in exported_template
        assert "id" not in exported_template

    def test_export_multiple_templates(self, in_memory_db, temp_directory, sample_account, sample_category):
        """
        Test exporting multiple templates to YAML.

        Given: 3 templates in database
        When: export_all_templates(session, temp_dir)
        Then: YAML contains all 3 templates
        And: Order preserved (templates have order field)
        """
        # Arrange
        template1 = RecordTemplate(
            label="Template 1",
            amount=100.0,
            accountId=sample_account.id,
            categoryId=sample_category.id,
            isIncome=False
        )
        template2 = RecordTemplate(
            label="Template 2",
            amount=200.0,
            accountId=sample_account.id,
            categoryId=sample_category.id,
            isIncome=True
        )
        template3 = RecordTemplate(
            label="Template 3",
            amount=300.0,
            accountId=sample_account.id,
            categoryId=sample_category.id,
            isIncome=False
        )

        in_memory_db.add_all([template1, template2, template3])
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_all_templates

        result_path = export_all_templates(in_memory_db, temp_directory)

        # Verify file exists
        assert result_path == temp_directory / "templates.yaml"
        assert result_path.exists()

        # Verify YAML structure
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        assert "templates" in data
        assert len(data["templates"]) == 3

        # Verify all templates present
        for template in [template1, template2, template3]:
            assert template.slug in data["templates"]

    def test_export_template_with_all_relationships(self, in_memory_db, temp_directory, sample_account, sample_category, sample_person):
        """
        Test exporting template with all relationship types.

        Given: Template with accountId, categoryId, personId
        When: Exported to YAML
        Then: All relationships use slug references
        And: No integer IDs in YAML
        """
        # Arrange
        template = RecordTemplate(
            label="Complex Template",
            amount=500.0,
            accountId=sample_account.id,
            categoryId=sample_category.id,
            isIncome=False,
            isTransfer=False
        )
        in_memory_db.add(template)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_template_to_yaml

        result_path = export_template_to_yaml(template, temp_directory)

        # Verify all relationships use slugs
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        exported = data["templates"][template.slug]
        assert "accountSlug" in exported
        assert "categorySlug" in exported
        assert isinstance(exported["accountSlug"], str)
        assert isinstance(exported["categorySlug"], str)
        # No integer IDs
        assert "accountId" not in exported
        assert "categoryId" not in exported
        assert "id" not in exported
        assert "personId" not in exported

    def test_export_template_with_transfer(self, in_memory_db, temp_directory, sample_account):
        """
        Test exporting template with transfer relationship.

        Given: Template with isTransfer=True and transferToAccountId
        When: Exported to YAML
        Then: Transfer relationship uses slug reference
        """
        # Arrange
        to_account = sample_account
        from_account = Account(
            name="From Account",
            description="Source account",
            beginningBalance=1000.0,
            hidden=False
        )
        in_memory_db.add(from_account)
        in_memory_db.flush()

        template = RecordTemplate(
            label="Transfer Template",
            amount=500.0,
            accountId=from_account.id,
            isTransfer=True,
            isIncome=False,
            transferToAccountId=to_account.id
        )
        in_memory_db.add(template)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_template_to_yaml

        result_path = export_template_to_yaml(template, temp_directory)

        # Verify transfer uses slug
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        exported = data["templates"][template.slug]
        assert exported["isTransfer"] is True
        assert exported["transferToAccountSlug"] == to_account.slug
        # No integer ID
        assert "transferToAccountId" not in exported

    def test_export_template_with_metadata(self, in_memory_db, temp_directory, sample_account, sample_category):
        """
        Test exporting template with metadata and order.

        Given: Template with createdAt, updatedAt, order
        When: Exported to YAML
        Then: Metadata included in export
        And: Order field preserved
        """
        # Arrange
        template = RecordTemplate(
            label="Metadata Test",
            amount=100.0,
            accountId=sample_account.id,
            categoryId=sample_category.id,
            isIncome=False
        )
        in_memory_db.add(template)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_template_to_yaml

        result_path = export_template_to_yaml(template, temp_directory)

        # Verify metadata
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        exported = data["templates"][template.slug]
        assert "createdAt" in exported
        assert "updatedAt" in exported
        assert "order" in exported
        # Verify ISO format for timestamps
        assert "T" in exported["createdAt"]
        assert "T" in exported["updatedAt"]
        # Verify order is integer
        assert isinstance(exported["order"], int)
