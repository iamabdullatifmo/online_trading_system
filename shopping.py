
from flask import Flask, session, url_for, redirect
from dotenv import load_dotenv
from extentions import mail, db
import os
from datetime import timedelta

# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

secret_key = os.getenv("SECRET_KEY")
database_url = os.getenv("DATABASE_URL")
email = os.getenv("MAIL_USERNAME")
password = os.getenv("MAIL_PASSWORD")

# Import blueprints
from sign_in import sign_in_bp
from create_account import create_account_bp
from items import items_bp
from cart import cart_bp
from cart_api import cart_api_bp
from admin import admin_bp
from payment import payment_bp

# Static directory
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(
    __name__,
    static_folder=STATIC_DIR,
    static_url_path="/static"
)

# Application configuration
app.config["SECRET_KEY"] = secret_key
app.permanent_session_lifetime = timedelta(days=200)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = database_url

# Flask-Mail configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
app.config["MAIL_USERNAME"] = email
app.config["MAIL_PASSWORD"] = password
app.config["MAIL_DEFAULT_SENDER"] = email
app.config["MAIL_TIMEOUT"] = 30

# Register blueprints
app.register_blueprint(sign_in_bp)
app.register_blueprint(create_account_bp)
app.register_blueprint(items_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(cart_api_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(payment_bp)

# Initialize extensions
db.init_app(app)
mail.init_app(app)

@app.route("/")
def home():
    customer_id = session.get("customer_id")

    if customer_id:
        return redirect(url_for("items_bp.items"))

    return redirect(url_for("sign_in.sign_in"))


# Create database tables
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
