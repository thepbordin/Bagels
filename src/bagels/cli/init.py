"""
Init CLI command for Bagels.

Provides the 'bagels init' command to initialize a new data directory
with Git repository.
"""

import click


@click.command()
@click.option('--force', is_flag=True, help='Reinitialize even if Git repo exists')
def init_command(force: bool):
    """Initialize new data directory with Git repository."""
    from bagels.locations import data_directory
    from bagels.git.repository import initialize_git_repo, create_gitignore

    try:
        # Ensure data directory exists
        data_dir = data_directory()
        click.echo(f"Data directory: {data_dir}")

        # Initialize Git repository
        click.echo("Initializing Git repository...")
        newly_created = initialize_git_repo(data_dir)

        if newly_created:
            click.echo(click.style("  ✓ Git repository initialized", fg="green"))
        else:
            if not force:
                click.echo(click.style("  ⚠ Git repository already exists", fg="yellow"))
                click.echo("  Use --force to reinitialize")
                return
            else:
                click.echo(click.style("  ✓ Git repository reinitialized", fg="green"))

        # Create .gitignore
        create_gitignore(data_dir)
        click.echo(click.style("  ✓ .gitignore created", fg="green"))

        # Create initial commit if repository is new
        if newly_created:
            from git import Repo
            repo = Repo(data_dir)
            if not repo.head.is_valid():
                click.echo("Creating initial commit...")
                repo.index.add([".gitignore"])
                repo.index.commit("Initial commit: Bagels data directory")
                click.echo(click.style("  ✓ Initial commit created", fg="green"))

        click.echo(click.style("\n✓ Initialization complete!", fg="green"))
        click.echo("\nNext steps:")
        click.echo("  1. Run 'bagels export' to create YAML files")
        click.echo("  2. Add remote: git remote add origin <url>")
        click.echo("  3. Push: git push -u origin main")

    except Exception as e:
        raise click.ClickException(f"Initialization failed: {str(e)}")
