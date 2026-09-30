import os

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from models import Items, Admin
from extentions import db


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# CONFIGURATION
ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "avif"
}



def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ADMIN CHECK
def admin_required():

    admin_id = session.get("admin_id")

    print("ADMIN ID FROM SESSION:", admin_id)
    print("IS ADMIN FROM SESSION:", session.get("is_admin"))

    if not admin_id:
        print("NO ADMIN ID - ACCESS DENIED")
        return False

    admin = Admin.query.get(admin_id)

    if not admin:
        print("ADMIN NOT FOUND IN DATABASE")

        session.pop("admin_id", None)
        session.pop("is_admin", None)
        session.pop("admin_username", None)

        return False

    print("ADMIN VERIFIED:", admin.admin_name)

    return True


@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():

    print("\n================================")
    print("ADMIN LOGIN ROUTE CALLED")
    print("METHOD:", request.method)
    print("================================")

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        print("USERNAME ENTERED:", username)
        print("PASSWORD PROVIDED:", bool(password))

        # ==============================
        # CHECK FORM
        # ==============================

        if not username or not password:

            print("LOGIN FAILED: Username or password missing")

            flash(
                "Username and password are required.",
                "error"
            )

            return render_template("admin_login.html")


        # ==============================
        # FIND ADMIN
        # ==============================

        admin = Admin.query.filter_by(
            admin_name=username
        ).first()

        print("ADMIN FOUND:", admin is not None)

        if not admin:

            print("LOGIN FAILED: Admin does not exist")

            flash(
                "Invalid admin username or password.",
                "error"
            )

            return render_template("admin_login.html")


        # ==============================
        # ADMIN DATABASE INFORMATION
        # ==============================

        print("ADMIN ID FROM DATABASE:", admin.id)
        print("ADMIN USERNAME FROM DATABASE:", admin.admin_name)
        print("ADMIN PASSWORD HASH EXISTS:", bool(admin.password))


        # ==============================
        # VERIFY PASSWORD
        # ==============================

        password_correct = check_password_hash(
            admin.password,
            password
        )

        print("PASSWORD CORRECT:", password_correct)

        if not password_correct:

            print("LOGIN FAILED: Incorrect password")

            flash(
                "Invalid admin username or password.",
                "error"
            )

            return render_template("admin_login.html")


        # ==============================
        # CREATE ADMIN SESSION
        # ==============================

        session["admin_id"] = admin.id
        session["is_admin"] = True
        session["admin_username"] = admin.admin_name


        # ==============================
        # VERIFY SESSION
        # ==============================

        print("\n================================")
        print("ADMIN LOGIN SUCCESSFUL")
        print("ADMIN ID:", admin.id)
        print("SESSION ADMIN ID:", session.get("admin_id"))
        print("SESSION IS ADMIN:", session.get("is_admin"))
        print("SESSION ADMIN USERNAME:", session.get("admin_name"))
        print("FULL SESSION:", dict(session))
        print("================================\n")


        flash(
            "Admin login successful.",
            "success"
        )

        return redirect(
            url_for("admin.dashboard")
        )


    print("GET REQUEST - SHOWING ADMIN LOGIN PAGE")

    return render_template("admin_login.html")

# ADMIN DASHBOARD
@admin_bp.route("/", methods=["GET"])
def dashboard():

    if not admin_required():
        return redirect(url_for("sign_in.sign_in"))

    items = Items.query.order_by(Items.id.desc()).all()

    return render_template(
        "admin_management.html",
        items=items
    )


