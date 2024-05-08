"""
Run App
=============
Script to run the Flask app in debug

Notes
-----
A lot of this project is based on the Flask tutorial:
Based on https://flask.palletsprojects.com/en/3.0.x/tutorial/
"""

from flaskapp.app import app

app.run(debug=True)
