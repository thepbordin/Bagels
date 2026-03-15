"""
Financial summary calculation module.

Provides functions for calculating monthly summaries, income/expense totals,
and budget status for CLI query commands.
"""

from bagels.managers.utils import get_start_end_of_period


def calculate_monthly_summary(session, month: str | None = None) -> dict:
    """
    Calculate financial summary for a specific month.

    Args:
        session: SQLAlchemy session
        month: Month string in "YYYY-MM" format or None for current month

    Returns:
        dict with keys: month, total_income, total_expenses, net_savings, record_count
    """
    # Parse month to get start/end dates
    if month:
        from bagels.queries.filters import parse_month

        start_date, end_date = parse_month(month)
        month_label = month
    else:
        # Use current month
        start_date, end_date = get_start_end_of_period(offset=0, offset_type="month")
        month_label = start_date.strftime("%Y-%m")

    # Query records for the month using the session
    from bagels.models.record import Record
    from sqlalchemy.orm import joinedload

    query = (
        session.query(Record)
        .options(
            joinedload(Record.category),
            joinedload(Record.account),
            joinedload(Record.splits),
        )
        .filter(Record.date >= start_date, Record.date < end_date)
        .filter(Record.isTransfer == False)  # noqa: E712
    )

    records = query.all()

    # Calculate totals
    total_income, total_expenses, net_savings = calculate_income_expense(records)

    return {
        "month": month_label,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_savings": net_savings,
        "record_count": len(records),
    }


def calculate_income_expense(records: list) -> tuple[float, float, float]:
    """
    Calculate income, expenses, and net savings from records.

    Args:
        records: List of Record objects

    Returns:
        tuple of (total_income, total_expenses, net_savings)
    """
    total_income = 0.0
    total_expenses = 0.0

    for record in records:
        # Skip transfers
        if record.isTransfer:
            continue

        # Subtract splits from record amount
        split_total = sum(split.amount for split in record.splits)
        record_amount = record.amount - split_total

        if record.isIncome:
            total_income += record_amount
        else:
            total_expenses += record_amount

    net_savings = total_income - total_expenses

    return (round(total_income, 2), round(total_expenses, 2), round(net_savings, 2))


def calculate_budget_status(session, month: str | None = None) -> dict:
    """
    Calculate budget status for categories with monthly budgets.

    Args:
        session: SQLAlchemy session
        month: Month string in "YYYY-MM" format or None for current month

    Returns:
        dict with category budgets, spent amounts, and remaining
    """
    from bagels.models.category import Category
    from bagels.models.record import Record
    from sqlalchemy.orm import joinedload

    # Parse month to get start/end dates
    if month:
        from bagels.queries.filters import parse_month

        start_date, end_date = parse_month(month)
        month_label = month
    else:
        # Use current month
        start_date, end_date = get_start_end_of_period(offset=0, offset_type="month")
        month_label = start_date.strftime("%Y-%m")

    # Query categories with budgets
    categories = (
        session.query(Category)
        .filter(Category.monthlyBudget.isnot(None))
        .filter(Category.monthlyBudget > 0)
        .all()
    )

    budget_status = []
    for category in categories:
        # Query records for this category in the month
        category_records = (
            session.query(Record)
            .options(joinedload(Record.splits))
            .filter(Record.categoryId == category.id)
            .filter(Record.date >= start_date, Record.date < end_date)
            .filter(Record.isIncome == False)  # noqa: E712
            .filter(Record.isTransfer == False)  # noqa: E712
            .all()
        )

        # Calculate spent amount
        spent = sum(
            r.amount - sum(split.amount for split in r.splits) for r in category_records
        )

        # Calculate remaining
        remaining = category.monthlyBudget - spent

        budget_status.append(
            {
                "category": category.name,
                "budget": category.monthlyBudget,
                "spent": round(spent, 2),
                "remaining": round(remaining, 2),
                "percentage": round((spent / category.monthlyBudget) * 100, 1)
                if category.monthlyBudget > 0
                else 0,
            }
        )

    return {"month": month_label, "categories": budget_status}
