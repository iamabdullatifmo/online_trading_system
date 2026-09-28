from flask import Blueprint, render_template, request,session,url_for,redirect
from models import Items,Cart
from extentions import db

items_bp = Blueprint("items_bp", __name__)

@items_bp.route("/items_bp", methods=["GET", "POST"])
def items():
    customer_id = session.get("customer_id")
    if not customer_id:
     return redirect(url_for("sign_in.sign_in"))
    search = request.args.get("q", "").strip()

    if search:
        items = Items.query.filter(
            Items.item_name.ilike(f"%{search}%")
        ).all()
    else:
        items = Items.query.all()

      # Add item to cart
    if request.method == "POST":
        item_id = request.form.get("item_id")
        cart_quantity = request.form.get("cart_quantity")

        # VALIDATE INPUT
        if not item_id or not cart_quantity:
            return render_template("shopping.html",items=items,
                error="Please select a quantity.")
        try:
            item_id = int(item_id)
            cart_quantity = int(cart_quantity)

        except ValueError:
            return render_template("shopping.html",items=items,
                error="Invalid product or quantity.")

        # FIND PRODUCT
        selected_item = Items.query.get(item_id)

        if not selected_item:
            return render_template("shopping.html",items=items,error="Product not found.")

        # VALIDATE QUANTITY
        if cart_quantity <= 0:
            return render_template("shopping.html",items=items,
                error="Quantity must be greater than zero.")

        # When you try to select more than the qauntity of the item
        if cart_quantity > selected_item.quantity:
            return render_template("shopping.html",items=items,
                error=(
                    f"Only {selected_item.quantity} "
                    f"{selected_item.item_name} "
                    f"left in stock."))

        # CHECK EXISTING CART ITEM
        existing_cart_item = Cart.query.filter_by(customer_id=customer_id,item_id=selected_item.id, ).first()

        if existing_cart_item:
            # Quantity already in cart
            new_quantity = (existing_cart_item.quantity + cart_quantity)

            # Check that combined quantity
            # doesn't exceed available stock
            if new_quantity > selected_item.quantity:

                return render_template("shopping.html",items=items,
                    error=(
                        f"You already have "
                        f"{existing_cart_item.quantity} "
                        f"in your cart. "
                        f"Only {selected_item.quantity} "
                        f"available." ))

            # Update cart quantity
            existing_cart_item.quantity = new_quantity

        else:
            # CREATE NEW CART ITEM
            new_cart_item = Cart(customer_id=customer_id,item_id=selected_item.id,quantity=cart_quantity)
            db.session.add(new_cart_item)

        # REDUCE STOCK
        selected_item.quantity -= cart_quantity

        # SAVE DATABASE
        db.session.commit()

        # GO DIRECTLY TO CART
        return redirect(url_for("cart_bp.cart"))

    # SHOW PRODUCTS
    return render_template("shopping.html",items=items)