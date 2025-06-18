from datetime import datetime
import sys
from app.models.userPurchase import UserPurchase
from flask import current_app as app


class Purchase:
    def __init__(self, id, uid, pid, time_purchased):
        self.id = id
        self.uid = uid
        self.pid = pid
        self.time_purchased = time_purchased

    # purchase
    @staticmethod
    def get(id):
        rows = app.db.execute(
            """
SELECT id, uid, pid, time_purchased
FROM Purchases
WHERE id = :id
""",
            id=id,
        )
        return Purchase(*(rows[0])) if rows else None

    # gets all the purchases for a user_id since a certain date (what type of date should we use?)
    @staticmethod
    def get_all_by_uid_since(uid, since):
        rows = app.db.execute(
            """
SELECT id, uid, pid, time_purchased
FROM Purchases
WHERE uid = :uid
AND time_purchased >= :since
ORDER BY time_purchased DESC
""",
            uid=uid,
            since=since,
        )
        return [Purchase(*row) for row in rows]

    # inserts a certain purchase
    @staticmethod
    def insert(uid, pid):
        try:
            rows = app.db.execute(
                """
                INSERT INTO Purchases (uid, pid, time_purchased)
                VALUES (:uid, :pid, :time_purchased)
                RETURNING id;
            """,
                uid=uid,
                pid=pid,
                time_purchased=datetime.now(),
            )

            return rows[0][0]
        except Exception as e:
            print(f"Error inserting purchase: {str(e)}", file=sys.stderr)
            return None

    # gets the number of purchases, used for UI
    @staticmethod
    def get_num_purchases_by_uid(uid):
        rows = app.db.execute(
            """
            SELECT COUNT(*)
            FROM Purchases p
            JOIN Products pr ON p.pid = pr.id
            WHERE p.uid = :uid
        """,
            uid=uid,
        )
        return rows[0][0]

    # gets the purchase history by a certain user_id -> all their purchases
    @staticmethod
    def get_purchase_history_by_uid(uid, page, per_page):
        offset = (page - 1) * per_page
        rows = app.db.execute(
            """
            SELECT p.id, p.uid, p.pid, p.time_purchased, pr.name, pr.price
            FROM Purchases p
            JOIN Products pr ON p.pid = pr.id
            WHERE p.uid = :uid
            ORDER BY p.time_purchased DESC
            LIMIT :per_page OFFSET :offset
        """,
            uid=uid,
            offset=offset,
            per_page=per_page,
        )

        return [
            UserPurchase(row[0], row[1], row[2], row[3], row[4], row[5]) for row in rows
        ]

    # get spending based on a certain category (not finished)
    @staticmethod
    def get_spending_by_category(user_id):
        rows = app.db.execute(
            """
SELECT pr.category, SUM(pr.price) as total_spent
FROM Purchases p
JOIN Products pr ON p.pid = pr.id
WHERE p.uid = :user_id
GROUP BY pr.category
ORDER BY total_spent DESC
""",
            user_id=user_id,
        )
        return rows

    # get purchases by a category (not total spent)
    @staticmethod
    def get_purchases_by_category(user_id):
        rows = app.db.execute(
            """
SELECT pr.category, COUNT(*) as total_purchases
FROM Purchases p
JOIN Products pr ON p.pid = pr.id
WHERE p.uid = :user_id
GROUP BY pr.category
ORDER BY total_purchases DESC
""",
            user_id=user_id,
        )
        return rows
