from flask import Blueprint, render_template, request, session, url_for, redirect
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

        # Validate input
        if not item_id or not cart_quantity:
            return render_template("shopping.html",items=items,
                error="Please select a quantity.")

        try:
            item_id = int(item_id)
            cart_quantity = int(cart_quantity)

        except ValueError:
            return render_template("shopping.html",items=items,
                error="Invalid product or quantity.")

        # Find product
        selected_item = Items.query.get(item_id)

        if not selected_item:
            return render_template("shopping.html",items=items,
                error="Product not found.")

        # Validate quantity
        if cart_quantity <= 0:
            return render_template("shopping.html",items=items,
                error="Quantity must be greater than zero.")

        # Check stock
        if cart_quantity > selected_item.quantity:
            return render_template("shopping.html",items=items,
                error=(
                    f"Only {selected_item.quantity} "
                    f"{selected_item.item_name} "
                    f"left in stock."))

        # Check if product is already in this customer's cart
        existing_cart_item = Cart.query.filter_by(customer_id=customer_id,item_id=selected_item.id).first()

        if existing_cart_item:
            # Increase existing cart quantity
            existing_cart_item.quantity += cart_quantity

        else:
            # Create new cart item
            new_cart_item = Cart(customer_id=customer_id,item_id=selected_item.id,quantity=cart_quantity)

            db.session.add(new_cart_item)

        # Reduce available stock
        selected_item.quantity -= cart_quantity
        # Save
        db.session.commit()

        # Go to cart
        return redirect(url_for("cart_bp.cart"))

    # Show products
    return render_template("shopping.html",items=items)
