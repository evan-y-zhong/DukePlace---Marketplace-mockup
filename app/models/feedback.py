from flask import current_app as app


class Feedback:
    def __init__(self, id, user_id, product_id, rating, comment, time_purchased):
        self.id = id
        self.user_id = user_id
        self.product_id = product_id
        self.rating = rating
        self.comment = comment
        self.time_purchased = time_purchased

    # necessary to pass into render_template
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "rating": self.rating,
            "comment": self.comment,
            "time_purchased": self.time_purchased.strftime("%Y-%m-%d %H:%M:%S"),
        }

    # gets recent feedback (per_page is for pagination)
    @staticmethod
    def get_recent_feedback_by_user(user_id, per_page=5, page=1):
        offset = (page - 1) * per_page
        rows = app.db.execute(
            """
            SELECT id, user_id, product_id, rating, comment, time_purchased
            FROM Feedback
            WHERE user_id = :user_id
            ORDER BY time_purchased DESC
            LIMIT :per_page OFFSET :offset
        """,
            user_id=user_id,
            per_page=per_page,
            offset=offset,
        )

        return [Feedback(*row) for row in rows] if rows else []

    # this will get the count
    @staticmethod
    def get_all_feedback_by_user(user_id):
        rows = app.db.execute(
            """
            SELECT COUNT(*)
            FROM Feedback
            WHERE user_id = :user_id
        """,
            user_id=user_id,
        )

        return rows[0][0]

    # this will get the actual feedback
    @staticmethod
    def get_feedback_by_user_id(user_id):
        rows = app.db.execute(
            """
    SELECT 
        f.id AS feedback_id, 
        f.user_id, 
        f.product_id, 
        p.name AS product_name, 
        f.rating, 
        f.comment, 
        f.time_purchased
    FROM Feedback f
    JOIN Products p ON f.product_id = p.id
    WHERE f.user_id = :user_id
    ORDER BY f.time_purchased DESC
    """,
            user_id=user_id,
        )
        return rows if rows else []

    # filter by product as well
    @staticmethod
    def get_by_user_and_product(user_id, product_id):
        rows = app.db.execute(
            """
            SELECT id, user_id, product_id, rating, comment, time_purchased
            FROM Feedback
            WHERE user_id = :user_id AND product_id = :product_id
        """,
            user_id=user_id,
            product_id=product_id,
        )
        return Feedback(*rows[0]) if rows else None

    # add / update is in the same method for functionality
    @staticmethod
    def add_or_update_feedback(user_id, product_id, rating, comment):
        existing_feedback = Feedback.get_by_user_and_product(user_id, product_id)
        if existing_feedback:
            # Update existing feedback
            app.db.execute(
                """
                UPDATE Feedback
                SET rating = :rating, comment = :comment, time_purchased = current_timestamp
                WHERE user_id = :user_id AND product_id = :product_id
            """,
                user_id=user_id,
                product_id=product_id,
                rating=rating,
                comment=comment,
            )
        else:
            # Add new feedback
            app.db.execute(
                """
                INSERT INTO Feedback (user_id, product_id, rating, comment)
                VALUES (:user_id, :product_id, :rating, :comment)
            """,
                user_id=user_id,
                product_id=product_id,
                rating=rating,
                comment=comment,
            )

    # deletes the feedback (only needs user_id and product_id bc it guaranteed unique)
    @staticmethod
    def delete_feedback(user_id, product_id):
        app.db.execute(
            """
            DELETE FROM Feedback
            WHERE user_id = :user_id AND product_id = :product_id
        """,
            user_id=user_id,
            product_id=product_id,
        )

    # gets reviews for a product
    @staticmethod
    def get_all_by_product(product_id):
        feedbacks = app.db.execute(
            """
            SELECT f.rating, f.comment, f.time_purchased, u.firstname || ' ' || u.lastname AS username
            FROM Feedback f
            JOIN Users u ON f.user_id = u.id
            WHERE f.product_id = :product_id
            ORDER BY f.time_purchased DESC
        """,
            product_id=product_id,
        )
        return feedbacks
