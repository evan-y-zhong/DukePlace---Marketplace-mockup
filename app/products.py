import sys
from app.models.product import Product
from app.models.purchase import Purchase
from app.models.feedback import Feedback  # Import the Feedback model
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from flask_login import current_user, login_required
from datetime import datetime

from flask import Blueprint


bp = Blueprint("products", __name__)


# for milestone 3
@bp.route("/products", methods=["POST", "GET"])
@login_required
def get_top_k():
    # try:
    my_products = Product.get_by_creator(current_user.id)
    return render_template(
        "topk.html",
        avail_products=Product.get_all_filtered(),
        my_products=my_products,
        categories=Product.get_categories(),
    )
    # except Exception as e:
    # return render_template('topk.html', error=str(e), avail_products=Product.get_all_filtered())


# gets a certain product's information
@bp.route("/product/<int:id>")
def product(id):
    product = Product.get(id)
    if not product:
        return render_template(
            "product.html",
            product=None,
            average_rating=0,
            full_stars=0,
            half_star=0,
            empty_stars=5,
        )

    # ensures that the correct seller is selected
    sellers = Product.get_sellers(id)
    seller_details = [
        {"id": seller[0], "name": f"{seller[1]} {seller[2]}", "quantity": seller[3]}
        for seller in sellers
    ]

    user_feedback = None
    if current_user.is_authenticated:
        user_feedback = Feedback.get_by_user_and_product(current_user.id, id)

    # gets all feedback for the product
    all_feedback = Feedback.get_all_by_product(id)

    # corner case check, if the product doesn't have any, default to 0
    if all_feedback:
        average_rating = sum(feedback.rating for feedback in all_feedback) / len(
            all_feedback
        )
        average_rating = round(average_rating, 1)  # Round to one decimal place
        full_stars = int(average_rating // 1)
        half_star = 1 if (average_rating - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
    else:
        average_rating = 0
        full_stars = 0
        half_star = 0
        empty_stars = 5

    return render_template(
        "product.html",
        product=product,
        sellers=seller_details,
        user_feedback=user_feedback,
        all_feedback=all_feedback,
        len_all_feedback=len(all_feedback),
        average_rating=average_rating,
        full_stars=full_stars,
        half_star=half_star,
        empty_stars=empty_stars,
    )


# buy the product straight up, not used
@bp.route("/purchase/<int:pid>", methods=["POST"])
@login_required
def purchase_product(pid):
    product = Product.get(pid)
    Purchase.insert(uid=current_user.id, pid=pid)
    print(current_user.id, pid, file=sys.stderr)
    return redirect(url_for("products.product", id=pid))


# checks the purchase_history
@bp.route("/purchase_history")
@login_required
def purchase_history():
    num_purchases = Purchase.get_num_purchases_by_uid(current_user.id)

    # more pagination
    page = request.args.get("page", 1, type=int)
    per_page = 10
    total_pages = num_purchases // per_page + (
        1 if num_purchases % per_page != 0 else 0
    )
    page = max(1, min(page, total_pages))

    page_range = []
    start = max(1, page - 2)
    end = min(total_pages, page + 2)

    if start > 1:
        page_range.extend([1])
        if start > 2:
            page_range.append("...")

    page_range.extend(range(start, end + 1))

    if end < total_pages:
        if end < total_pages - 1:
            page_range.append("...")
        page_range.append(total_pages)

    purchases = Purchase.get_purchase_history_by_uid(current_user.id, page, per_page)

    return render_template(
        "purchase_history.html",
        purchase_history=purchases,
        total_pages=total_pages,
        current_page=page,
        page_range=page_range,
    )


# creates a product, used in /product page
@bp.route("/product/create", methods=["POST"])
@login_required
def create_product():
    name = request.form.get("name")
    desc = request.form.get("description")
    price = float(request.form.get("price"))
    category = request.form.get("category")
    image_url = request.form.get("image_url")

    try:
        success = Product.add_product(
            product_name=name,
            description=desc,
            creator_id=current_user.id,
            price=price,
            available=False,
            category=category,
            url=image_url,
        )
        if success:
            flash("Product added successfully!", "success")
        else:
            flash("Failed to add product. Please try again.", "danger")
    except Exception as e:
        # failure, show the error message
        flash(f"Error: {e}", "danger")

    return redirect(url_for("products.get_top_k"))


# edits a certain product on /product page
@bp.route("/product/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_product(id):
    product = Product.get(id)

    # ensure the product exists
    if not product or product.creator_id != current_user.id:
        flash("You are not authorized to edit this product.", "danger")
        return redirect(url_for("products.get_top_k"))

    if request.method == "POST":
        # get updated details from the form
        name = request.form.get("name")
        description = request.form.get("description")
        price = request.form.get("price")
        category = request.form.get("category")
        image_url = request.form.get("image_url")

        try:
            # update the product
            success = Product.update(
                id=id,
                name=name,
                description=description,
                price=price,
                category=category,
                image_url=image_url,
            )
            if success:
                flash("Product updated successfully!", "success")
            else:
                flash("Failed to update product. Please try again.", "danger")
        except Exception as e:
            flash(f"Error: {e}", "danger")

        return redirect(url_for("products.get_top_k"))

    return render_template("edit_product.html", product=product)


# DONT USE
# @bp.route('/browse')
# def browse_products():
#     search_query = request.args.get('search', '')
#     category = request.args.get('category', '')
#     sort_order = request.args.get('sort', 'price_asc')
#     page = request.args.get('page', 1, type=int)
#     per_page = 9
#     products, total_count = Product.get_all_filtered(available=True, category=category, search_query=search_query, sort_order=sort_order, page=page, per_page=per_page)
#     total_pages = (total_count + per_page - 1) // per_page  # Calculate total pages

#     return render_template('browse.html', products=products, total_pages=total_pages, current_page=page, categories=Product.get_categories(), search_query=search_query, current_category=category, sort_order=sort_order)
