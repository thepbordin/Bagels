"""
Spending analysis calculation module.

Provides functions for analyzing spending patterns by category,
time period, and other dimensions.
"""

from bagels.managers.utils import get_start_end_of_period
from bagels.queries.filters import parse_month


def calculate_spending_by_category(session, month: str | None = None) -> list[dict]:
    """
    Calculate total spending by category for a specific month.

    Args:
        session: SQLAlchemy session
        month: Month string in "YYYY-MM" format or None for current month

    Returns:
        List of dicts with category name, amount, and percentage,
        sorted by amount descending
    """
    from bagels.models.record import Record
    from bagels.models.category import Category
    from sqlalchemy import func

    # Parse month to get start/end dates
    if month:
        start_date, end_date = parse_month(month)
    else:
        # Use current month
        start_date, end_date = get_start_end_of_period(offset=0, offset_type="month")

    # Query records grouped by category
    results = (
        session.query(
            Category.id, Category.name, func.sum(Record.amount).label("total_amount")
        )
        .join(Record, Record.categoryId == Category.id)
        .filter(Record.date >= start_date, Record.date < end_date)
        .filter(Record.isIncome == False)  # noqa: E712
        .filter(Record.isTransfer == False)  # noqa: E712
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Record.amount).desc())
        .all()
    )

    spending_by_category = []
    total_spending = sum(r.total_amount for r in results) if results else 0

    for result in results:
        percentage = (
            (result.total_amount / total_spending * 100) if total_spending > 0 else 0
        )
        spending_by_category.append(
            {
                "category": result.name,
                "amount": round(result.total_amount, 2),
                "percentage": round(percentage, 1),
            }
        )

    return spending_by_category


def calculate_spending_by_day(session, month: str | None = None) -> list[dict]:
    """
    Calculate total spending by day for a specific month.

    Args:
        session: SQLAlchemy session
        month: Month string in "YYYY-MM" format or None for current month

    Returns:
        List of dicts with date and amount, sorted by date ascending
    """
    from bagels.models.record import Record
    from sqlalchemy import func

    # Parse month to get start/end dates
    if month:
        start_date, end_date = parse_month(month)
    else:
        # Use current month
        start_date, end_date = get_start_end_of_period(offset=0, offset_type="month")

    # Query records grouped by day
    results = (
        session.query(
            func.date(Record.date).label("day"),
            func.sum(Record.amount).label("total_amount"),
        )
        .filter(Record.date >= start_date, Record.date < end_date)
        .filter(Record.isIncome == False)  # noqa: E712
        .filter(Record.isTransfer == False)  # noqa: E712
        .group_by(func.date(Record.date))
        .order_by(func.date(Record.date))
        .all()
    )

    spending_by_day = []
    for result in results:
        spending_by_day.append(
            {
                "date": str(result.day) if result.day else None,
                "amount": round(result.total_amount, 2),
            }
        )

    return spending_by_day
