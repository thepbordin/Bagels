"""
Git CLI command group for Bagels.

Provides four subcommands:
  bagels git status  - show uncommitted YAML file paths
  bagels git log     - print recent commit history
  bagels git sync    - commit all dirty YAML files and push to remote
  bagels git pull    - export, commit, pull from remote, reimport YAML
"""

import sys

import click


# ---------------------------------------------------------------------------
# Helper: full YAML reimport (used by pull command)
# ---------------------------------------------------------------------------


def _run_full_import() -> None:
    """Reimport all YAML files into SQLite after a pull.

    Runs the same import sequence as `bagels import`: accounts, categories,
    persons, templates, records.  All operations use a fresh Session.
    """
    import yaml

    from bagels.importer.importer import (
        import_accounts_from_yaml,
        import_categories_from_yaml,
        import_persons_from_yaml,
        import_records_from_yaml,
        import_templates_from_yaml,
    )
    from bagels.locations import (
        yaml_accounts_path,
        yaml_categories_path,
        yaml_persons_path,
        yaml_records_directory,
        yaml_templates_path,
    )
    from bagels.models.database.app import Session

    session = Session()
    try:
        if yaml_accounts_path().exists():
            with open(yaml_accounts_path()) as f:
                import_accounts_from_yaml(yaml.safe_load(f), session=session)

        if yaml_categories_path().exists():
            with open(yaml_categories_path()) as f:
                import_categories_from_yaml(yaml.safe_load(f), session=session)

        if yaml_persons_path().exists():
            with open(yaml_persons_path()) as f:
                import_persons_from_yaml(yaml.safe_load(f), session=session)

        if yaml_templates_path().exists():
            with open(yaml_templates_path()) as f:
                import_templates_from_yaml(yaml.safe_load(f), session=session)

        if yaml_records_directory().exists():
            for yaml_file in sorted(yaml_records_directory().glob("*.yaml")):
                with open(yaml_file) as f:
                    import_records_from_yaml(yaml.safe_load(f), session=session)
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Click group
# ---------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.pass_context
def git(ctx: click.Context) -> None:
    """Git sync operations for YAML data."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


@git.command("status")
def status() -> None:
    """Show uncommitted YAML file paths in the data directory."""
    from bagels.git.operations import get_status

    files = get_status()
    if not files:
        click.echo("Working tree clean — no uncommitted changes.")
    else:
        for path in files:
            click.echo(path)
        click.echo(f"\n{len(files)} file(s) with uncommitted changes.")


# ---------------------------------------------------------------------------
# log
# ---------------------------------------------------------------------------


@git.command("log")
@click.option(
    "--count",
    default=10,
    type=int,
    show_default=True,
    help="Number of commits to show.",
)
def log(count: int) -> None:
    """Print recent git commit history for the data directory."""
    from bagels.git.operations import get_log

    entries = get_log(max_count=count)
    if not entries:
        click.echo("No commits found.")
    else:
        for entry in entries:
            click.echo(f"{entry['hash']}  {entry['date']}  {entry['message']}")


# ---------------------------------------------------------------------------
# sync
# ---------------------------------------------------------------------------


@git.command("sync")
def sync() -> None:
    """Commit all dirty YAML files and push to remote."""
    from bagels.config import CONFIG, load_config
    from bagels.git.operations import auto_commit_yaml, get_status, push_to_remote
    from bagels.locations import data_directory
    from bagels.models.database.app import init_db

    init_db()
    load_config()

    dirty = get_status()
    data_dir = data_directory()

    committed = 0
    for rel_path in dirty:
        abs_path = data_dir / rel_path
        if auto_commit_yaml(abs_path, message=f"sync: {rel_path}"):
            committed += 1

    remote = CONFIG.git.remote
    branch = CONFIG.git.branch
    pushed = push_to_remote(remote, branch)

    if not pushed:
        click.echo(
            click.style(
                f"Warning: push to {remote}/{branch} failed (working offline or no remote configured).",
                fg="yellow",
            )
        )
    else:
        click.echo(f"Synced {committed} file(s), pushed to {remote}/{branch}.")


# ---------------------------------------------------------------------------
# pull
# ---------------------------------------------------------------------------


@git.command("pull")
def pull() -> None:
    """Export current data, pull from remote, reimport YAML into SQLite.

    Sequence (safe data-loss prevention):
      1. init_db + load_config
      2. Export all SQLite entities to YAML
      3. Commit any export changes
      4. Pull from remote (exit 1 on failure)
      5. Reimport YAML into SQLite
    """
    from bagels.config import CONFIG, load_config
    from bagels.export.exporter import (
        export_accounts,
        export_categories,
        export_persons,
        export_records_by_month,
        export_templates,
    )
    from bagels.git.operations import auto_commit_yaml, get_status, pull_from_remote
    from bagels.locations import data_directory
    from bagels.models.database.app import Session, init_db

    init_db()
    load_config()

    data_dir = data_directory()
    session = Session()

    try:
        # Step 1: Full export to YAML
        click.echo("Exporting current data to YAML...")
        export_accounts(session=session, output_dir=data_dir)
        export_categories(session=session, output_dir=data_dir)
        export_persons(session=session, output_dir=data_dir)
        export_templates(session=session, output_dir=data_dir)
        export_records_by_month(session=session, output_dir=data_dir)
    finally:
        session.close()

    # Step 2: Commit export changes
    dirty = get_status()
    for rel_path in dirty:
        auto_commit_yaml(data_dir / rel_path, message=f"pre-pull export: {rel_path}")

    # Step 3: Pull from remote
    remote = CONFIG.git.remote
    branch = CONFIG.git.branch
    click.echo(f"Pulling from {remote}/{branch}...")

    success = pull_from_remote(remote, branch, silent=False)
    if not success:
        click.echo(
            click.style(
                f"Error: pull from {remote}/{branch} failed. "
                "Check your network connection and remote configuration.",
                fg="red",
            ),
            err=True,
        )
        sys.exit(1)

    # Step 4: Reimport YAML into SQLite
    click.echo("Reimporting YAML into database...")
    _run_full_import()

    click.echo(
        click.style("Pull complete — YAML reimported into database.", fg="green")
    )
