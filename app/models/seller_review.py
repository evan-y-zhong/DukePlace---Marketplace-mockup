from flask import current_app as app


class SellerReview:
    def __init__(self, id, user_id, seller_id, rating, comment, time_of_review):
        self.id = id
        self.user_id = user_id
        self.seller_id = seller_id
        self.rating = rating
        self.comment = comment
        self.time_of_review = time_of_review

    # render_template
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "seller_id": self.seller_id,
            "rating": self.rating,
            "comment": self.comment,
            "time_of_review": self.time_of_review.strftime("%Y-%m-%d %H:%M:%S"),
        }

    # gets the most recent reviews for a seller_id (paginated)
    @staticmethod
    def get_recent_reviews_by_seller(seller_id, per_page=5, page=1):
        offset = (page - 1) * per_page
        rows = app.db.execute(
            """
            SELECT id, user_id, seller_id, rating, comment, time_of_review
            FROM Seller_Reviews
            WHERE seller_id = :seller_id
            ORDER BY time_of_review DESC
            LIMIT :per_page OFFSET :offset
        """,
            seller_id=seller_id,
            per_page=per_page,
            offset=offset,
        )

        return [SellerReview(*row) for row in rows] if rows else []

    # gets all reviews for a seller (historical, not used)
    @staticmethod
    def get_all_reviews_by_seller(seller_id):
        rows = app.db.execute(
            """
            SELECT COUNT(*)
            FROM Seller_Reviews
            WHERE seller_id = :seller_id
        """,
            seller_id=seller_id,
        )

        return rows[0][0]

    # gets review froma certain user to a certain seller
    @staticmethod
    def get_review_by_user_and_seller(user_id, seller_id):
        rows = app.db.execute(
            """
            SELECT id, user_id, seller_id, rating, comment, time_of_review
            FROM Seller_Reviews
            WHERE user_id = :user_id AND seller_id = :seller_id
        """,
            user_id=user_id,
            seller_id=seller_id,
        )
        return SellerReview(*rows[0]) if rows else None

    # can add or update review given user_id, and seller_id (guaranteed to be unique)
    @staticmethod
    def add_or_update_review(user_id, seller_id, rating, comment):
        existing_review = SellerReview.get_review_by_user_and_seller(user_id, seller_id)
        if existing_review:
            # Update existing review
            app.db.execute(
                """
                UPDATE Seller_Reviews
                SET rating = :rating, comment = :comment, time_of_review = current_timestamp
                WHERE user_id = :user_id AND seller_id = :seller_id
            """,
                user_id=user_id,
                seller_id=seller_id,
                rating=rating,
                comment=comment,
            )
        else:
            # Add new review
            app.db.execute(
                """
                INSERT INTO Seller_Reviews (user_id, seller_id, rating, comment)
                VALUES (:user_id, :seller_id, :rating, :comment)
            """,
                user_id=user_id,
                seller_id=seller_id,
                rating=rating,
                comment=comment,
            )

    # deletes review based on (user_id, seller_id) -> unique
    @staticmethod
    def delete_review(user_id, seller_id):
        app.db.execute(
            """
            DELETE FROM Seller_Reviews
            WHERE user_id = :user_id AND seller_id = :seller_id
        """,
            user_id=user_id,
            seller_id=seller_id,
        )

    # gets all the reviews for a seller
    @staticmethod
    def get_all_by_seller(seller_id):
        reviews = app.db.execute(
            """
            SELECT r.rating, r.comment, r.time_of_review, u.firstname || ' ' || u.lastname AS username
            FROM Seller_Reviews r
            JOIN Users u ON r.user_id = u.id
            WHERE r.seller_id = :seller_id
            ORDER BY r.time_of_review DESC
        """,
            seller_id=seller_id,
        )
        return reviews

    # historical, not used
    @staticmethod
    def get_seller_feedback_by_user_id(user_id):
        rows = app.db.execute(
            """
SELECT id, user_id, seller_id, rating, comment, time_of_review
FROM Seller_Reviews
WHERE seller_id = :user_id
ORDER BY time_of_review DESC
""",
            user_id=user_id,
        )
        return [SellerReview(*row) for row in rows] if rows else []
