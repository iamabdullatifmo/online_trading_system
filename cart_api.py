from flask import Blueprint, request, jsonify, session
from models import Cart, Items
from extentions import db

cart_api_bp = Blueprint("cart_api", __name__, url_prefix="/api/cart")

# GET CART
@cart_api_bp.route("", methods=["GET"])
def get_cart():

    customer_id = session.get("customer_id")

    if not customer_id:
        return jsonify({
            "success": False,
            "message": "Please sign in first."
        }), 401

    cart_items = Cart.query.filter_by(
        customer_id=customer_id
    ).all()

    items = []
    total_price = 0
    total_quantity = 0

    for cart_item in cart_items:

        subtotal = cart_item.item.price * cart_item.quantity

        total_price += subtotal
        total_quantity += cart_item.quantity

        items.append({
            "cart_id": cart_item.id,
            "item_id": cart_item.item.id,
            "item_name": cart_item.item.item_name,
            "price": float(cart_item.item.price),
            "quantity": cart_item.quantity,
            "stock_available": cart_item.item.quantity,
            "subtotal": float(subtotal),
            "photo": cart_item.item.item_photo
        })

    return jsonify({
        "success": True,
        "cart": items,
        "total_quantity": total_quantity,
        "total_price": float(total_price)
    })


# ADD ITEM TO CART
@cart_api_bp.route("/add", methods=["POST"])
def add_to_cart():

    customer_id = session.get("customer_id")

    if not customer_id:
        return jsonify({
            "success": False,
            "message": "Please sign in first."
        }), 401

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body is required."
        }), 400

    item_id = data.get("item_id")
    quantity = data.get("quantity", 1)

    try:
        item_id = int(item_id)
        quantity = int(quantity)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid item_id or quantity."
        }), 400

    if quantity <= 0:
        return jsonify({
            "success": False,
            "message": "Quantity must be greater than zero."
        }), 400

    item = Items.query.get(item_id)

    if not item:
        return jsonify({
            "success": False,
            "message": "Product not found."
        }), 404

    if item.quantity <= 0:
        return jsonify({
            "success": False,
            "message": "This product is out of stock."
        }), 400

    cart_item = Cart.query.filter_by(
        customer_id=customer_id,
        item_id=item_id
    ).first()

    if cart_item:

        new_quantity = cart_item.quantity + quantity

        if new_quantity > item.quantity:
            return jsonify({
                "success": False,
                "message": f"Only {item.quantity} available in stock.",
                "stock_available": item.quantity,
                "already_in_cart": cart_item.quantity
            }), 400

        cart_item.quantity = new_quantity

    else:

        if quantity > item.quantity:
            return jsonify({
                "success": False,
                "message": f"Only {item.quantity} available in stock.",
                "stock_available": item.quantity
            }), 400

        cart_item = Cart(
            customer_id=customer_id,
            item_id=item_id,
            quantity=quantity
        )

        db.session.add(cart_item)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Item added to cart.",
        "item_id": item.id,
        "quantity": cart_item.quantity
    }), 201


# UPDATE QUANTITY
@cart_api_bp.route("/update/<int:cart_id>", methods=["PUT"])
def update_cart(cart_id):

    customer_id = session.get("customer_id")

    if not customer_id:
        return jsonify({
            "success": False,
            "message": "Please sign in first."
        }), 401

    cart_item = Cart.query.filter_by(
        id=cart_id,
        customer_id=customer_id
    ).first()

    if not cart_item:
        return jsonify({
            "success": False,
            "message": "Cart item not found."
        }), 404

    data = request.get_json()

    if not data or "quantity" not in data:
        return jsonify({
            "success": False,
            "message": "Quantity is required."
        }), 400

    try:
        quantity = int(data["quantity"])
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid quantity."
        }), 400

    if quantity <= 0:
        return jsonify({
            "success": False,
            "message": "Quantity must be greater than zero."
        }), 400

    if quantity > cart_item.item.quantity:
        return jsonify({
            "success": False,
            "message": f"Only {cart_item.item.quantity} available in stock.",
            "stock_available": cart_item.item.quantity
        }), 400

    cart_item.quantity = quantity

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Cart quantity updated.",
        "cart_id": cart_item.id,
        "quantity": cart_item.quantity
    })


# REMOVE ITEM
@cart_api_bp.route("/remove/<int:cart_id>", methods=["DELETE"])
def remove_from_cart(cart_id):

    customer_id = session.get("customer_id")

    if not customer_id:
        return jsonify({
            "success": False,
            "message": "Please sign in first."
        }), 401

    cart_item = Cart.query.filter_by(
        id=cart_id,
        customer_id=customer_id
    ).first()

    if not cart_item:
        return jsonify({
            "success": False,
            "message": "Cart item not found."
        }), 404

    db.session.delete(cart_item)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Item removed from cart."
    })


# CLEAR CART
@cart_api_bp.route("/clear", methods=["DELETE"])
def clear_cart():

    customer_id = session.get("customer_id")

    if not customer_id:
        return jsonify({
            "success": False,
            "message": "Please sign in first."
        }), 401

    Cart.query.filter_by(
        customer_id=customer_id
    ).delete()

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Cart cleared."
    })
