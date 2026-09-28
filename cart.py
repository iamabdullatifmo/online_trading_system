from flask import Blueprint, render_template,session
from models import Cart

cart_bp = Blueprint("cart_bp", __name__)

@cart_bp.route("/my_cart", methods=["GET"])
def cart():

    customer_id = session.get("customer_id")

    cart_items = Cart.query.filter_by(customer_id=customer_id).all()
    total_price = 0

    for cart_item in cart_items:

        total_price += (cart_item.item.price * cart_item.quantity)

    return render_template("cart.html",cart_items=cart_items,total_price=total_price)
