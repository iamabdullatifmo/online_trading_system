from flask import (
    Blueprint,
    render_template,
    request,
    session,
    url_for,
    redirect,
    jsonify
)

from models import Items, Cart
from extentions import db

items_bp = Blueprint("items_bp", __name__)


@items_bp.route("/items_bp", methods=["GET", "POST"])
def items():

    customer_id = session.get("customer_id")

    # User must be logged in
    if not customer_id:
        return redirect(url_for("sign_in.sign_in"))

    search = request.args.get("q", "").strip()

    # Get products
    if search:
        items = Items.query.filter(
            Items.item_name.ilike(f"%{search}%")
        ).all()
    else:
        items = Items.query.all()

    # ADD TO CART
    if request.method == "POST":

        item_id = request.form.get("item_id")
        cart_quantity = request.form.get("cart_quantity")

        if not item_id or not cart_quantity:
            return render_template(
                "shopping.html",
                items=items,
                error="Please select a quantity."
            )

        try:
            item_id = int(item_id)
            cart_quantity = int(cart_quantity)

        except ValueError:
            return render_template(
                "shopping.html",
                items=items,
                error="Invalid product or quantity."
            )

        selected_item = db.session.get(Items, item_id)

        if not selected_item:
            return render_template(
                "shopping.html",
                items=items,
                error="Product not found."
            )

        if cart_quantity <= 0:
            return render_template(
                "shopping.html",
                items=items,
                error="Quantity must be greater than zero."
            )

        if cart_quantity > selected_item.quantity:
            return render_template(
                "shopping.html",
                items=items,
                error=(
                    f"Only {selected_item.quantity} "
                    f"{selected_item.item_name} "
                    f"left in stock."
                )
            )

        existing_cart_item = Cart.query.filter_by(
            customer_id=customer_id,
            item_id=selected_item.id
        ).first()

        if existing_cart_item:
            existing_cart_item.quantity += cart_quantity

        else:
            new_cart_item = Cart(
                customer_id=customer_id,
                item_id=selected_item.id,
                quantity=cart_quantity
            )

            db.session.add(new_cart_item)

        selected_item.quantity -= cart_quantity

        db.session.commit()

        return redirect(url_for("cart_bp.cart"))

    return render_template("shopping.html", items=items)


# ==========================================
# GET PRODUCT DESCRIPTION
# ==========================================

@items_bp.route("/product/<int:item_id>/details", methods=["GET"])
def product_details():

    if not session.get("customer_id"):
        return jsonify({
            "success": False,
            "message": "Please log in to view product details."
        }), 401

    item_id = request.view_args["item_id"]

    selected_item = db.session.get(Items, item_id)

    if not selected_item:
        return jsonify({
            "success": False,
            "message": "Product not found."
        }), 404

    return jsonify({
        "success": True,
        "id": selected_item.id,
        "name": selected_item.item_name,
        "price": float(selected_item.price),
        "description": selected_item.description or "No description available for this product.",
        "quantity": selected_item.quantity,
        "image": url_for(
            "static",
            filename=selected_item.item_photo
        ) if selected_item.item_photo else None
    })