from flask import current_app as app


class InventoryItem:
    def __init__(self, id, seller_id, product_id, quantity):
        self.id = id
        self.seller_id = seller_id
        self.product_id = product_id
        self.quantity = quantity

    # gets inventory based on seller_id
    @staticmethod
    def get_by_seller_id(seller_id):
        """Retrieve all inventory items for a specific seller."""
        rows = app.db.execute(
            """
SELECT id, seller_id, product_id, quantity
FROM Inventory
WHERE seller_id = :seller_id
""",
            seller_id=seller_id,
        )

        return [InventoryItem(*row) for row in rows]

    # gets the info based an the seller_id and product_id (guaranteed to be unique)
    @staticmethod
    def get_by_product_id(seller_id, product_id):
        """Retrieve a specific inventory item by seller and product."""
        rows = app.db.execute(
            """
SELECT id, seller_id, product_id, quantity
FROM Inventory
WHERE seller_id = :seller_id AND product_id = :product_id
""",
            seller_id=seller_id,
            product_id=product_id,
        )

        return InventoryItem(*rows[0]) if rows else None

    # adds an item to the inventory, necessary for creating new inventory info
    @staticmethod
    def add_item(seller_id, product_id, quantity):
        """Add a new product to the seller's inventory."""
        try:
            app.db.execute(
                """
INSERT INTO Inventory (seller_id, product_id, quantity)
VALUES (:seller_id, :product_id, :quantity)
""",
                seller_id=seller_id,
                product_id=product_id,
                quantity=quantity,
            )
            return True
        except Exception as e:
            # Likely a violation of the unique constraint
            print(str(e))
            return False

    # updates the quantity for a certain product_id, DOES NOT do it in-place (+-x)
    @staticmethod
    def update_quantity(seller_id, product_id, quantity):
        """Update the quantity of an inventory item."""
        try:
            app.db.execute(
                """
UPDATE Inventory
SET quantity = :quantity
WHERE product_id = :product_id AND seller_id = :seller_id
""",
                seller_id=seller_id,
                product_id=product_id,
                quantity=quantity,
            )
            return True
        except Exception as e:
            print(str(e))
            return False

    # removes item from cart
    @staticmethod
    def remove_item(seller_id, product_id):
        """Remove a product from the seller's inventory."""
        try:
            app.db.execute(
                """
DELETE FROM Inventory
WHERE seller_id = :seller_id AND product_id = :product_id
""",
                seller_id=seller_id,
                product_id=product_id,
            )
            return True
        except Exception as e:
            print(str(e))
            return False

    # gets the image_url for testing purposes
    @staticmethod
    def get_image(product_id):
        image_url = app.db.execute(
            """
        SELECT image_url FROM Products WHERE id=:product_id
        """,
            product_id=product_id,
        )[0][0]
        return image_url
