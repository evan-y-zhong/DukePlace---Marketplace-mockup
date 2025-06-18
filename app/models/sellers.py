from flask import current_app as app


class Sellers:
    # gets all the products a seller sells
    @staticmethod
    def get_products_by_seller_id(seller_id, page=1, per_page=10):
        offset = (page - 1) * per_page
        rows = app.db.execute(
            """
SELECT p.id, p.name, p.price, p.available
FROM Products p
JOIN Inventory i ON p.id = i.product_id
WHERE i.seller_id = :seller_id
LIMIT :per_page OFFSET :offset
""",
            seller_id=seller_id,
            per_page=per_page,
            offset=offset,
        )
        return rows if rows else []

    # used for UI purposes, gets the number of products they sell
    @staticmethod
    def get_product_count_by_seller(seller_id):
        rows = app.db.execute(
            """
        SELECT COUNT(*) FROM Inventory WHERE seller_id = :seller_id
        """,
            seller_id=seller_id,
        )

        return rows[0][0]

    # 1 if they are seller, 0 if not
    @staticmethod
    def is_seller(user_id):
        rows = app.db.execute(
            """
SELECT 1
FROM Inventory
WHERE seller_id = :user_id
""",
            user_id=user_id,
        )
        return len(rows) > 0
