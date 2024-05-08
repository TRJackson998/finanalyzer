"""
DB
==
SQLite Database connection

Notes
-----
https://flask.palletsprojects.com/en/3.0.x/tutorial/database/
"""

import sqlite3

import click
from flask import current_app, g


def get_db():
    """Init database connection"""
    if "db" not in g:

        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(_=None):
    """Close database connection"""
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """Initializes the db using the schema.sql file"""
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app():
    """Initialize app w/db functions"""
    current_app.teardown_appcontext(close_db)
    current_app.cli.add_command(init_db_command)
