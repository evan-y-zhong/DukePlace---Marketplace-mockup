from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from .models.cart import Cart, CartItem
from .models.product import Product
from .models.user import User
from flask import Blueprint
from flask import current_app as app
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

bp = Blueprint("carts", __name__)


# render_template for cart
@bp.route("/cart")
@login_required
def cart():
    # get the cart for the current user
    cart = Cart.get_by_user_id(current_user.id)
    if cart is None:
        items = []
    else:
        # get all items in the cart
        items = CartItem.get_by_cart_id(cart.id)

    cart_items = []
    total_amount = 0.0
    for item in items:
        product = Product.get(item.product_id)
        if product:
            # calculate the total amount for the cart
            total_amount += float(item.total_price)
            cart_items.append(
                {
                    "cart_item_id": item.id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "seller_name": item.seller_name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.total_price),
                }
            )

    coupon_code = request.args.get("coupon_code")
    discount = 0.0
    if coupon_code:
        # apply the coupon code if provided
        discount, error = Cart.apply_coupon(cart.id, coupon_code)
        if error:
            flash(error, "danger")
        elif discount > 0:
            discount = float(discount)

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total_amount=total_amount,
        discount=discount,
        applied_coupon_code=coupon_code,
    )


# add a product to the cart
@bp.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    seller_id = request.form.get("seller_id", type=int)
    seller_name = request.form.get("seller_name", type=str)
    seller_quantity = app.db.execute(
        """
SELECT quantity
FROM Inventory
WHERE seller_id=:seller_id AND product_id=:product_id
""",
        seller_id=seller_id,
        product_id=product_id,
    )[0][0]

    quantity = request.form.get("quantity", type=int)

    if not seller_quantity or seller_quantity < quantity:
        flash("Seller stock is too low")
        return redirect(url_for("products.product", id=product_id))

    if seller_id is None or not seller_name:
        flash("Please select a seller")
        return redirect(url_for("carts.cart"))
    if quantity is None or quantity <= 0:
        flash("Invalid quantity")
        return redirect(url_for("carts.cart"))

    product = Product.get(product_id)

    # not available -> return error
    if product is None or not product.available:
        flash("Product not found or not available")
        return redirect(url_for("carts.cart"))

    cart = Cart.get_by_user_id(current_user.id)

    # if the user doesn't have a cart, create it
    if cart is None:
        cart = Cart.create(current_user.id)
    existing_items = app.db.execute(
        """
SELECT id, quantity
FROM Cart_Items
WHERE cart_id = :cart_id AND product_id = :product_id AND seller_id=:seller_id
""",
        cart_id=cart.id,
        product_id=product_id,
        seller_id=seller_id,
    )

    # update, else add the item
    if existing_items:
        existing_item_id = existing_items[0][0]
        new_quantity = existing_items[0][1] + quantity
        total_price = new_quantity * product.price
        CartItem.update_quantity(existing_item_id, new_quantity, total_price)
    else:
        CartItem.add_item(
            cart.id, product_id, seller_id, seller_name, quantity, product.price
        )

    flash("Item added to cart", "success")
    return redirect(url_for("carts.cart"))


# checkout the cart
@bp.route("/cart/checkout", methods=["POST"])
@login_required  # ensure, prevents going back and accessing cart
def checkout():
    cart = Cart.get_by_user_id(current_user.id)

    # if doesn't have cart or items, then it is empty
    if not cart:
        flash("Your cart is empty.", "danger")
        return redirect(url_for("carts.cart"))

    items = CartItem.get_by_cart_id(cart.id)
    if not items:
        flash("Your cart is empty.", "danger")
        return redirect(url_for("carts.cart"))

    # sums the total price of all the items for the UI
    total_amount = float(sum(item.total_price for item in items))
    discount = float(request.form.get("discount", 0.0))

    # coupons
    coupon_code = request.form.get("coupon_code")
    discount_value = 0
    if coupon_code:
        # ensures coupon works
        discount_value, error = Cart.apply_coupon(cart.id, coupon_code)
        if error:
            flash(error, "danger")
            return redirect(url_for("carts.cart"))
        if discount > 0:
            total_amount -= discount

    # insufficient balance
    if current_user.balance < total_amount:
        flash("Insufficient funds, please top up balance.", "danger")
        return redirect(url_for("carts.cart"))

    order_id = app.db.execute("SELECT COALESCE(MAX(order_id), 0) + 1 FROM Orders")[0][0]
    order_date = datetime.now(timezone.utc)

    total_final_price = 0.0
    inventory_adjustment_message = ""

    for item in items:
        quantity = app.db.execute(
            """
        SELECT quantity
        FROM Inventory
        WHERE product_id = :product_id AND seller_id = :seller_id
        """,
            product_id=item.product_id,
            seller_id=item.seller_id,
        )

        if not quantity:
            flash("Product does not exist", "danger")
            return redirect(url_for("carts.cart"))

        available_quantity = quantity[0][0]

        if available_quantity < item.quantity:
            quantity_to_buy = available_quantity
            remaining_message = f"Inventory decreased since cart add, remaining inventory ({available_quantity} items) has been purchased."
        else:
            quantity_to_buy = item.quantity
            remaining_message = ""

        if quantity_to_buy == 0:
            flash(
                "Inventory decreased since cart add, item is now out of stock", "danger"
            )
            return redirect(url_for("carts.cart"))

        unit_price = float(item.unit_price)
        total_price = quantity_to_buy * unit_price

        app.db.execute(
            """
        INSERT INTO Orders (order_id, order_date, product_id, buyer_id, seller_id, seller_name, quantity, unit_price, total_price, fulfilled)
        VALUES (:order_id, :order_date, :product_id, :buyer_id, :seller_id, :seller_name, :quantity, :unit_price, :total_price, :fulfilled)
        """,
            order_id=order_id,
            order_date=order_date,
            product_id=item.product_id,
            buyer_id=current_user.id,
            seller_id=item.seller_id,
            seller_name=item.seller_name,
            quantity=quantity_to_buy,
            unit_price=unit_price,
            total_price=quantity_to_buy * float(item.unit_price)
            - float(discount_value),
            fulfilled=False,
        )

        app.db.execute(
            """
        UPDATE Inventory
        SET quantity = quantity - :quantity
        WHERE product_id = :product_id AND seller_id = :seller_id
        """,
            quantity=quantity_to_buy,
            product_id=item.product_id,
            seller_id=item.seller_id,
        )

        total_final_price += total_price

        if remaining_message:
            inventory_adjustment_message += f" {remaining_message}"

    total_final_price = max(0, total_final_price - discount)  # apply discount
    current_user.balance -= Decimal(total_final_price).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    app.db.execute(
        "UPDATE Users SET balance = :balance WHERE id = :user_id",
        balance=current_user.balance,
        user_id=current_user.id,
    )

    # clear cart
    CartItem.clear_cart(cart.id)

    # update the balance history so it reflects in the balance history graph
    User.update_balance_history(current_user.id)

    flash(
        f"Order successfully placed! Total: ${total_final_price:.2f} (Discount: ${discount:.2f})",
        "success",
    )
    if inventory_adjustment_message:
        flash(inventory_adjustment_message, "info")

    return redirect(url_for("orders.history"))


