"""Smoke tests for CLI CRUD command registration."""

import pytest


class TestAccountsCRUD:
    """Verify accounts command group has all CRUD subcommands."""

    def test_accounts_commands_registered(self):
        from bagels.cli.accounts import accounts

        cmd_names = [c.name for c in accounts.commands.values()]
        assert "list" in cmd_names
        assert "show" in cmd_names
        assert "add" in cmd_names
        assert "update" in cmd_names
        assert "delete" in cmd_names

    def test_accounts_add_has_name_option(self):
        from bagels.cli.accounts import accounts

        add_cmd = accounts.commands["add"]
        param_names = [p.name for p in add_cmd.params]
        assert "name" in param_names
        assert "balance" in param_names

    def test_accounts_delete_has_cascade(self):
        from bagels.cli.accounts import accounts

        delete_cmd = accounts.commands["delete"]
        param_names = [p.name for p in delete_cmd.params]
        assert "cascade" in param_names
        assert "force" in param_names


class TestCategoriesCRUD:
    """Verify categories command group has all CRUD subcommands."""

    def test_categories_commands_registered(self):
        from bagels.cli.categories import categories

        cmd_names = [c.name for c in categories.commands.values()]
        assert "tree" in cmd_names
        assert "list" in cmd_names
        assert "show" in cmd_names
        assert "add" in cmd_names
        assert "update" in cmd_names
        assert "delete" in cmd_names

    def test_categories_add_has_nature_option(self):
        from bagels.cli.categories import categories

        add_cmd = categories.commands["add"]
        param_names = [p.name for p in add_cmd.params]
        assert "name" in param_names
        assert "nature" in param_names

    def test_categories_delete_has_cascade(self):
        from bagels.cli.categories import categories

        delete_cmd = categories.commands["delete"]
        param_names = [p.name for p in delete_cmd.params]
        assert "cascade" in param_names
        assert "force" in param_names


class TestPersonsCRUD:
    """Verify persons command group has all CRUD subcommands."""

    def test_persons_commands_registered(self):
        from bagels.cli.persons import persons

        cmd_names = [c.name for c in persons.commands.values()]
        assert "list" in cmd_names
        assert "show" in cmd_names
        assert "add" in cmd_names
        assert "update" in cmd_names
        assert "delete" in cmd_names

    def test_persons_registered_in_cli(self):
        from bagels.__main__ import cli

        assert "persons" in cli.commands

    def test_persons_delete_has_cascade(self):
        from bagels.cli.persons import persons

        delete_cmd = persons.commands["delete"]
        param_names = [p.name for p in delete_cmd.params]
        assert "cascade" in param_names
        assert "force" in param_names


class TestTemplatesCRUD:
    """Verify templates command group has all CRUD subcommands."""

    def test_templates_commands_registered(self):
        from bagels.cli.templates import templates

        cmd_names = [c.name for c in templates.commands.values()]
        assert "list" in cmd_names
        assert "show" in cmd_names
        assert "add" in cmd_names
        assert "update" in cmd_names
        assert "delete" in cmd_names

    def test_templates_registered_in_cli(self):
        from bagels.__main__ import cli

        assert "templates" in cli.commands

    def test_templates_add_has_required_options(self):
        from bagels.cli.templates import templates

        add_cmd = templates.commands["add"]
        param_names = [p.name for p in add_cmd.params]
        assert "label" in param_names
        assert "amount" in param_names
        assert "account_id" in param_names


class TestRecordsCRUD:
    """Verify records command group has all CRUD subcommands."""

    def test_records_commands_registered(self):
        from bagels.cli.records import records

        cmd_names = [c.name for c in records.commands.values()]
        assert "list" in cmd_names
        assert "show" in cmd_names
        assert "add" in cmd_names
        assert "update" in cmd_names
        assert "delete" in cmd_names

    def test_records_add_has_inline_options(self):
        from bagels.cli.records import records

        add_cmd = records.commands["add"]
        param_names = [p.name for p in add_cmd.params]
        assert "yaml" in param_names
        assert "label" in param_names
        assert "amount" in param_names
        assert "date" in param_names
        assert "account_id" in param_names

    def test_records_update_has_identifier(self):
        from bagels.cli.records import records

        update_cmd = records.commands["update"]
        param_names = [p.name for p in update_cmd.params]
        assert "identifier" in param_names

    def test_records_delete_has_force(self):
        from bagels.cli.records import records

        delete_cmd = records.commands["delete"]
        param_names = [p.name for p in delete_cmd.params]
        assert "identifier" in param_names
        assert "force" in param_names
