from flask import Blueprint, render_template, session, redirect, url_for
from models import Cart
from extentions import db

cart_bp = Blueprint("cart_bp", __name__)

@cart_bp.route("/my_cart", methods=["GET"])
def cart():

    customer_id = session.get("customer_id")

    if not customer_id:
        return redirect(
            url_for("sign_in.sign_in")
        )

    cart_items = Cart.query.filter_by(
        customer_id=customer_id
    ).all()

    total_price = 0

    for cart_item in cart_items:

        print("================================")
        print("CART ID:", cart_item.id)
        print("CUSTOMER ID:", cart_item.customer_id)
        print("ITEM ID:", cart_item.item_id)
        print("QUANTITY:", cart_item.quantity)
        print("ITEM:", cart_item.item)

        if cart_item.item:

            print(
                "ITEM NAME:",
                cart_item.item.item_name
            )

            print(
                "ITEM PRICE:",
                cart_item.item.price
            )

            total_price += (
                float(cart_item.item.price)
                * cart_item.quantity
            )

    print("================================")
    print("TOTAL:", total_price)
    print("NUMBER OF CART ITEMS:", len(cart_items))
    print("================================")

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total_price=total_price
    )

@cart_bp.route("/remove_from_cart/<int:cart_id>", methods=["POST"])
def remove_from_cart(cart_id):

    customer_id = session.get("customer_id")

    if not customer_id:
        return redirect(url_for("sign_in.sign_in"))

    # Find only this customer's cart item
    cart_item = Cart.query.filter_by(id=cart_id,customer_id=customer_id).first()

    if not cart_item:
        return redirect(url_for("cart_bp.cart"))

    # Return the cart quantity back to stock
    cart_item.item.quantity += cart_item.quantity

    # Remove from cart
    db.session.delete(cart_item)
    db.session.commit()

    return redirect(url_for("cart_bp.cart"))
