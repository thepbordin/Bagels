"""
Schema viewing commands for CLI.

Provides commands to display data model schemas for LLM context.
"""

import click
from bagels.models.account import Account
from bagels.models.category import Category
from bagels.models.person import Person
from bagels.models.record import Record
from bagels.models.record_template import RecordTemplate
from bagels.queries.formatters import to_yaml, to_json


@click.group()
def schema():
    """View data schema for LLM context."""
    pass


@schema.command()
def full():
    """Show full data schema (all models)."""
    # Extract all model schemas
    models = {
        "Account": _extract_model_schema(Account),
        "Category": _extract_model_schema(Category),
        "Person": _extract_model_schema(Person),
        "Record": _extract_model_schema(Record),
        "RecordTemplate": _extract_model_schema(RecordTemplate),
    }

    # Format as YAML structure
    schema_yaml = to_yaml({"models": models})
    click.echo(schema_yaml)


@schema.command("model")
@click.argument(
    "model_name",
    type=click.Choice(["account", "category", "person", "record", "template"]),
)
@click.option("--format", "-f", type=click.Choice(["yaml", "json"]), default="yaml")
def schema_model(model_name, format):
    """Show schema for a specific model."""
    # Map model_name to SQLAlchemy model class
    model_map = {
        "account": Account,
        "category": Category,
        "person": Person,
        "record": Record,
        "template": RecordTemplate,
    }

    model_class = model_map.get(model_name)
    if not model_class:
        click.echo(f"Error: Unknown model '{model_name}'")
        return

    # Extract schema
    schema_data = _extract_model_schema(model_class)

    # Format output
    if format == "json":
        output = to_json(schema_data)
    else:
        output = to_yaml(schema_data)

    click.echo(output)


def _extract_model_schema(model_class) -> dict:
    """
    Extract schema information from a SQLAlchemy model.

    Args:
        model_class: SQLAlchemy model class

    Returns:
        Dict with fields, relationships, and constraints
    """
    from sqlalchemy import inspect

    # Get mapper
    mapper = inspect(model_class)

    # Extract field information
    fields = []
    for column in mapper.columns:
        field_info = {
            "name": column.name,
            "type": str(column.type),
            "nullable": column.nullable,
            "primary_key": column.primary_key,
        }

        # Add foreign key info if present
        if column.foreign_keys:
            fk_keys = [str(fk.column) for fk in column.foreign_keys]
            field_info["foreign_key"] = fk_keys

        # Add default value if present
        if column.default is not None:
            field_info["default"] = str(column.default)

        fields.append(field_info)

    # Extract relationships
    relationships = []
    for rel in mapper.relationships:
        rel_info = {
            "name": rel.key,
            "target": rel.mapper.class_.__name__,
            "uselist": rel.uselist,
        }
        relationships.append(rel_info)

    # Get table name - ensure it's a string
    table_name = (
        str(mapper.tables[0].name) if mapper.tables else str(model_class.__tablename__)
    )

    return {
        "table_name": table_name,
        "fields": fields,
        "relationships": relationships,
    }
