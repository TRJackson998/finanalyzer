"""
Portfolio Module Init
=====================
Initializes and configures the Flask app
Registers the auth and routes blueprints
"""

import os
from datetime import date
from logging.config import dictConfig
from pathlib import Path

from flask import Flask

from flaskapp.app import auth, db, routes

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            },
        },
        "handlers": {
            "file": {
                "level": "INFO",
                "formatter": "default",
                "class": "logging.FileHandler",
                "filename": f"{date.today()}.log",
                "mode": "a",
            },
        },
        "root": {"level": "INFO", "handlers": ["file"]},
    }
)


instance_path = Path(Path(__file__).parent, "instance")
instance_path.mkdir(exist_ok=True)

# create and configure the app
app_object = Flask(__name__, instance_path=instance_path, instance_relative_config=True)
app_object.config.from_mapping(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
    DATABASE=Path(app_object.instance_path, "mydb.sqlite"),
)

# blueprints
app_object.register_blueprint(auth.bp)
app_object.register_blueprint(routes.bp)

# db requires app context
with app_object.app_context():
    db.init_app()
    if not Path(app_object.config["DATABASE"]).exists():
        # init database if it doesn't already exist
        db.init_db()
