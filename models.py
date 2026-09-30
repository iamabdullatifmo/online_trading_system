from flask_sqlalchemy import SQLAlchemy
from extentions import mail,db
from datetime import datetime

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

class Admin(db.Model):
    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_name = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer,db.ForeignKey("customer.id"),nullable=False)
    payment_reference = db.Column(db.String(100),unique=True,nullable=False)
    amount = db.Column(db.Integer,nullable=False)
    status = db.Column(db.String(50),default="paid",nullable=False)
    created_at = db.Column(db.DateTime,default=datetime.utcnow)
    items = db.relationship("OrderItem",backref="order",lazy=True)


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer,db.ForeignKey("orders.id"),nullable=False)
    item_id = db.Column(db.Integer,db.ForeignKey("items.id"),nullable=False)
    quantity = db.Column(db.Integer,nullable=False)
    price = db.Column(db.Numeric(10, 2),nullable=False)
    item = db.relationship("Items",backref="order_items")

