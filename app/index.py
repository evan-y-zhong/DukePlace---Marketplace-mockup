# app/index.py
from app.models.purchase import Purchase
from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user
import datetime

from .models.product import Product
from .models.user import User

from flask import Blueprint

bp = Blueprint("index", __name__)


# for the home page, render_template
@bp.route("/")
def index():
    search_query = request.args.get("search", "")
    category = request.args.get("category", "")
    sort_order = request.args.get("sort", "price_asc")
    search_type = request.args.get("search_type", "product")

    users = []
    products = []
    total_pages = 1
    current_page = 1
    page_range = []

    # Pagination setup
    page = request.args.get("page", 1, type=int)
    per_page = 9

    if search_type == "user":
        # Search for user by ID or name
        users = User.get_by_id_or_name(search_query)
        total_count = len(users)
        total_pages = (total_count + per_page - 1) // per_page

        # Adjust page range for pagination
        start = max(1, page - 2)
        end = min(total_pages, page + 2)
        if start > 1:
            page_range.extend([1, "..."] if start > 2 else [1])
        page_range.extend(range(start, end + 1))
        if end < total_pages:
            page_range.extend(
                ["...", total_pages] if end < total_pages - 1 else [total_pages]
            )

        # Paginate users
        users = users[(page - 1) * per_page : page * per_page]

        return render_template(
            "index.html",
            users=users,
            search_query=search_query,
            search_type=search_type,
            total_pages=total_pages,
            current_page=page,
            page_range=page_range,
        )

    # Get filtered products and total count for pagination
    products, total_count = Product.get_all_filtered(
        available=True,
        category=category,
        search_query=search_query,
        sort_order=sort_order,
        page=page,
        per_page=per_page,
    )
    total_pages = (total_count + per_page - 1) // per_page

    # Adjust page range for pagination
    start = max(1, page - 2)
    end = min(total_pages, page + 2)
    if start > 1:
        page_range.extend([1, "..."] if start > 2 else [1])
    page_range.extend(range(start, end + 1))
    if end < total_pages:
        page_range.extend(
            ["...", total_pages] if end < total_pages - 1 else [total_pages]
        )

    # Check if the user is authenticated to display purchase history
    purchases = None
    if current_user.is_authenticated:
        purchases = Purchase.get_all_by_uid_since(
            current_user.id, datetime.datetime(1980, 9, 14, 0, 0, 0)
        )

    return render_template(
        "index.html",
        avail_products=products,
        purchase_history=purchases,
        total_pages=total_pages,
        current_page=page,
        page_range=page_range,
        categories=Product.get_categories(),  # Assuming you have a method to get categories
        search_query=search_query,
        current_category=category,
        sort_order=sort_order,
        users=users,
        search_type=search_type,
    )


@bp.route("/seller_home")
def seller_home():
    return render_template("seller_home.html")
