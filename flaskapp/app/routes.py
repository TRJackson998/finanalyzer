"""
Routes
==============
Flask Blueprint for rendering non-auth routes
"""

from datetime import datetime

from flask import Blueprint, g, redirect, render_template, request, url_for

bp = Blueprint("routes", __name__)


@bp.before_request
def before_request():
    """Check if logged in first"""
    allowed_routes = ["routes.landing", "auth.login", "auth.register"]

    if not g.user and request.endpoint not in allowed_routes:
        # if not logged in, redirect to landing page
        return redirect(url_for("routes.landing"))


@bp.route("/")
def landing():
    """Renders landing page"""
    return render_template("routes/landing.html")


@bp.route("/dashboard")
def dashboard():
    """Renders dashboard page with today's date"""
    today_ = datetime.today()
    date_string = f"{today_.strftime(r'%B, %d %Y')} at {today_.strftime(r'%I:%M%p')}"
    return render_template(
        "routes/dashboard.html",
        current_datetime=date_string,
    )
