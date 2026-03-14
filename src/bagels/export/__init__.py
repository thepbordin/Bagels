"""
Export functionality for Bagels entities.

This module provides functions to export SQLite entities to YAML format
for Git tracking and LLM accessibility.
"""

from bagels.export.slug_generator import generate_record_slug

__all__ = ["generate_record_slug"]
