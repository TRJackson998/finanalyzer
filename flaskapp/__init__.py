"""
Flask App
=========
Flask web app interface for finance analyzer
"""

from pathlib import Path

# store auth in an instance folder
# https://flask.palletsprojects.com/en/3.0.x/config/#instance-folders
AUTH_PICKLE = Path(__file__).parent / "instance" / "auth.pkl"
AUTH_PICKLE.parent.mkdir(exist_ok=True)
