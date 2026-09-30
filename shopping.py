from flask import Flask, render_template,session,url_for,flash,redirect
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from extentions import mail,db
import os
from werkzeug.security import generate_password_hash

load_dotenv()

secret_key = os.getenv("SECRET_KEY")
database_url = os.getenv("DATABASE_URL")
email = os.getenv("MAIL_USERNAME")
password = os.getenv("MAIL_PASSWORD")


from sign_in import sign_in_bp
from create_account import create_account_bp
from items import items_bp
from cart import cart_bp
from cart_api import cart_api_bp
from admin import admin_bp
from payment import payment_bp



#To find the images directoriers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask( __name__,
    static_folder=STATIC_DIR,
    static_url_path="/static"
)

from datetime import timedelta


app.config["SECRET_KEY"] = secret_key
app.permanent_session_lifetime = timedelta(days=200)


app.register_blueprint(sign_in_bp,url_prefix="")
app.register_blueprint(create_account_bp,url_prefix="")
app.register_blueprint(items_bp,url_prefix="")
app.register_blueprint(cart_bp,url_prefix="")
app.register_blueprint(cart_api_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(payment_bp)


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = database_url

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", "False").lower() == "true"

db.init_app(app)
mail.init_app(app)


@app.route("/")
def home():

    customer_id = session.get("customer_id")

    if customer_id:
        return redirect(url_for("items_bp.items"))

    return redirect(url_for("sign_in.sign_in"))
    
   # return render_template("create_account.html")
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)