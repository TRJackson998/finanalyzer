"""
Portfolio Module Init
=====================
Initializes and configures the Flask app
Registers the auth and routes blueprints
"""

from pathlib import Path

from flask import Flask

from flaskapp.app import auth, db, routes

instance_path = Path(Path(__file__).parent, "instance")
instance_path.mkdir(exist_ok=True)

# create and configure the app
app_object = Flask(__name__, instance_path=instance_path, instance_relative_config=True)
app_object.config.from_mapping(
    SECRET_KEY="dev",
    DATABASE=Path(app_object.instance_path, "mydb.sqlite"),
)
app_object.app_context()

# blueprints
app_object.register_blueprint(auth.bp)
app_object.register_blueprint(routes.bp)

# db requires app context
with app_object.app_context():
    db.init_app()
    # db.init_db()
