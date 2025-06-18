from flask import render_template, Blueprint, redirect, url_for, flash
from flask_login import login_required, current_user
from flask import current_app as app
from datetime import datetime

bp = Blueprint("sellerorders", __name__)


# route to show all orders for the seller
@bp.route("/seller/orders")
@login_required
def seller_orders():
    orders = app.db.execute(
        """
    SELECT o.order_id, o.order_date, o.product_id, u.firstname || ' ' || u.lastname AS buyer_name, o.total_price
    FROM Orders o
    JOIN Users u ON o.buyer_id = u.id
    WHERE o.seller_id = :user_id AND o.fulfilled = FALSE
    ORDER BY o.order_date DESC
    """,
        user_id=current_user.id,
    )

    return render_template("seller_orders.html", orders=orders)


# fulfill an order
@bp.route("/seller/fulfill_order/<int:order_id>/<int:product_id>", methods=["POST"])
@login_required
def fulfill_order(order_id, product_id):
    # get the order details
    order = app.db.execute(
        """
    SELECT * FROM Orders WHERE order_id = :order_id AND seller_id = :user_id AND product_id = :product_id
    """,
        order_id=order_id,
        user_id=current_user.id,
        product_id=product_id,
    )

    if order:
        # mark the order as fulfilled
        app.db.execute(
            """
        UPDATE Orders SET fulfilled = TRUE WHERE order_id = :order_id AND seller_id = :seller_id AND product_id = :product_id
        """,
            order_id=order_id,
            seller_id=current_user.id,
            product_id=product_id,
        )

        # add the order total to the seller's balance
        app.db.execute(
            """
        UPDATE Users SET balance = balance + :amount WHERE id = :user_id
        """,
            amount=order[0][9],
            user_id=current_user.id,
        )

    flash("Order fulfilled", "success")
    return redirect(url_for("sellerorders.seller_orders"))
