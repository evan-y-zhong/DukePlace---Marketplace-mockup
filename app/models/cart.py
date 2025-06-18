# app/models/cart.py

from flask import current_app as app
from datetime import datetime


class Cart:
    # cart has a user id and an id
    def __init__(self, id, user_id):
        self.id = id
        self.user_id = user_id

    # get sthe cart for a user id
    @staticmethod
    def get_by_user_id(user_id):
        rows = app.db.execute(
            """
SELECT id, user_id
FROM Carts
WHERE user_id = :user_id
""",
            user_id=user_id,
        )
        if rows:
            return Cart(*rows[0])
        else:
            return None

    # creates a cart for a user_id
    @staticmethod
    def create(user_id):
        try:
            rows = app.db.execute(
                """
INSERT INTO Carts(user_id)
VALUES(:user_id)
RETURNING id, user_id
""",
                user_id=user_id,
            )
            return Cart(*rows[0]) if rows else None
        except Exception as e:
            print(str(e))
            return None

    # applies coupon for a certain cart (coupon_code must be valid)
    @staticmethod
    def apply_coupon(cart_id, coupon_code):
        rows = app.db.execute(
            """
SELECT discount_type, discount_value, applicable_product_ids, expiration_date, is_active
FROM Coupons
WHERE code = :coupon_code
""",
            coupon_code=coupon_code,
        )

        if not rows:
            # returns error if bad coupon code
            return None, "Invalid coupon code."

        coupon = rows[0]
        discount_type = coupon[0]
        discount_value = coupon[1]
        applicable_product_ids = coupon[2]
        expiration_date = coupon[3]
        is_active = coupon[4]

        if not is_active or (expiration_date and expiration_date < datetime.utcnow()):
            return None, "Coupon has expired or is inactive."

        items = CartItem.get_by_cart_id(cart_id)

        discount = 0
        if discount_type == "item":
            for item in items:
                if item.product_id in applicable_product_ids:
                    discount += discount_value
        elif discount_type == "group":
            for item in items:
                if item.product_id in applicable_product_ids:
                    discount += item.total_price * (discount_value / 100)
        elif discount_type == "cart":
            total_price = sum(item.total_price for item in items)
            discount = total_price * (discount_value / 100)

        return discount, None


class CartItem:
    def __init__(
        self,
        id,
        cart_id,
        product_id,
        seller_id,
        seller_name,
        quantity,
        unit_price,
        total_price,
    ):
        self.id = id
        self.cart_id = cart_id
        self.product_id = product_id
        self.seller_id = seller_id
        self.seller_name = seller_name
        self.quantity = quantity
        self.unit_price = unit_price
        self.total_price = total_price

    @staticmethod
    # get rows in CartItem
    def get_by_cart_id(cart_id):
        rows = app.db.execute(
            """
SELECT *
FROM Cart_Items
WHERE cart_id = :cart_id
""",
            cart_id=cart_id,
        )
        return [CartItem(*row) for row in rows]

    # adds item to cart given info below
    @staticmethod
    def add_item(cart_id, product_id, seller_id, seller_name, quantity, unit_price):
        total_price = quantity * unit_price
        try:
            rows = app.db.execute(
                """
INSERT INTO Cart_Items(cart_id, product_id, seller_id, seller_name, quantity, unit_price, total_price)
VALUES(:cart_id, :product_id, :seller_id, :seller_name, :quantity, :unit_price, :total_price)
RETURNING id
""",
                cart_id=cart_id,
                product_id=product_id,
                seller_id=seller_id,
                seller_name=seller_name,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
            )
            return rows[0][0] if rows else None
        except Exception as e:
            print(str(e))
            return None

    # updates quantity for a specific item_id in the cart
    @staticmethod
    def update_quantity(cart_item_id, quantity, total_price):
        try:
            app.db.execute(
                """
UPDATE Cart_Items
SET quantity = :quantity, total_price = :total_price
WHERE id = :cart_item_id
""",
                cart_item_id=cart_item_id,
                quantity=quantity,
                total_price=total_price,
            )
            return True
        except Exception as e:
            print(str(e))
            return False

    # when they checkout, this method should be called
    @staticmethod
    def clear_cart(cart_id):
        try:
            # Delete all items from the cart with the given cart_id
            app.db.execute(
                """
DELETE FROM Cart_Items
WHERE cart_id = :cart_id
""",
                cart_id=cart_id,
            )
            return True
        except Exception as e:
            # Print an error message if something goes wrong
            print(f"Error clearing cart {cart_id}: {str(e)}")
            return False

    # update the quantity and total price of a cart item
    @staticmethod
    def update_quantity(cart_item_id, quantity, total_price):
        # Execute the SQL query to update the cart item
        app.db.execute(
            """
UPDATE Cart_Items
SET quantity = :quantity, total_price = :total_price
WHERE id = :cart_item_id
""",
            quantity=quantity,
            total_price=total_price,
            cart_item_id=cart_item_id,
        )