# ADD PRODUCT
@admin_bp.route("/products/add", methods=["POST"])
def add_product():
    
    print("================================")
    print("ADD PRODUCT ROUTE CALLED")
    print("FORM:", request.form)
    print("FILES:", request.files)
    print("================================")
    if not admin_required():
        return redirect(url_for("sign_in.sign_in"))

    item_name = request.form.get("item_name", "").strip()
    price = request.form.get("price", "").strip()
    quantity = request.form.get("quantity", "").strip()

    image = request.files.get("item_photo")


    # VALIDATE TEXT FIELDS
    if not item_name:
        flash("Product name is required.", "error")
        return redirect(url_for("admin.dashboard"))

    if not price:
        flash("Product price is required.", "error")
        return redirect(url_for("admin.dashboard"))

    if not quantity:
        flash("Product quantity is required.", "error")
        return redirect(url_for("admin.dashboard"))


    # CONVERT VALUES
    try:
        price = float(price)
        quantity = int(quantity)

    except ValueError:
        flash("Price or quantity is invalid.", "error")
        return redirect(url_for("admin.dashboard"))


    if price < 0:
        flash("Price cannot be negative.", "error")
        return redirect(url_for("admin.dashboard"))


    if quantity < 0:
        flash("Stock quantity cannot be negative.", "error")
        return redirect(url_for("admin.dashboard"))


    # CHECK IMAGE
    if not image or image.filename == "":
        flash("Please select a product image.", "error")
        return redirect(url_for("admin.dashboard"))


    if not allowed_file(image.filename):
        flash(
            "Invalid image format. Use PNG, JPG, JPEG, GIF or WEBP.",
            "error"
        )
        return redirect(url_for("admin.dashboard"))


    # CREATE UPLOAD DIRECTORY
    upload_folder = os.path.join(
        "static",
        "uploads"
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )


    # SAVE IMAGE
    filename = secure_filename(image.filename)

    # Prevent duplicate filenames
    base, extension = os.path.splitext(filename)

    counter = 1

    while os.path.exists(
        os.path.join(upload_folder, filename)
    ):

        filename = f"{base}_{counter}{extension}"
        counter += 1


    image.save(
        os.path.join(
            upload_folder,
            filename
        )
    )


    # SAVE PRODUCT TO DATABASE
    new_item = Items(
        item_name=item_name,
        price=price,
        quantity=quantity,
        item_photo=f"uploads/{filename}"
    )

    db.session.add(new_item)
    db.session.commit()


    flash(
        f"{item_name} was added successfully.",
        "success"
    )

    return redirect(
        url_for("admin.dashboard")
    )


# DELETE PRODUCT
@admin_bp.route("/products/delete/<int:item_id>", methods=["POST"])
def delete_product(item_id):

    if not admin_required():
        return redirect(url_for("sign_in.sign_in"))


    item = Items.query.get(item_id)

    if not item:
        flash("Product not found.", "error")
        return redirect(url_for("admin.dashboard"))


    # DELETE IMAGE
    if item.item_photo:

        image_path = os.path.join(
            "static",
            item.item_photo
        )

        if os.path.exists(image_path):
            os.remove(image_path)


    # DELETE DATABASE RECORD
    db.session.delete(item)
    db.session.commit()


    flash(
        f"{item.item_name} was deleted.",
        "success"
    )

    return redirect(
        url_for("admin.dashboard")
    )


# EDIT PRODUCT
@admin_bp.route("/products/edit/<int:item_id>", methods=["GET", "POST"])
def edit_product(item_id):

    if not admin_required():
        return redirect(url_for("sign_in.sign_in"))


    item = Items.query.get(item_id)

    if not item:
        flash("Product not found.", "error")
        return redirect(url_for("admin.dashboard"))


    # GET
    if request.method == "GET":

        return render_template(
            "admin_edit.html",
            item=item
        )


    # POST
    item_name = request.form.get(
        "item_name",
        ""
    ).strip()

    price = request.form.get(
        "price",
        ""
    ).strip()

    quantity = request.form.get(
        "quantity",
        ""
    ).strip()

    image = request.files.get(
        "item_photo"
    )


    if not item_name:
        flash("Product name is required.", "error")
        return redirect(
            url_for("admin.edit_product",item_id=item.id) )


    try:

        price = float(price)
        quantity = int(quantity)

    except ValueError:

        flash("Invalid price or quantity.", "error")

        return redirect(
            url_for("admin.edit_product",item_id=item.id))


    if price < 0 or quantity < 0:

        flash("Price and quantity cannot be negative.","error")

        return redirect(
            url_for("admin.edit_product",item_id=item.id))


    # UPDATE BASIC INFORMATION
    item.item_name = item_name
    item.price = price
    item.quantity = quantity


    # REPLACE IMAGE IF NEW IMAGE WAS PROVIDED
    if image and image.filename:

        if not allowed_file(image.filename):

            flash("Invalid image format.", "error")

            return redirect(
                url_for("admin.edit_product",item_id=item.id ))

        upload_folder = os.path.join("static","uploads")

        os.makedirs(upload_folder,exist_ok=True)

        filename = secure_filename(image.filename)
        base, extension = os.path.splitext(filename)

        counter = 1

        while os.path.exists(
            os.path.join(upload_folder,filename)):

            filename = (f"{base}_{counter}{extension}")

            counter += 1


        image.save(
            os.path.join(upload_folder,filename))

        # Delete old image
        if item.item_photo:

            old_image = os.path.join("static",item.item_photo)

            if os.path.exists(old_image):
               os.remove(old_image)

        item.item_photo = (f"uploads/{filename}")


    db.session.commit()


    flash("Product updated successfully.","success")


    return redirect(url_for("admin.dashboard"))
