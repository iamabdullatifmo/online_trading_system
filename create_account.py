from flask import Blueprint,render_template,url_for,request,redirect,flash,session
from models import Customer
from extentions import mail,db
from flask_mail import Message
from werkzeug.security import generate_password_hash,check_password_hash


create_account_bp =Blueprint("create_account_bp",__name__)

@create_account_bp.route("/Create_account",methods=["POST","GET"])
def create_account():
    if request.method == "POST":
        f_name = request.form.get("f_name")
        l_name = request.form.get("l_name")
        username = f_name + " " + l_name
        email = request.form.get("email")
        password = request.form.get("password")

        hashed_password = generate_password_hash(password)

        email_check = Customer.query.filter_by(email=email).first()
        if email_check:
            flash("Email already exists.", "error")
            return render_template("create_account.html")
         
        customer = Customer(username=username, email=email, password=generate_password_hash(password))
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
        db.session.add(customer)
        db.session.commit()
        return redirect(url_for("items_bp.items"))
    return render_template("create_account.html")