# apply a coupon to the cart
@bp.route("/cart/apply_coupon", methods=["POST"])
@login_required
def apply_coupon():
    # checks for any errors
    cart = Cart.get_by_user_id(current_user.id)
    if not cart:
        flash("Cart not found.", "danger")
        return redirect(url_for("carts.cart"))

    coupon_code = request.form.get("coupon_code")
    if not coupon_code:
        flash("Please provide a coupon code.", "danger")
        return redirect(url_for("carts.cart"))

    discount, error = Cart.apply_coupon(cart.id, coupon_code)
    if error:
        flash(error, "danger")
        return redirect(url_for("carts.cart"))

    flash(f"Coupon applied! Discount: ${discount:.2f}", "success")
    return redirect(url_for("carts.cart", coupon_code=coupon_code))


# remove an item from the cart
@bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_from_cart(item_id):
    cart = Cart.get_by_user_id(current_user.id)
    if not cart:
        flash("Cart not found.", "danger")
        return redirect(url_for("carts.cart"))

    item = app.db.execute(
        """
SELECT id
FROM Cart_Items
WHERE id = :item_id AND cart_id = :cart_id
""",
        item_id=item_id,
        cart_id=cart.id,
    )

    if not item:
        flash("Item not found in your cart.", "danger")
        return redirect(url_for("carts.cart"))

    app.db.execute(
        """
DELETE FROM Cart_Items
WHERE id = :item_id
""",
        item_id=item_id,
    )

    flash("Item removed from cart.", "success")
    return redirect(url_for("carts.cart"))


# render the change quantity page
@bp.route("/cart/change_quantity/<int:item_id>", methods=["GET"])
@login_required
def change_quantity_page(item_id):
    cart = Cart.get_by_user_id(current_user.id)
    if not cart:
        flash("Cart not found.", "danger")
        return redirect(url_for("carts.cart"))
    cart_item = app.db.execute(
        """
SELECT *
FROM Cart_Items
WHERE id = :item_id AND cart_id = :cart_id
""",
        item_id=item_id,
        cart_id=cart.id,
    )[0]
    if not cart_item:
        flash("Item not found in your cart.", "danger")
        return redirect(url_for("carts.cart"))

    return render_template("change_quantity.html", item=cart_item)


# update the quantity of an item in the cart
@bp.route("/cart/update_quantity/<int:item_id>", methods=["POST"])
@login_required
def update_quantity(item_id):
    cart = Cart.get_by_user_id(current_user.id)
    if not cart:
        flash("Cart not found.", "danger")
        return redirect(url_for("carts.cart"))
    cart_item = app.db.execute(
        """
SELECT *
FROM Cart_Items
WHERE id = :item_id AND cart_id = :cart_id
""",
        item_id=item_id,
        cart_id=cart.id,
    )[0]

    # copy pasted from above, juts makes sure that user has a cart and that the cart has items
    if not cart_item:
        flash("Item not found in your cart.", "danger")
        return redirect(url_for("carts.cart"))

    new_quantity = request.form.get("quantity", type=int)
    if new_quantity <= 0:
        flash("Quantity must be greater than zero.", "danger")
        return redirect(url_for("carts.change_quantity_page", item_id=item_id))

    product = Product.get(cart_item.product_id)
    if not product or not product.available:
        flash("Product not available.", "danger")
        return redirect(url_for("carts.cart"))

    stock = app.db.execute(
        """
SELECT quantity
FROM Inventory
WHERE seller_id = :seller_id AND product_id = :product_id
""",
        seller_id=cart_item.seller_id,
        product_id=cart_item.product_id,
    )

    if not stock or stock[0][0] < new_quantity:
        flash("Insufficient stock for the requested quantity.", "danger")
        return redirect(url_for("carts.change_quantity_page", item_id=item_id))

    total_price = new_quantity * product.price
    CartItem.update_quantity(cart_item.id, new_quantity, total_price)

    flash("Quantity updated successfully!", "success")
    return redirect(url_for("carts.cart"))
