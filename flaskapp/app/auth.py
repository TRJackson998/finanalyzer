"""
Authentication
==============
Flask Blueprint for authentication page behaviour
"""

from pathlib import Path
from string import ascii_lowercase, ascii_uppercase, digits, punctuation

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from passlib.hash import sha256_crypt

from flaskapp.app.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


class AuthError(Exception):
    """Exception class to flash and log any auth error message"""

    def __init__(self, message: str = "Incorrect Username or Password") -> None:
        super().__init__()
        flash(message, "error")

        # write to log file
        current_app.logger.info("%s - %s", *(g.ip, message))


@bp.before_app_request
def load_logged_in_user():
    """
    Load user based on session if available,
    in order to skip over logging in step
    """
    user_id = session.get("user_id")
    g.ip = request.remote_addr

    if user_id is None:
        g.user = None
    else:
        # pull user from db
        db = get_db()
        this_user = db.execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        g.user = this_user["username"]


def validate_password(password: str) -> bool:
    """Raises an Authentication Exception if the password does not meet the requirements"""
    # not common requirement
    common_passwords = []
    with open(
        Path(__file__).parent.joinpath("static", "CommonPassword.txt"),
        "r",
        encoding="UTF-8",
    ) as common_file:
        for line in common_file.readlines():
            common_passwords.append(line.strip().lower())

    if password.strip().lower() in common_passwords:
        raise AuthError("Password must not be in commonly known password list.")

    # length requirement
    if len(password) < 12:
        raise AuthError(
            "Password is too short! It must be at least 12 characters long."
        )

    # character requirement
    lowercase = False
    uppercase = False
    digit = False
    special = False
    for char in password:
        if char in ascii_lowercase:
            lowercase = True
        if char in ascii_uppercase:
            uppercase = True
        if char in digits:
            digit = True
        if char in punctuation:
            special = True
    if not (lowercase and uppercase and digit and special):
        raise AuthError(
            "Password must include at least 1 uppercase character, "
            "1 lowercase character, 1 number and 1 special character"
        )


@bp.route("/register", methods=("GET", "POST"))
def register():
    """
    Load the register form html
    If request is a post, register the user
    """
    if request.method == "POST":
        try:
            # pull data from request form
            username = request.form["username"]
            password = request.form["password"]

            # check both fields are there
            if not username:
                raise AuthError("Username is required.")
            if not password:
                raise AuthError("Password is required.")

            validate_password(password)

            # hash the password
            password = sha256_crypt.hash(password)

            # add user to the database
            try:
                db = get_db()
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, password),
                )
                db.commit()
            except db.IntegrityError as e:
                raise AuthError(f"User {username} is already registered.") from e

            return redirect(url_for("auth.login"))

        except AuthError:
            # no need to do anything here, error already flashed
            pass

    # load register page html
    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """
    Load the login form html
    If request is a post, log in user
    Does not give descriptive error messages in order to avoid giving anything away to attackers
    """
    if request.method == "POST":
        try:
            # pull data from request form
            username = request.form["username"]
            password = request.form["password"]

            # pull user from db
            db = get_db()
            this_user = db.execute(
                "SELECT * FROM user WHERE username = ?", (username,)
            ).fetchone()

            if this_user is None:
                # this user doesn't exist in the db
                raise AuthError("User is none")
            if not sha256_crypt.verify(password, this_user["password"]):
                # password doesn't match
                raise AuthError("Pass doesn't match")

            # clear the session and set current user
            session.clear()
            session["user_id"] = this_user["id"]
            g.user = this_user["username"]
            g.ip = request.remote_addr

            # send user to landing page once logged in
            return redirect(url_for("routes.landing"))
        except AuthError:
            # no need to do anything here, error already flashed
            pass

    # load login page html
    return render_template("auth/login.html")


@bp.route("/update", methods=("GET", "POST"))
def update():
    """
    Load the update password form html
    If request is a post, update the user's password
    """
    if not g.user:
        # if not logged in
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        try:
            # pull data from request form
            password = request.form["password"]
            confirm = request.form["confirm"]

            # validate password meets requirements and is the same in both fields
            validate_password(password)
            if password != confirm:
                raise AuthError("New Password and Confirm Password fields must match")

            # get this user's current password
            # pull user from db
            db = get_db()
            this_user = db.execute(
                "SELECT * FROM user WHERE username = ?", (g.user,)
            ).fetchone()

            # verify it isn't the same
            if sha256_crypt.verify(password, this_user["password"]):
                raise AuthError("Cannot use same password.")

            # hash the password
            password = sha256_crypt.hash(password)

            # update this user in the auth pickle
            db.execute(
                "UPDATE user SET password = ? where username = ?",
                (
                    password,
                    g.user,
                ),
            )
            db.commit()

            # send feedback to the end user
            flash("Password successfully changed!", "info")
        except AuthError:
            # no need to do anything here, error already flashed/logged
            pass

    return render_template("auth/update.html")


@bp.route("/logout")
def logout():
    """Clear current session and send back to login page"""
    session.clear()
    return redirect(url_for("auth.login"))
