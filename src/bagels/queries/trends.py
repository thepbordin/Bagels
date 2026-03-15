"""
Trend comparison calculation module.

Provides functions for comparing spending across multiple months,
calculating month-over-month changes, and tracking category trends.
"""

from bagels.managers.utils import get_start_end_of_period
from bagels.queries.summaries import calculate_monthly_summary


def calculate_monthly_comparison(session, months: int = 3) -> list[dict]:
    """
    Compare spending across multiple months.

    Args:
        session: SQLAlchemy session
        months: Number of months to compare (default: 3)

    Returns:
        List of monthly summaries with month-over-month change percentages,
        sorted by month descending (most recent first)
    """
    if months < 1 or months > 12:
        raise ValueError("months must be between 1 and 12")

    monthly_summaries = []

    # Calculate summaries for the last N months (including current)
    for offset in range(months):
        # Get start/end dates for this month
        start_date, end_date = get_start_end_of_period(
            offset=-offset, offset_type="month"
        )
        month_label = start_date.strftime("%Y-%m")

        # Calculate summary for this month
        summary = calculate_monthly_summary(session, month_label)

        # Calculate month-over-month change if we have a previous month
        if offset > 0:
            prev_summary = monthly_summaries[offset - 1]
            prev_savings = prev_summary["net_savings"]

            # Calculate percentage change
            if prev_savings != 0:
                change_pct = (
                    (summary["net_savings"] - prev_savings) / abs(prev_savings)
                ) * 100
            else:
                change_pct = 0.0

            summary["change_percentage"] = round(change_pct, 1)
            summary["change_direction"] = (
                "up" if change_pct > 0 else "down" if change_pct < 0 else "flat"
            )
        else:
            # Most recent month has no previous comparison
            summary["change_percentage"] = None
            summary["change_direction"] = None

        monthly_summaries.append(summary)

    return monthly_summaries


def calculate_category_trends(session, months: int = 3) -> dict:
    """
    Track spending by category across multiple months.

    Args:
        session: SQLAlchemy session
        months: Number of months to analyze (default: 3)

    Returns:
        Dict mapping category names to lists of monthly spending data
        Format: {"Food": [{"month": "2026-03", "amount": 500}, ...], ...}
    """
    if months < 1 or months > 12:
        raise ValueError("months must be between 1 and 12")

    from bagels.models.record import Record
    from bagels.models.category import Category
    from sqlalchemy.orm import joinedload

    category_trends = {}

    # Get all categories that have records
    categories = (
        session.query(Category)
        .join(Record)
        .filter(Record.isIncome == False)  # noqa: E712
        .filter(Record.isTransfer == False)  # noqa: E712
        .distinct()
        .all()
    )

    for category in categories:
        monthly_data = []

        # Calculate spending for this category across months
        for offset in range(months):
            start_date, end_date = get_start_end_of_period(
                offset=-offset, offset_type="month"
            )
            month_label = start_date.strftime("%Y-%m")

            # Query records for this category in the month
            records = (
                session.query(Record)
                .options(joinedload(Record.splits))
                .filter(Record.categoryId == category.id)
                .filter(Record.date >= start_date, Record.date < end_date)
                .filter(Record.isIncome == False)  # noqa: E712
                .filter(Record.isTransfer == False)  # noqa: E712
                .all()
            )

            # Calculate total spent
            total = sum(
                r.amount - sum(split.amount for split in r.splits) for r in records
            )

            monthly_data.append({"month": month_label, "amount": round(total, 2)})

        category_trends[category.name] = monthly_data

    return category_trends


def _get_previous_months(n: int) -> list[str]:
    """
    Generate list of month strings for the last N months.

    Args:
        n: Number of months to generate

    Returns:
        List of month strings in "YYYY-MM" format, most recent first
    """
    months = []
    for offset in range(n):
        start_date, _ = get_start_end_of_period(offset=-offset, offset_type="month")
        months.append(start_date.strftime("%Y-%m"))

    return months
