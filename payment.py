import os
import secrets
import requests

from dotenv import load_dotenv

from flask import (
    Blueprint,
    session,
    redirect,
    url_for,
    flash,
    render_template,
    request
)

from models import Cart, Order, OrderItem
from extentions import db


# ==========================================
# LOAD .ENV
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

load_dotenv(
    os.path.join(BASE_DIR, ".env")
)


# ==========================================
# PAYMENT BLUEPRINT
# ==========================================

payment_bp = Blueprint(
    "payment",
    __name__,
    url_prefix="/payment"
)


# ==========================================
# PAYSTACK CONFIGURATION
# ==========================================

PAYSTACK_SECRET_KEY = os.getenv(
    "PAYSTACK_SECRET_KEY"
)

PAYSTACK_INITIALIZE_URL = (
    "https://api.paystack.co/transaction/initialize"
)

PAYSTACK_VERIFY_URL = (
    "https://api.paystack.co/transaction/verify/"
)


# ==========================================
# START PAYMENT
# ==========================================

@payment_bp.route("/pay", methods=["GET"])
def pay():

    # --------------------------------------
    # CHECK PAYSTACK SECRET KEY
    # --------------------------------------

    if not PAYSTACK_SECRET_KEY:

        flash(
            "Paystack secret key is not configured.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # CHECK CUSTOMER LOGIN
    # --------------------------------------

    customer_id = session.get(
        "customer_id"
    )

    if not customer_id:

        flash(
            "Please sign in before making a payment.",
            "error"
        )

        return redirect(
            url_for("sign_in.sign_in")
        )


    # --------------------------------------
    # GET CUSTOMER EMAIL
    # --------------------------------------

    customer_email = session.get(
        "customer_email"
    )

    if not customer_email:

        flash(
            "Customer email was not found. "
            "Please sign in again.",
            "error"
        )

        return redirect(
            url_for("sign_in.sign_in")
        )


    # --------------------------------------
    # GET CUSTOMER CART
    # --------------------------------------

    cart_items = Cart.query.filter_by(
        customer_id=customer_id
    ).all()


    if not cart_items:

        flash(
            "Your cart is empty.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # CALCULATE CART TOTAL
    # --------------------------------------

    total_price = 0

    for cart_item in cart_items:

        item = cart_item.item

        if not item:

            flash(
                "A product in your cart "
                "no longer exists.",
                "error"
            )

            return redirect(
                url_for("cart_bp.cart")
            )

        total_price += (
            float(item.price)
            * cart_item.quantity
        )


    # --------------------------------------
    # CONVERT GHS TO PESEWAS
    # --------------------------------------

    amount = int(
        round(total_price * 100)
    )


    if amount <= 0:

        flash(
            "Invalid payment amount.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # GENERATE 10 CHARACTER REFERENCE
    # --------------------------------------
    #
    # 5 random bytes = 10 hexadecimal
    # characters.
    #
    # Example:
    # A7F39B20C1
    #
    # --------------------------------------

    reference = secrets.token_hex(
        5
    ).upper()


    # --------------------------------------
    # PAYSTACK HEADERS
    # --------------------------------------

    headers = {

        "Authorization":
            f"Bearer {PAYSTACK_SECRET_KEY}",

        "Content-Type":
            "application/json"
    }


    # --------------------------------------
    # PAYMENT DATA
    # --------------------------------------

    data = {

        "email":
            customer_email,

        "amount":
            amount,

        "currency":
            "GHS",

        "reference":
            reference,

        "callback_url":
            url_for(
                "payment.payment_callback",
                _external=True
            ),

        "metadata": {

            "customer_id":
                str(customer_id),

            "payment_reference":
                reference
        }
    }


    # --------------------------------------
    # INITIALIZE PAYSTACK PAYMENT
    # --------------------------------------

    try:

        response = requests.post(

            PAYSTACK_INITIALIZE_URL,

            json=data,

            headers=headers,

            timeout=30
        )

        result = response.json()


    except requests.RequestException:

        flash(
            "Unable to connect to Paystack. "
            "Please try again.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    except ValueError:

        flash(
            "Paystack returned an invalid response.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # CHECK PAYSTACK RESPONSE
    # --------------------------------------

    if not result.get("status"):

        error_message = result.get(
            "message",
            "Unable to initialize payment."
        )

        flash(
            error_message,
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # GET PAYSTACK CHECKOUT URL
    # --------------------------------------

    payment_data = result.get(
        "data",
        {}
    )

    authorization_url = payment_data.get(
        "authorization_url"
    )


    if not authorization_url:

        flash(
            "Paystack did not return a payment URL.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # SAVE PAYMENT INFORMATION
    # --------------------------------------

    session["payment_reference"] = (
        reference
    )

    session["payment_amount"] = (
        amount
    )


    # --------------------------------------
    # SEND CUSTOMER TO PAYSTACK
    # --------------------------------------

    return redirect(
        authorization_url
    )


# ==========================================
# PAYSTACK CALLBACK
# ==========================================

@payment_bp.route("/callback")
def payment_callback():

    # --------------------------------------
    # CHECK CUSTOMER LOGIN
    # --------------------------------------

    customer_id = session.get("customer_id")

    if not customer_id:

        flash(
            "Your payment session has expired. "
            "Please sign in again.",
            "error"
        )

        return redirect(
            url_for("sign_in.sign_in")
        )


    # --------------------------------------
    # CHECK PAYSTACK SECRET KEY
    # --------------------------------------

    if not PAYSTACK_SECRET_KEY:

        flash(
            "Paystack secret key is not configured.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # GET PAYMENT REFERENCE
    # --------------------------------------

    reference = request.args.get("reference")

    if not reference:

        flash(
            "Payment reference was not received.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # CHECK SAVED REFERENCE
    # --------------------------------------

    saved_reference = session.get(
        "payment_reference"
    )

    if saved_reference != reference:

        flash(
            "Invalid payment reference.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # PAYSTACK VERIFY HEADERS
    # --------------------------------------

    headers = {
        "Authorization":
            f"Bearer {PAYSTACK_SECRET_KEY}"
    }


    # --------------------------------------
    # VERIFY PAYMENT WITH PAYSTACK
    # --------------------------------------

    try:

        response = requests.get(
            PAYSTACK_VERIFY_URL + reference,
            headers=headers,
            timeout=30
        )

        result = response.json()

    except requests.RequestException:

        flash(
            "Unable to verify payment with Paystack.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )

    except ValueError:

        flash(
            "Paystack returned an invalid "
            "verification response.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # CHECK PAYSTACK RESPONSE
    # --------------------------------------

    if not result.get("status"):

        flash(
            result.get(
                "message",
                "Payment verification failed."
            ),
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    transaction = result.get(
        "data",
        {}
    )


    # --------------------------------------
    # CHECK PAYMENT STATUS
    # --------------------------------------

    if transaction.get("status") != "success":

        flash(
            "Payment was not successful.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # VERIFY PAYMENT REFERENCE
    # --------------------------------------

    if transaction.get("reference") != reference:

        flash(
            "Payment reference verification failed.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # VERIFY PAYMENT AMOUNT
    # --------------------------------------

    expected_amount = session.get(
        "payment_amount"
    )

    paid_amount = transaction.get(
        "amount"
    )

    if expected_amount != paid_amount:

        flash(
            "Payment amount could not be verified.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # GET CUSTOMER CART
    # --------------------------------------

    cart_items = Cart.query.filter_by(
        customer_id=customer_id
    ).all()


    if not cart_items:

        flash(
            "Your cart is empty.",
            "error"
        )

        return redirect(
            url_for("items_bp.items")
        )


    # --------------------------------------
    # VERIFY STOCK BEFORE CHANGING DATABASE
    # --------------------------------------

    for cart_item in cart_items:

        item = cart_item.item

        if not item:

            flash(
                "A product in your cart "
                "no longer exists.",
                "error"
            )

            return redirect(
                url_for("cart_bp.cart")
            )


        if cart_item.quantity > item.quantity:

            flash(
                "Payment succeeded, but there "
                "is not enough stock for one "
                "of your items.",
                "error"
            )

            return redirect(
                url_for("cart_bp.cart")
            )


    # --------------------------------------
    # CREATE ORDER
    # --------------------------------------

    order = Order(
        customer_id=customer_id,
        payment_reference=reference,
        amount=paid_amount,
        status="paid"
    )

    db.session.add(order)

    # Get the generated order ID
    db.session.flush()


    # --------------------------------------
    # SAVE PURCHASED ITEMS
    # --------------------------------------

    purchased_items = []


    for cart_item in cart_items:

        item = cart_item.item


        # Save item information for
        # payment_success.html

        purchased_items.append({

            "item_id": item.id,

            "quantity": cart_item.quantity,

            "price": float(item.price)

        })


        # Create order item

        order_item = OrderItem(

            order_id=order.id,

            item_id=item.id,

            quantity=cart_item.quantity,

            price=item.price

        )

        db.session.add(order_item)


    # --------------------------------------
    # REDUCE PRODUCT STOCK
    # --------------------------------------

    for cart_item in cart_items:

        cart_item.item.quantity -= (
            cart_item.quantity
        )


    # --------------------------------------
    # REMOVE ITEMS FROM CART
    # --------------------------------------

    for cart_item in cart_items:

        db.session.delete(
            cart_item
        )


    # --------------------------------------
    # SAVE EVERYTHING
    # --------------------------------------

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Payment was successful, but "
            "your order could not be completed.",
            "error"
        )

        return redirect(
            url_for("cart_bp.cart")
        )


    # --------------------------------------
    # CLEAR PAYMENT SESSION
    # --------------------------------------

    session.pop(
        "payment_reference",
        None
    )

    session.pop(
        "payment_amount",
        None
    )


    # --------------------------------------
    # PAYMENT SUCCESSFUL
    # --------------------------------------

    return render_template(

        "payment_success.html",

        reference=reference,

        amount=paid_amount,

        order_id=order.id,

        purchased_items=purchased_items
    )
