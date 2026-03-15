"""
Spending analysis module for CLI query commands.

Provides spending calculation functions grouped by category and day
for analyzing expense patterns.
"""

from datetime import datetime
from collections import defaultdict

from sqlalchemy.orm import sessionmaker

from bagels.models.database.app import db_engine
from bagels.models.record import Record
from bagels.queries.filters import parse_month

Session = sessionmaker(bind=db_engine)


def calculate_spending_by_category(session, month: str | None = None) -> list[dict]:
    """
    Calculate spending breakdown by category for a given month.

    Args:
        session: SQLAlchemy session
        month: Month string in "YYYY-MM" format or None for current month

    Returns:
        List of dicts with keys: category, amount, count
        Sorted by amount descending (highest spending first)
    """
    # Parse month or use current month
    if month:
        start_date, end_date = parse_month(month)
    else:
        # Use current month
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        # Calculate first day of next month
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1)
        else:
            end_date = datetime(now.year, now.month + 1, 1)

    # Query expense records for the month
    query = session.query(Record).filter(
        Record.isIncome == False,  # noqa: E712
        Record.date >= start_date,
        Record.date < end_date,
        Record.isTransfer == False,  # noqa: E712
    )

    # Get category and account relationships
    from sqlalchemy.orm import joinedload

    query = query.options(joinedload(Record.category), joinedload(Record.splits))

    records = query.all()

    # Group by category and sum amounts
    category_totals = defaultdict(lambda: {"amount": 0.0, "count": 0})

    for record in records:
        # Subtract split amounts from record amount
        splits_sum = sum(split.amount for split in record.splits)
        actual_spend = record.amount - splits_sum

        # Get category name or use "Uncategorized"
        if record.category:
            category_name = record.category.name
        else:
            category_name = "Uncategorized"

        category_totals[category_name]["amount"] += actual_spend
        category_totals[category_name]["count"] += 1

    # Convert to list of dicts
    result = [
        {"category": cat, "amount": data["amount"], "count": data["count"]}
        for cat, data in category_totals.items()
    ]

    # Sort by amount descending
    result.sort(key=lambda x: x["amount"], reverse=True)

    return result


def calculate_spending_by_day(session, month: str | None = None) -> list[dict]:
    """
    Calculate spending breakdown by day for a given month.

    Args:
        session: SQLAlchemy session
        month: Month string in "YYYY-MM" format or None for current month

    Returns:
        List of dicts with keys: date, amount, count
        Sorted by date ascending (chronological order)
    """
    # Parse month or use current month
    if month:
        start_date, end_date = parse_month(month)
    else:
        # Use current month
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        # Calculate first day of next month
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1)
        else:
            end_date = datetime(now.year, now.month + 1, 1)

    # Query expense records for the month
    query = session.query(Record).filter(
        Record.isIncome == False,  # noqa: E712
        Record.date >= start_date,
        Record.date < end_date,
        Record.isTransfer == False,  # noqa: E712
    )

    # Get splits relationship
    from sqlalchemy.orm import joinedload

    query = query.options(joinedload(Record.splits))

    records = query.all()

    # Group by date and sum amounts
    daily_totals = defaultdict(lambda: {"amount": 0.0, "count": 0})

    for record in records:
        # Subtract split amounts from record amount
        splits_sum = sum(split.amount for split in record.splits)
        actual_spend = record.amount - splits_sum

        # Get date string
        date_str = record.date.strftime("%Y-%m-%d")

        daily_totals[date_str]["amount"] += actual_spend
        daily_totals[date_str]["count"] += 1

    # Fill in missing days with $0.00
    current_date = start_date.date()
    end_date_normalized = end_date.date()

    all_days = []
    while current_date < end_date_normalized:
        date_str = current_date.strftime("%Y-%m-%d")
        if date_str in daily_totals:
            all_days.append(
                {
                    "date": date_str,
                    "amount": daily_totals[date_str]["amount"],
                    "count": daily_totals[date_str]["count"],
                }
            )
        else:
            all_days.append({"date": date_str, "amount": 0.0, "count": 0})
        current_date = current_date.replace(day=current_date.day + 1)

    return all_days


def _group_records_by_field(records: list[Record], field: str) -> dict:
    """
    Generic grouping function for records by a field.

    Args:
        records: List of Record objects
        field: Field name to group by (e.g., 'category', 'date')

    Returns:
        Dict with field values as keys and dicts with sums and counts as values
    """
    grouped = defaultdict(lambda: {"amount": 0.0, "count": 0})

    for record in records:
        # Get field value
        if field == "category":
            value = record.category.name if record.category else "Uncategorized"
        elif field == "date":
            value = record.date.strftime("%Y-%m-%d")
        else:
            value = str(getattr(record, field, "Unknown"))

        # Calculate actual spend (minus splits)
        splits_sum = sum(split.amount for split in record.splits)
        actual_spend = record.amount - splits_sum

        grouped[value]["amount"] += actual_spend
        grouped[value]["count"] += 1

    return dict(grouped)
