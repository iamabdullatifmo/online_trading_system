from flask import Blueprint, render_template, request, flash, session, redirect, url_for
from models import Customer
from werkzeug.security import check_password_hash

sign_in_bp = Blueprint("sign_in", __name__)


@sign_in_bp.route("/Sign_in", methods=["GET", "POST"])
def sign_in():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Find customer
        customer = Customer.query.filter_by(
            email=email
        ).first()

        # Customer doesn't exist
        if not customer:

            flash(
                "Email does not exist.",
                "error"
            )

            return render_template(
                "sign_in.html"
            )

        # Check password
        if not check_password_hash(customer.password,password):

            flash("Password is incorrect.","error")
            return render_template("sign_in.html"  )

        # LOGIN SUCCESSFUL
        session.permanent = True

        session["customer_id"] = customer.id
        session["username"] = customer.username
        session["customer_email"] = customer.email

        # Go to shopping page
        return redirect(url_for("items_bp.items"))

    return render_template("sign_in.html")
