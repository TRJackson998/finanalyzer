"""
Authentication
==============
Flask Blueprint for authentication page behaviour
"""

from datetime import datetime
from pathlib import Path
from string import ascii_lowercase, ascii_uppercase, digits, punctuation

import pandas as pd
from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)
from passlib.hash import sha256_crypt

from flaskapp import AUTH_PICKLE

bp = Blueprint("auth", __name__, url_prefix="/auth")


class AuthError(Exception):
    """Exception class to flash and log any auth error message"""

    def __init__(self, message: str = "Incorrect Username or Password") -> None:
        super().__init__()
        flash(message, "error")

        # write to log file
        with open(
            Path(__file__).parent.parent.joinpath("instance", "log.txt"),
            "a",
            encoding="UTF-8",
        ) as log_file:
            log_file.writelines(f"{datetime.today().strftime(r"%d/%m/%Y | %H:%M:%S")}"
                                " | IP {g.ip} | {message}\n")


@bp.before_app_request
def load_logged_in_user():
    """
    Load user based on session if available,
    in order to skip over logging in step
    """
    user_id = session.get("user_id")
    g.ip = request.remote_addr

    if user_id is None or not AUTH_PICKLE.exists():
        g.user = None
    else:
        auth_df: pd.DataFrame = pd.read_pickle(AUTH_PICKLE)
        g.user = auth_df.iloc[user_id, :]["Username"]


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

            # read pre-existing auth pickle into df, or create new df
            auth_df = (
                pd.read_pickle(AUTH_PICKLE)
                if AUTH_PICKLE.exists()
                else pd.DataFrame(columns=["Username", "Password"])
            )

            # check if username already in auth pickle
            if username in auth_df.loc[:, "Username"].tolist():
                raise AuthError(f"User {username} is already registered.")

            # add user/pass to auth pickle
            auth_df = pd.concat(
                [
                    auth_df,
                    pd.DataFrame(
                        {"Username": username, "Password": password},
                        index=[len(auth_df)],
                    ),
                ],
            )
            pd.to_pickle(auth_df, AUTH_PICKLE)

            # redirect to login page
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

            # if no auth pickle, no users have been registered
            if not AUTH_PICKLE.exists():
                raise AuthError()

            # pull this user from the auth pickle
            auth_df: pd.DataFrame = pd.read_pickle(AUTH_PICKLE)
            this_user = auth_df.loc[auth_df["Username"] == username]

            if not this_user.empty:
                # pull username and password fields
                _user = this_user["Username"].iloc[0]
                _pass = this_user["Password"].iloc[0]
            else:
                # this user doesn't exist in the auth pickle
                raise AuthError()

            if _user is None:
                # no username for this user
                raise AuthError()
            if not sha256_crypt.verify(password, _pass):
                # password doesn't match
                raise AuthError()

            # clear the session and set current user
            session.clear()
            user_index = int(this_user.index.values[0])
            session["user_id"] = user_index
            g.user = auth_df.iloc[user_index, :]["Username"]
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
            auth_df: pd.DataFrame = pd.read_pickle(AUTH_PICKLE)
            current_password = auth_df.loc[auth_df["Username"] == g.user, "Password"].values[0]

            # verify it isn't the same
            if sha256_crypt.verify(password, current_password):
                raise AuthError("Cannot use same password.")

            # hash the password
            password = sha256_crypt.hash(password)

            # update this user in the auth pickle
            auth_df.loc[auth_df["Username"] == g.user, "Password"] = password
            pd.to_pickle(auth_df, AUTH_PICKLE)

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
