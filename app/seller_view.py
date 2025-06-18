from flask import render_template, request
from flask_login import current_user

from .models.product import Product
from .models.sellers import Sellers

from flask import Blueprint

bp = Blueprint("seller_view", __name__)


# gets the seller information and their products
@bp.route("/seller", methods=["GET", "POST"])
def seller_products():
    products = []
    seller_id = None
    page = request.args.get("page", 1, type=int)
    per_page = 10
    total_pages = 1
    page_range = [0, 1]

    # if trying to post to /seller
    if request.method == "POST":
        seller_id = request.form.get("seller_id")
        if seller_id:
            total_products = Sellers.get_product_count_by_seller(seller_id)
            total_pages = (total_products // per_page) + (
                1 if total_products % per_page > 0 else 0
            )

            page = max(1, min(page, total_pages))

            products = Sellers.get_products_by_seller_id(
                seller_id, page=page, per_page=per_page
            )

            # pagination
            page_range = []
            start = max(1, page - 2)
            end = min(total_pages, page + 2)

            if start > 1:
                page_range.append(1)
                if start > 2:
                    page_range.append("...")

            page_range.extend(range(start, end + 1))

            if end < total_pages:
                if end < total_pages - 1:
                    page_range.append("...")
                page_range.append(total_pages)

    if request.method == "GET":
        seller_id = request.args.get("seller_id")
        if seller_id:
            total_products = Sellers.get_product_count_by_seller(seller_id)
            total_pages = (total_products // per_page) + (
                1 if total_products % per_page > 0 else 0
            )
            products = Sellers.get_products_by_seller_id(
                seller_id, page=page, per_page=per_page
            )

            # pagination
            page_range = []
            start = max(1, page - 2)
            end = min(total_pages, page + 2)

            if start > 1:
                page_range.append(1)
                if start > 2:
                    page_range.append("...")

            page_range.extend(range(start, end + 1))

            if end < total_pages:
                if end < total_pages - 1:
                    page_range.append("...")
                page_range.append(total_pages)

    return render_template(
        "sellers.html",
        products=products,
        seller_id=seller_id,
        total_pages=total_pages,
        current_page=page,
        page_range=page_range,
    )
