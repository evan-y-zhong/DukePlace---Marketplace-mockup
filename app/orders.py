from flask import render_template, Blueprint
from flask_login import login_required, current_user
from flask import current_app as app
from datetime import datetime

bp = Blueprint("orders", __name__)


# render_template for order history
@bp.route("/orders")
@login_required
def history():
    orders = app.db.execute(
        """
    SELECT DISTINCT order_id, order_date, SUM(total_price) AS price, BOOL_AND(fulfilled) AS fulfilled
    FROM Orders
    WHERE buyer_id = :user_id
    GROUP BY order_id, order_date
    ORDER BY order_date DESC
    """,
        user_id=current_user.id,
    )

    return render_template("order_history.html", orders=orders)


# gets a certain order's details
@bp.route("/orders/<int:order_id>")
@login_required
def order_details(order_id):
    products = app.db.execute(
        """
    SELECT product_id, seller_id, seller_name, quantity, unit_price, total_price, fulfilled
    FROM Orders
    WHERE order_id = :order_id
    """,
        order_id=order_id,
    )

    return render_template("order_details.html", products=products, order_id=order_id)
