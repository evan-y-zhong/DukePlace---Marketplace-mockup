from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask import Blueprint
from flask import current_app as app
from app.models.InventoryItem import InventoryItem
from app.models.product import Product

bp = Blueprint("inventory", __name__)


@bp.route("/inv", methods=["GET", "POST"])
@login_required
def inventory():
    # display and manage the logged-in user's inventory
    if request.method == "POST":
        # check if the user is creating a new product
        if request.form.get("action") == "create_product":
            product_name = request.form.get("name")
            description = request.form.get("description")
            price = request.form.get("price", type=float)
            quantity = request.form.get("quantity", type=int)
            available = True
            category = request.form.get("category")
            url = request.form.get("image_url")

            if not all([product_name, description, price, available, category]):
                flash("Please fill out all fields to create a new product.", "danger")
                return redirect(url_for("inventory.inventory"))

            success = Product.add_product(
                product_name,
                description,
                current_user.id,
                price,
                available,
                category,
                url,
            )
            if not success:
                flash("Failed to create product. It may already exist.", "danger")
                return redirect(url_for("inventory.inventory"))

            # add product to inventory
            product_id = Product.get_by_name(product_name)
            if product_id == -1:
                flash("Error adding product to inventory.", "danger")
            else:
                added_to_inventory = InventoryItem.add_item(
                    current_user.id, product_id, quantity
                )
                if added_to_inventory:
                    flash("Product created and added to inventory.", "success")
                else:
                    flash(
                        "Product created but could not be added to inventory.", "danger"
                    )

            return redirect(url_for("inventory.inventory"))

        # handle adding an existing product to inventory
        elif request.form.get("action") == "add_to_inventory":
            product_name = request.form.get("name")
            quantity = request.form.get("quantity", type=int)

            if not product_name or quantity is None or quantity <= 0:
                flash("Invalid product name or quantity.")
                return redirect(url_for("inventory.inventory"))

            product_id = Product.get_by_name(product_name)
            if product_id == -1:
                flash("Product does not exist.", "danger")
            else:
                success = InventoryItem.add_item(current_user.id, product_id, quantity)
                if not success:
                    flash("This product is already in your inventory.", "danger")
                else:
                    app.db.execute(
                        """UPDATE Products SET available = :available WHERE id=:pid""",
                        available=True,
                        pid=product_id,
                    )
                    flash("Product added to inventory.", "success")

        return redirect(url_for("inventory.inventory"))

    # fetch all inventory items for the current user
    items = InventoryItem.get_by_seller_id(current_user.id)
    inventory_items = [
        {
            "image_url": InventoryItem.get_image(item.product_id),
            "id": item.id,
            "product_id": item.product_id,
            "product_name": Product.get(item.product_id).name,
            "quantity": item.quantity,
        }
        for item in items
    ]

    return render_template(
        "inventory.html",
        inventory_items=inventory_items,
        categories=Product.get_categories(),
    )


@bp.route("/inventory/<int:product_id>", methods=["GET", "POST"])
@login_required
def manage_product(product_id):
    """Manage an individual product in the user's inventory."""
    if request.method == "POST":
        # check if this is a DELETE request
        if request.form.get("_method") == "DELETE":
            # remove product from inventory
            success = InventoryItem.remove_item(current_user.id, product_id)
            if success:
                flash("Product removed from inventory.", "success")
            else:
                flash("Failed to remove product.", "danger")
            return redirect(url_for("inventory.inventory"))

        # handle as a regular POST request
        quantity = request.form.get("quantity", type=int)
        if quantity is None or quantity < 0:
            flash("Invalid quantity.")
            return redirect(url_for("inventory.inventory"))

        success = InventoryItem.update_quantity(current_user.id, product_id, quantity)
        if success:
            flash("Product quantity updated.", "success")
        else:
            flash("Failed to update product quantity.", "danger")

        return redirect(url_for("inventory.inventory"))

    # fetch product details for the GET request
    product = Product.get(product_id)
    if not product:
        flash("Product not found.")
        return redirect(url_for("inventory.inventory"))

    item = InventoryItem.get_by_product_id(current_user.id, product_id)
    if not item:
        flash("Product not found in your inventory.")
        return redirect(url_for("inventory.inventory"))

    return render_template("manage_product.html", product=product, inventory_item=item)
