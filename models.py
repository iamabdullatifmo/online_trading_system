from flask_sqlalchemy import SQLAlchemy
from extentions import mail,db


class Customer(db.Model):
    __tablename__ = "customer"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100))    
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))

class Items(db.Model):
    __tablename__ = "items"    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_name = db.Column(db.String(100))
    item_photo = db.Column(db.String(255))
    price = db.Column(db.Numeric(10, 2))
    quantity = db.Column(db.Integer)

class Cart(db.Model):
    __tablename__ = "cart"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer,db.ForeignKey("items.id"), nullable=False)
    quantity = db.Column(db.Integer,nullable=False,default=1)
    item = db.relationship("Items",backref="cart_items")
    customer_id = db.Column(db.Integer,db.ForeignKey("customer.id"),nullable=False)
    customer = db.relationship("Customer",backref="cart_items")
