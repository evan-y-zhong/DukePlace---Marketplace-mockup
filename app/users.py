from app.models.feedback import Feedback
from app.models.sellers import Sellers
from app.models.seller_review import SellerReview
from flask import render_template, redirect, url_for, flash, request, jsonify
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Optional

from .models.user import User
from .models.purchase import Purchase

from flask import Blueprint

bp = Blueprint("users", __name__)


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


# login, pre-made
@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_auth(form.email.data, form.password.data)
        if user is None:
            flash("Invalid email or password")
            return redirect(url_for("users.login"))
        login_user(user)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("index.index")

        return redirect(next_page)
    return render_template("login.html", title="Sign In", form=form)


# template class
class RegistrationForm(FlaskForm):
    firstname = StringField("First Name", validators=[DataRequired()])
    lastname = StringField("Last Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

    def validate_email(self, email):
        if User.email_exists(email.data):
            raise ValidationError("Already a user with this email.")


# template class
class EditProfileForm(FlaskForm):
    firstname = StringField("First Name", validators=[DataRequired()])
    lastname = StringField("Last Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("New Password", validators=[Optional()])
    password2 = PasswordField(
        "Repeat Password", validators=[Optional(), EqualTo("password")]
    )
    address = StringField("Address", validators=[DataRequired()])
    submit = SubmitField("Update Profile")


# try to register, return error if wrong
@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.register(
            form.email.data, form.password.data, form.firstname.data, form.lastname.data
        ):
            flash("Congratulations, you are now a registered user!")
            return redirect(url_for("users.login"))
    return render_template("register.html", title="Register", form=form)


# logout route
@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index.index"))


# increase balance by some value, WILL DO +/- x in-place
@bp.route("/top_up", methods=["POST"])
@login_required
def top_up():
    amount = request.form.get("amount", type=float)
    if amount is None or amount <= 0:
        flash("Invalid amount")
        return redirect(url_for("users.profile"))
    if User.update_balance(current_user.id, amount):
        flash("Balance topped up successfully")
    else:
        flash("Failed to top up balance")
    return redirect(url_for("users.profile"))


# withdraw balance by some value, WILL DO +/- x in-place
@bp.route("/withdraw", methods=["POST"])
@login_required
def withdraw():
    amount = request.form.get("amount", type=float)
    if amount is None or amount <= 0:
        flash("Invalid amount")
        return redirect(url_for("users.profile"))
    if current_user.balance < amount:
        flash("Insufficient balance")
        return redirect(url_for("users.profile"))
    if User.update_balance(current_user.id, -amount):
        flash("Balance withdrawn successfully")
    else:
        flash("Failed to withdraw balance")
    return redirect(url_for("users.profile"))


# gets the profile information
@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        # validate the form before submitting
        password = form.password.data if form.password.data else None
        if User.update_profile(
            current_user.id,
            form.firstname.data,
            form.lastname.data,
            form.email.data,
            password,
            form.address.data,
        ):
            flash("Your profile has been updated.")
            return redirect(url_for("users.profile"))
        else:
            flash("That email is already in use. Try logging in.")
    elif request.method == "GET":
        # put the information into the form
        form.firstname.data = current_user.firstname
        form.lastname.data = current_user.lastname
        form.email.data = current_user.email
        form.address.data = current_user.address

    # fetch data for visualizations
    balance_history = User.get_balance_history(current_user.id)
    spending_by_category = Purchase.get_spending_by_category(current_user.id)
    purchases_by_category = Purchase.get_purchases_by_category(current_user.id)

    return render_template(
        "profile.html",
        title="Profile",
        form=form,
        balance_history=balance_history,
        spending_by_category=spending_by_category,
        purchases_by_category=purchases_by_category,
    )


# the public view for a user, shows different information
@bp.route("/user/<int:user_id>")
def public_view(user_id):
    user = User.get(user_id)
    if not user:
        return render_template("public_view.html", user=None)

    is_seller = user.is_seller
    reviews = SellerReview.get_all_by_seller(user_id)

    if reviews:
        average_rating = sum(review.rating for review in reviews) / len(reviews)
        average_rating = round(average_rating, 1)  # round to one decimal place
        full_stars = int(average_rating // 1)
        half_star = 1 if (average_rating - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
    else:
        average_rating = 0
        full_stars = 0
        half_star = 0
        empty_stars = 5

    return render_template(
        "public_view.html",
        user=user,
        is_seller=is_seller,
        reviews=reviews,
        average_rating=average_rating,
        full_stars=full_stars,
        half_star=half_star,
        empty_stars=empty_stars,
        num_reviews=len(reviews),
    )
