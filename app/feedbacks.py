import sys
from flask import render_template, redirect, url_for, flash, request
from flask import current_app as app
from flask_login import login_required, current_user
from datetime import datetime

from .models.feedback import Feedback
from .models.seller_review import SellerReview

from flask import Blueprint

bp = Blueprint("feedbacks", __name__)


# fetch and display the 5 most recent feedbacks for a given user
@bp.route("/user/feedback", methods=["GET", "POST"])
@login_required
def get_feedback():
    user_id = request.form.get("user_id") or request.args.get("user_id")

    # pagination
    num_feedback = Feedback.get_all_feedback_by_user(user_id)
    page = request.args.get("page", 1, type=int)

    # more for pagination, ceil divide to make sure that all products get shown
    per_page = 5
    total_pages = num_feedback // per_page + (1 if num_feedback % per_page != 0 else 0)
    page = max(1, min(page, total_pages))

    page_range = []
    start = max(1, page - 2)
    end = min(total_pages, page + 2)

    if start > 1:
        page_range.extend([1])
        if start > 2:
            page_range.append("...")

    # extends pages if not enough
    page_range.extend(range(start, end + 1))

    if end < total_pages:
        if end < total_pages - 1:
            page_range.append("...")
        page_range.append(total_pages)

    recent_feedback = Feedback.get_recent_feedback_by_user(user_id, per_page, page)

    return render_template(
        "feedback.html",
        feedback_list=recent_feedback,
        user_id=user_id,
        current_page=page,
        page_range=page_range,
        total_pages=total_pages,
    )


# get current user's feedback
@bp.route("/feedback", methods=["GET"])
@login_required
def get_my_feedback():
    user_feedback = Feedback.get_feedback_by_user_id(current_user.id)
    return render_template("feedback_list.html", feedback=user_feedback)


@bp.route("/product/<int:product_id>/feedback", methods=["POST"])
@login_required
def add_or_update_feedback(product_id):
    rating = request.form.get("rating", type=int)
    comment = request.form.get("comment")

    # add and update is the same method, check the method for more details
    Feedback.add_or_update_feedback(current_user.id, product_id, rating, comment)
    flash("Feedback submitted successfully.")
    return redirect(url_for("products.product", id=product_id))


@bp.route("/product/<int:product_id>/feedback/delete", methods=["POST"])
@login_required
def delete_feedback(product_id):
    Feedback.delete_feedback(current_user.id, product_id)
    flash("Feedback removed successfully.")
    return redirect(url_for("products.product", id=product_id))


@bp.route("/user/<int:seller_id>/review", methods=["POST"])
@login_required
def add_or_update_seller_review(seller_id):
    rating = request.form.get("rating", type=int)
    comment = request.form.get("comment")

    has_ordered = (
        app.db.execute(
            """
    SELECT COUNT(*) 
    FROM Orders 
    WHERE buyer_id = :user_id AND seller_id = :seller_id
    """,
            user_id=current_user.id,
            seller_id=seller_id,
        )[0][0]
        > 0
    )

    # makes sure that user has bought from this seller
    if not has_ordered:
        flash("You can only review sellers you have purchased from.", "danger")
        return redirect(url_for("users.public_view", user_id=seller_id))

    SellerReview.add_or_update_review(current_user.id, seller_id, rating, comment)
    flash("Seller review submitted successfully.")
    return redirect(url_for("users.public_view", user_id=seller_id))


@bp.route("/seller/<int:seller_id>/review/delete", methods=["POST"])
@login_required
def delete_seller_review(seller_id):
    SellerReview.delete_review(current_user.id, seller_id)
    flash("Seller review removed successfully.")
    return redirect(url_for("users.public_view", user_id=seller_id))
