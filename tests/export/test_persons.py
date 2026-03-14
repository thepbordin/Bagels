"""
Tests for person export to YAML format (TDD - RED phase).

These tests define the expected behavior for exporting Person entities
from SQLite to human-readable YAML files.
"""

import pytest
from pathlib import Path
import yaml

from bagels.models.person import Person


class TestPersonExport:
    """Test suite for person export functionality."""

    def test_export_single_person(self, in_memory_db, temp_directory):
        """
        Test exporting a single person to YAML.

        Given: Person(name="John Doe")
        When: export_person_to_yaml(person, temp_dir)
        Then: YAML contains person with slug key
        And: Name field exported
        """
        # Arrange
        person = Person(name="John Doe")
        in_memory_db.add(person)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_person_to_yaml

        result_path = export_person_to_yaml(person, temp_directory)

        # Verify file exists
        assert result_path == temp_directory / "persons.yaml"
        assert result_path.exists()

        # Verify YAML structure
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        assert "persons" in data
        assert len(data["persons"]) == 1

        # Person should be keyed by slug
        person_slug = person.slug
        assert person_slug in data["persons"]

        exported_person = data["persons"][person_slug]
        assert exported_person["name"] == "John Doe"

    def test_export_multiple_persons(self, in_memory_db, temp_directory):
        """
        Test exporting multiple persons to YAML.

        Given: 5 persons in database
        When: export_all_persons(session, temp_dir)
        Then: YAML contains all 5 persons
        And: Dict keyed by person slugs
        """
        # Arrange
        persons = [
            Person(name="John Doe"),
            Person(name="Jane Smith"),
            Person(name="Bob Johnson"),
            Person(name="Alice Williams"),
            Person(name="Charlie Brown")
        ]

        in_memory_db.add_all(persons)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_all_persons

        result_path = export_all_persons(in_memory_db, temp_directory)

        # Verify file exists
        assert result_path == temp_directory / "persons.yaml"
        assert result_path.exists()

        # Verify YAML structure
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        assert "persons" in data
        assert len(data["persons"]) == 5

        # Verify all persons present with slug keys
        for person in persons:
            assert person.slug in data["persons"]
            exported = data["persons"][person.slug]
            assert exported["name"] == person.name
            # No integer IDs
            assert "id" not in exported

    def test_export_person_with_metadata(self, in_memory_db, temp_directory):
        """
        Test exporting person with timestamps.

        Given: Person with createdAt and updatedAt
        When: Exported to YAML
        Then: Timestamps in ISO format
        """
        # Arrange
        person = Person(name="Test Person")
        in_memory_db.add(person)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_person_to_yaml

        result_path = export_person_to_yaml(person, temp_directory)

        # Verify timestamps
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        exported = data["persons"][person.slug]
        assert exported["name"] == "Test Person"
        assert "createdAt" in exported
        assert "updatedAt" in exported
        # Verify ISO format
        assert "T" in exported["createdAt"]
        assert "T" in exported["updatedAt"]

    def test_export_person_minimal_fields(self, in_memory_db, temp_directory):
        """
        Test that Person model has minimal fields.

        Given: Person with only name field
        When: Exported to YAML
        Then: Only name and metadata exported
        And: No unnecessary fields
        """
        # Arrange
        person = Person(name="Minimal Person")
        in_memory_db.add(person)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_person_to_yaml

        result_path = export_person_to_yaml(person, temp_directory)

        # Verify minimal fields
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        exported = data["persons"][person.slug]

        # Person model has minimal fields per existing codebase
        expected_fields = {"name", "createdAt", "updatedAt"}
        actual_fields = set(exported.keys())

        # Should have exactly these fields
        assert actual_fields == expected_fields
        assert exported["name"] == "Minimal Person"
