"""
Filter utilities for CLI query commands.

Provides common filter patterns for dates, amounts, and categories
with SQLAlchemy query builder support.
"""

from datetime import datetime

from sqlalchemy.orm import Query

from bagels.managers.utils import get_start_end_of_period


def parse_month(month_str: str | None) -> tuple[datetime, datetime] | None:
    """
    Parse "YYYY-MM" format to (start_of_month, end_of_month).

    Args:
        month_str: Month string in "YYYY-MM" format or None

    Returns:
        Tuple of (start_datetime, end_datetime) or None if month_str is None

    Raises:
        ValueError: If month_str format is invalid
    """
    if month_str is None:
        return None

    try:
        # Parse YYYY-MM format
        year, month = map(int, month_str.split("-"))

        # Calculate month offset from current date
        now = datetime.now()
        current_year = now.year
        current_month = now.month

        # Calculate offset
        offset = (year - current_year) * 12 + (month - current_month)

        # Use existing utility to get start/end of month
        start, end = get_start_end_of_period(offset=offset, offset_type="month")
        return start, end

    except (ValueError, AttributeError) as e:
        raise ValueError(
            f"Invalid month format '{month_str}'. Expected YYYY-MM format: {e}"
        )


def parse_amount_range(range_str: str | None) -> tuple[float, float] | None:
    """
    Parse amount range string "100..500" to (100.0, 500.0).

    Supports:
    - "100..500" -> (100.0, 500.0)
    - "100.." -> (100.0, float('inf'))
    - "..500" -> (0.0, 500.0)

    Args:
        range_str: Range string in format "min..max" or None

    Returns:
        Tuple of (min_amount, max_amount) or None if range_str is None

    Raises:
        ValueError: If range_str format is invalid
    """
    if range_str is None:
        return None

    try:
        if ".." not in range_str:
            raise ValueError("Range must contain '..' separator")

        parts = range_str.split("..")

        if len(parts) != 2:
            raise ValueError(f"Invalid range format '{range_str}'")

        min_str, max_str = parts

        # Parse min (default to 0 if empty)
        if min_str:
            min_amount = float(min_str)
        else:
            min_amount = 0.0

        # Parse max (default to infinity if empty)
        if max_str:
            max_amount = float(max_str)
        else:
            max_amount = float("inf")

        return min_amount, max_amount

    except ValueError as e:
        raise ValueError(
            f"Invalid amount range '{range_str}'. Expected format '100..500': {e}"
        )


def apply_date_filters(
    query: Query,
    month: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> Query:
    """
    Apply date filters to SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        month: Month string in "YYYY-MM" format
        date_from: Start date string in "YYYY-MM-DD" format
        date_to: End date string in "YYYY-MM-DD" format

    Returns:
        Modified query with date filters applied

    Raises:
        ValueError: If date formats are invalid
    """
    from bagels.models.record import Record

    # Apply month filter (takes precedence over date_from/date_to)
    if month:
        start, end = parse_month(month)
        query = query.filter(Record.date >= start, Record.date < end)
    else:
        # Apply individual date filters
        if date_from:
            try:
                start_date = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(Record.date >= start_date)
            except ValueError as e:
                raise ValueError(
                    f"Invalid date_from format '{date_from}'. Expected YYYY-MM-DD: {e}"
                )

        if date_to:
            try:
                # Include entire end date
                end_date = datetime.strptime(date_to, "%Y-%m-%d")
                # Set to end of day
                end_date = end_date.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
                query = query.filter(Record.date <= end_date)
            except ValueError as e:
                raise ValueError(
                    f"Invalid date_to format '{date_to}'. Expected YYYY-MM-DD: {e}"
                )

    return query


def apply_category_filter(query: Query, category_name: str | None = None) -> Query:
    """
    Apply category filter to SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        category_name: Category name to filter by

    Returns:
        Modified query with category filter applied
    """
    from bagels.models.record import Record
    from bagels.models.category import Category

    if category_name:
        query = query.join(Record.category).filter(Category.name == category_name)

    return query


def apply_amount_filter(query: Query, amount_range: str | None = None) -> Query:
    """
    Apply amount range filter to SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        amount_range: Amount range string in "min..max" format

    Returns:
        Modified query with amount filter applied

    Raises:
        ValueError: If amount range format is invalid
    """
    from bagels.models.record import Record

    if amount_range:
        min_amt, max_amt = parse_amount_range(amount_range)

        if max_amt == float("inf"):
            # Only lower bound
            query = query.filter(Record.amount >= min_amt)
        elif min_amt == 0.0 and max_amt > 0:
            # Only upper bound
            query = query.filter(Record.amount <= max_amt)
        else:
            # Both bounds
            query = query.filter(Record.amount.between(min_amt, max_amt))

    return query


def apply_account_filter(query: Query, account_name: str | None = None) -> Query:
    """
    Apply account filter to SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        account_name: Account name to filter by

    Returns:
        Modified query with account filter applied
    """
    from bagels.models.record import Record
    from bagels.models.account import Account

    if account_name:
        query = query.join(Record.account).filter(Account.name == account_name)

    return query


def apply_person_filter(query: Query, person_name: str | None = None) -> Query:
    """
    Apply person filter to SQLAlchemy query (via splits).

    Args:
        query: SQLAlchemy query object
        person_name: Person name to filter by

    Returns:
        Modified query with person filter applied
    """
    from bagels.models.record import Record
    from bagels.models.split import Split
    from bagels.models.person import Person

    if person_name:
        # Filter records that have splits with the specified person
        query = (
            query.join(Record.splits)
            .join(Split.person)
            .filter(Person.name == person_name)
        )

    return query
