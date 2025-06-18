from flask import Flask, g, request, redirect, url_for, session
from flask_login import LoginManager, current_user
from .models.user import User
from .config import Config
from .db import DB


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.db = DB(app)
    login_manager = LoginManager()
    login_manager.login_view = "users.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    @app.before_request
    def before_request():
        g.user = current_user
        if request.endpoint in [
            "carts.cart",
            "carts.checkout",
            "carts.add_to_cart",
            "carts.remove_from_cart",
            "carts.change_quantity_page",
            "carts.update_quantity",
        ]:
            if not current_user.is_authenticated:
                return redirect(url_for("users.login"))
        if request.endpoint in [
            "users.profile",
            "orders.history",
            "feedbacks.get_my_feedback",
        ]:
            if not current_user.is_authenticated:
                return redirect(url_for("users.login"))

    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "-1"
        return response

    from .index import bp as index_bp

    app.register_blueprint(index_bp)

    from .users import bp as users_bp

    app.register_blueprint(users_bp)

    from .carts import bp as carts_bp

    app.register_blueprint(carts_bp)

    from .products import bp as products_bp

    app.register_blueprint(products_bp)

    from .seller_view import bp as seller_view_bp

    app.register_blueprint(seller_view_bp)

    from .feedbacks import bp as feedbacks_bp

    app.register_blueprint(feedbacks_bp)

    from .inventory import bp as inventory_bp

    app.register_blueprint(inventory_bp)

    from .orders import bp as orders_bp

    app.register_blueprint(orders_bp)

    from .seller_orders import bp as seller_orders_bp

    app.register_blueprint(seller_orders_bp)

    return app
