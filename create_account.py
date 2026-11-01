
from flask import (
    Blueprint, render_template, url_for, request,
    redirect, flash, session, current_app
)
from models import Customer
from extentions import mail, db
from flask_mail import Message
from werkzeug.security import generate_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature


create_account_bp = Blueprint("create_account_bp", __name__)


# Generate a secure password-reset token
def generate_reset_token(customer):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    return serializer.dumps(
        {
            "email": customer.email,
            "password": customer.password
        },
        salt="password-reset-salt"
    )


# Verify the password-reset token
def verify_reset_token(token, max_age=3600):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    try:
        data = serializer.loads(
            token,
            salt="password-reset-salt",
            max_age=max_age
        )

        customer = Customer.query.filter_by(email=data["email"]).first()

        # Invalidate old tokens after the password changes
        if not customer or customer.password != data["password"]:
            return None

        return customer

    except (SignatureExpired, BadSignature, KeyError):
        return None


# CREATE ACCOUNT
@create_account_bp.route("/Create_account", methods=["POST", "GET"])
def create_account():

    if request.method == "POST":

        f_name = request.form.get("f_name", "").strip()
        l_name = request.form.get("l_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not f_name or not l_name or not email or not password:
            flash("Please complete all fields.", "error")
            return render_template("create_account.html")

        username = f_name + " " + l_name

        email_check = Customer.query.filter_by(email=email).first()

        if email_check:
            flash("Email already exists.", "error")
            return render_template("create_account.html")

        customer = Customer(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(customer)
        db.session.commit()

        session["customer_id"] = customer.id

        msg = Message(
            subject=f"Welcome {username}",
            sender="abdullatifmohammedyasir@gmail.com",
            recipients=[email]
        )

        msg.html = """
        <h1>Welcome to our online shopping system!</h1>
        <p>We are very happy to start trading with you.</p>
        """

        mail.send(msg)

        return redirect(url_for("items_bp.items"))

    return render_template("create_account.html")


# FORGOT PASSWORD
@create_account_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        customer = Customer.query.filter_by(email=email).first()

        # Use a generic response to avoid revealing registered emails
        if customer:

            token = generate_reset_token(customer)

            reset_link = url_for(
                "create_account_bp.reset_password",
                token=token,
                _external=True
            )

            msg = Message(
                subject="Password Reset Request",
                sender="abdullatifmohammedyasir@gmail.com",
                recipients=[customer.email]
            )

            msg.html = f"""
            <h2>Password Reset Request</h2>

            <p>We received a request to reset your password.</p>

            <p>Click the link below to create a new password:</p>

            <a href="{reset_link}">
                Reset My Password
            </a>

            <p>This link expires after one hour.</p>

            <p>If you did not request this, ignore this email.</p>
            """

            mail.send(msg)

        flash(
            "If an account exists with that email, a password-reset link has been sent.",
            "success"
        )

        return redirect(url_for("create_account_bp.forgot_password"))

    return render_template("forgot_password.html")


# RESET PASSWORD
@create_account_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):

    customer = verify_reset_token(token)

    if not customer:
        flash("This password-reset link is invalid or has expired.", "error")
        return redirect(url_for("create_account_bp.forgot_password"))

    if request.method == "POST":

        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not password or not confirm_password:
            flash("Please enter and confirm your new password.", "error")
            return render_template("reset_password.html", token=token)

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("reset_password.html", token=token)

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template("reset_password.html", token=token)

        customer.password = generate_password_hash(password)

        db.session.commit()

        flash("Your password has been reset successfully. You can now sign in.", "success")

        return redirect(url_for("sign_in.sign_in"))

    return render_template("reset_password.html", token=token)
