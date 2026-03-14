"""
Slug-based ID generation for records.

Generates unique slugs in format r_YYYY-MM-DD_### to enable
Git-friendly merge-by-ID workflows for financial records.
"""

from datetime import date, datetime, time
from sqlalchemy.orm import Session


def generate_record_slug(record_date: date, session: Session) -> str:
    """
    Generate a unique slug for a record based on its date.

    Slugs follow the pattern r_YYYY-MM-DD_### where ### is a sequential
    number that resets each day. This enables Git mergeability by using
    date-based scoping instead of global sequences.

    Args:
        record_date: The date of the record
        session: SQLAlchemy session for querying existing records

    Returns:
        A unique slug string like "r_2026-03-14_001"
    """
    # Format date part
    date_str = record_date.strftime("%Y-%m-%d")

    # Find existing records for this date
    start_of_day = datetime.combine(record_date, time.min)
    end_of_day = datetime.combine(record_date, time.max)

    from bagels.models.record import Record

    existing = session.query(Record).filter(
        Record.date >= start_of_day,
        Record.date <= end_of_day
    ).all()

    # Extract sequence numbers from existing slugs
    sequences = []
    for record in existing:
        # Check if record has slug attribute and slug exists
        if hasattr(record, 'slug') and record.slug and record.slug.startswith(f"r_{date_str}_"):
            try:
                seq = int(record.slug.split('_')[-1])
                sequences.append(seq)
            except (ValueError, IndexError):
                # Invalid slug format, skip it
                pass

    # Next sequence number
    next_seq = max(sequences) + 1 if sequences else 1
    return f"r_{date_str}_{next_seq:03d}"
