from app.models.feedback import Feedback
from flask import current_app as app
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
import sys

bp = Blueprint("products", __name__)


class Product:
    def __init__(
        self,
        id,
        name,
        description,
        creator_id,
        price,
        available,
        category,
        image_url=None,
    ):
        self.id = id
        self.name = name
        self.description = description or "No description available"
        self.creator_id = creator_id
        self.price = price
        self.available = available
        self.category = category or "Uncategorized"
        self.image_url = image_url or "default-image.jpg"

    # necessary for render_template
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "creator_id": self.creator_id,
            "price": str(self.price),
            "available": self.available,
            "category": self.category,
            "image_url": self.image_url,
        }

    # gets all products
    @staticmethod
    def get(id):
        rows = app.db.execute(
            """
SELECT *
FROM Products
WHERE id = :id
""",
            id=id,
        )
        return Product(*(rows[0])) if rows else None

    # gets all products with a filter applied (category and query)
    @staticmethod
    def get_all_filtered(
        available=True,
        category="",
        search_query="",
        sort_order="price_asc",
        page=1,
        per_page=10,
    ):
        query = """
SELECT *
FROM Products
WHERE available = :available
"""
        if category:
            query += " AND category = :category"
        if search_query:
            query += " AND (name LIKE :search_query OR description LIKE :search_query)"

        if sort_order == "price_asc":
            query += " ORDER BY price ASC"
        elif sort_order == "price_desc":
            query += " ORDER BY price DESC"

        query += " LIMIT :per_page OFFSET :offset"

        offset = (page - 1) * per_page
        rows = app.db.execute(
            query,
            available=available,
            category=category,
            search_query=f"%{search_query}%",
            per_page=per_page,
            offset=offset,
        )
        products = [Product(*row) for row in rows]

        # Fetch total count for pagination
        count_query = """
SELECT COUNT(*)
FROM Products
WHERE available = :available
"""
        if category:
            count_query += " AND category = :category"
        if search_query:
            count_query += (
                " AND (name LIKE :search_query OR description LIKE :search_query)"
            )

        total_count = app.db.execute(
            count_query,
            available=available,
            category=category,
            search_query=f"%{search_query}%",
        )[0][0]
        return products, total_count

    # get top k, used for milestone 1
    @staticmethod
    def get_top_k_expensive(k):
        rows = app.db.execute(
            """
SELECT id, name, description, price, available, category, image_url
FROM Products
ORDER BY price DESC
LIMIT :k
""",
            k=k,
        )
        return [Product(*row) for row in rows]

    # gets the number of products
    @staticmethod
    def get_product_count(available=True, category=""):
        query = """
SELECT COUNT(*)
FROM Products
WHERE available = :available
"""
        if category:
            query += " AND category = :category"

        result = app.db.execute(query, available=available, category=category)
        return result[0][0] if result else 0

    # gets all categories (books, movies, etc.)
    @staticmethod
    def get_categories():
        query = """
    SELECT DISTINCT category
    FROM Products
    WHERE category IS NOT NULL
    ORDER BY category
    """
        rows = app.db.execute(query)
        categories = [row[0] for row in rows]
        return categories

    # gets by the creator_id, SAME AS SELLER_ID
    @staticmethod
    def get_by_creator(creator_id):
        rows = app.db.execute(
            """
SELECT *
FROM Products
WHERE creator_id = :creator_id
""",
            creator_id=creator_id,
        )
        return [Product(*row) for row in rows]

    # gets by the product_name instead of id
    @staticmethod
    def get_by_name(product_name):
        result = app.db.execute(
            """
        SELECT id
        FROM Products
        WHERE name = :product_name
        """,
            product_name=product_name,
        )
        return result[0][0] if result else -1

    # can add a product to the product list
    @staticmethod
    def add_product(
        product_name, description, creator_id, price, available, category, url
    ):
        """Create new product, added by Kaden 11/30"""
        try:
            app.db.execute(
                """
INSERT INTO Products (name, description, creator_id, price, available, category, image_url)
VALUES (:product_name, :description, :creator_id, :price, :available, :category, :url)
""",
                product_name=product_name,
                description=description,
                creator_id=creator_id,
                price=price,
                available=available,
                category=category,
                url=url,
            )
            return True
        except Exception as e:
            # Likely a violation of the unique constraint
            print(str(e))
            return False

    # gets all the sellers for a certain product
    @staticmethod
    def get_sellers(product_id):
        sellers = app.db.execute(
            """
            SELECT Users.id AS seller_id, Users.firstname, Users.lastname, Inventory.quantity
            FROM Inventory
            JOIN Users ON Inventory.seller_id = Users.id
            WHERE Inventory.product_id = :product_id
        """,
            product_id=product_id,
        )
        return sellers

    # updates info
    @staticmethod
    def update(id, name, description, price, category, image_url):
        try:
            app.db.execute(
                """
        UPDATE Products
        SET name = :name, description = :description, price = :price, category = :category, image_url = :image_url
        WHERE id = :id
        """,
                id=id,
                name=name,
                description=description,
                price=price,
                category=category,
                image_url=image_url,
            )
            return True
        except Exception as e:
            flash(e, "danger")
            return False

    # @staticmethod
    # def get_all(available=True, category='', search_query='', sort_order='price_asc', page=1, per_page=10):
    #     query = '''
    # SELECT id, name, description, price, available, category, image_url
    # FROM Products
    # WHERE available = :available
    # '''
    #     if category:
    #         query += ' AND category = :category'
    #     if search_query:
    #         query += ' AND (name LIKE :search_query OR description LIKE :search_query)'
    #     if sort_order == 'price_asc':
    #         query += ' ORDER BY price ASC'
    #     elif sort_order == 'price_desc':
    #         query += ' ORDER BY price DESC'

    #     query += ' LIMIT :per_page OFFSET :offset'

    #     offset = (page-1) * per_page
    #     params = {
    #         'available': available,
    #         'category': category,
    #         'search_query': f'%{search_query}%',
    #         'per_page': per_page,
    #         'offset': offset
    #     }
    #     rows = app.db.execute(query, **params)
    #     return [Product(*row) for row in rows]
