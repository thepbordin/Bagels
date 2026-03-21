"""
LLM integration commands for CLI.

Provides context dump commands for AI-powered financial analysis.
"""

import click
from datetime import datetime
from sqlalchemy import create_engine

from bagels.models.database.app import Session as AppSession, init_db
from bagels.models.database.db import Base
from bagels.config import load_config
from bagels.locations import database_file
from bagels.queries.summaries import calculate_monthly_summary, calculate_budget_status
from bagels.queries.spending import calculate_spending_by_category
from bagels.queries.formatters import to_yaml
from bagels.managers.accounts import get_all_accounts
from bagels.managers.categories import get_all_categories_tree

Session = AppSession


def _open_session():
    """Open session with current DB path while allowing tests to patch Session."""
    engine = None
    if hasattr(Session, "configure"):
        engine = create_engine(f"sqlite:///{database_file().resolve()}")
        Base.metadata.create_all(engine)
        Session.configure(bind=engine)
    session = Session()
    return session, engine


@click.group()
def llm():
    """LLM integration commands."""
    pass


@llm.command("context")
@click.option("--month", "-m", help="Month for context (YYYY-MM), defaults to current")
@click.option("--period", help="Time period: all, 30d, 60d, 90d")
@click.option("--days", type=int, help="Number of recent days to include")
def llm_context(month, period, days):
    """Dump financial snapshot for LLM consumption.

    Outputs structured YAML with accounts, summary, spending by category,
    recent records, and budget status for AI analysis.
    """
    # Load config
    load_config()

    # Initialize database
    init_db()

    # Validate options (only one of month/period/days should be specified)
    specified = [x for x in [month, period, days] if x is not None]
    if len(specified) > 1:
        click.echo("Error: Only one of --month, --period, or --days can be specified")
        return

    session, engine = _open_session()

    try:
        # Determine time range
        if month:
            time_range = month
        elif period:
            time_range = period
        elif days:
            time_range = f"last_{days}_days"
        else:
            # Default to current month
            now = datetime.now()
            time_range = now.strftime("%Y-%m")

        # Build context dictionary
        context = {
            "snapshot_date": datetime.now().isoformat(),
            "period": time_range,
            "accounts": _get_accounts_context(session),
            "summary": _get_summary_context(session, month),
            "spending_by_category": _get_spending_context(session, month),
            "recent_records": _get_records_context(session, month, period, days),
            "budget_status": _get_budget_context(session, month),
            "categories": _get_categories_context(session),
        }

        # Output as YAML
        yaml_output = to_yaml(context)
        click.echo(yaml_output)

    except Exception as e:
        click.echo(
            click.style(f"Error generating LLM context: {e}", fg="red"), err=True
        )
        raise click.ClickException(str(e))
    finally:
        session.close()
        if engine is not None:
            engine.dispose()


def _get_accounts_context(session):
    """Get accounts context."""
    accounts = get_all_accounts(session)
    return [
        {
            "id": acc.id,
            "name": acc.name,
            "balance": acc.beginningBalance,
            "description": acc.description,
            "hidden": acc.hidden,
        }
        for acc in accounts
    ]


def _get_summary_context(session, month):
    """Get monthly summary context."""
    try:
        summary = calculate_monthly_summary(session, month)
        return {
            "month": summary["month"],
            "total_income": summary["total_income"],
            "total_expenses": summary["total_expenses"],
            "net_savings": summary["net_savings"],
            "record_count": summary["record_count"],
        }
    except Exception:
        return None


def _get_spending_context(session, month):
    """Get spending by category context."""
    try:
        spending = calculate_spending_by_category(session, month)
        return spending
    except Exception:
        return []


def _get_records_context(session, month, period, days):
    """Get recent records context."""
    from bagels.managers.utils import get_start_end_of_period
    from sqlalchemy.orm import joinedload

    try:
        # Determine date range
        if month:
            from bagels.queries.filters import parse_month

            start_date, end_date = parse_month(month)
        elif days:
            from datetime import timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
        elif period == "all":
            # No date filter
            start_date = None
            end_date = None
        else:
            # Default to current month
            start_date, end_date = get_start_end_of_period(
                offset=0, offset_type="month"
            )

        # Query records using the provided session with eager loading
        from bagels.models.record import Record as RecordModel

        query = session.query(RecordModel).options(
            joinedload(RecordModel.category),
            joinedload(RecordModel.account),
        )
        if start_date is not None:
            query = query.filter(RecordModel.date >= start_date)
        if end_date is not None:
            query = query.filter(RecordModel.date < end_date)
        query = query.order_by(RecordModel.date.desc())
        records = query.all()

        # Limit to last 30 records for LLM context
        recent_records = records[:30]

        return [
            {
                "id": rec.slug if rec.slug else rec.id,
                "label": rec.label,
                "amount": rec.amount,
                "date": rec.date.isoformat() if rec.date else None,
                "is_income": rec.isIncome,
                "is_transfer": rec.isTransfer,
                "category": rec.category.name if rec.category else None,
                "account": rec.account.name if rec.account else None,
            }
            for rec in recent_records
        ]
    except Exception:
        return []


def _get_budget_context(session, month):
    """Get budget status context."""
    try:
        budget = calculate_budget_status(session, month)
        return budget
    except Exception:
        return None


def _get_categories_context(session):
    """Get categories context."""
    try:
        categories = get_all_categories_tree(session)
        return [
            {
                "id": cat.id,
                "name": cat.name,
                "nature": str(cat.nature),
                "color": cat.color,
                "parent": cat.parentCategory.name if cat.parentCategory else None,
                "monthly_budget": getattr(cat, "monthlyBudget", None),
            }
            for cat, _, _ in categories
        ]
    except Exception:
        return []
