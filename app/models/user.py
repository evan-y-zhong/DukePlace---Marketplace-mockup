# app/models/user.py
from flask_login import UserMixin
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin):
    def __init__(self, id, email, firstname, lastname, balance=0, address=None):
        self.id = id
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.balance = balance
        self.address = address

    # auth stuff for flask
    @staticmethod
    def get_by_auth(email, password):
        rows = app.db.execute(
            """
SELECT password, id, email, firstname, lastname, balance, address
FROM Users
WHERE email = :email
""",
            email=email,
        )
        if not rows:  # email not found
            return None
        elif not check_password_hash(rows[0][0], password):
            # incorrect password
            return None
        else:
            return User(*(rows[0][1:]))

    # checks if email exists in database
    @staticmethod
    def email_exists(email):
        rows = app.db.execute(
            """
SELECT email
FROM Users
WHERE email = :email
""",
            email=email,
        )
        return len(rows) > 0

    # tries to register, returns None if fails
    @staticmethod
    def register(email, password, firstname, lastname):
        try:
            rows = app.db.execute(
                """
INSERT INTO Users(email, password, firstname, lastname, balance, address)
VALUES(:email, :password, :firstname, :lastname, 0, NULL)
RETURNING id
""",
                email=email,
                password=generate_password_hash(password),
                firstname=firstname,
                lastname=lastname,
            )
            id = rows[0][0]
            return User.get(id)
        except Exception as e:
            print(str(e))
            return None

    # gets a certain user
    @staticmethod
    def get(id):
        rows = app.db.execute(
            """
SELECT id, email, firstname, lastname, balance, address
FROM Users
WHERE id = :id
""",
            id=id,
        )
        return User(*(rows[0])) if rows else None

    # updates the balance, not cumulative (not +/- x)
    @staticmethod
    def update_balance(user_id, amount):
        try:
            app.db.execute(
                """
UPDATE Users
SET balance = balance + :amount
WHERE id = :user_id
""",
                user_id=user_id,
                amount=amount,
            )
            User.update_balance_history(user_id)
            return True
        except Exception as e:
            print(str(e))
            return False

    # updates profile given a user_id and their other information, password is not necessary
    @staticmethod
    def update_profile(user_id, firstname, lastname, email, password, address):
        try:
            if password:
                app.db.execute(
                    """
UPDATE Users
SET firstname = :firstname, lastname = :lastname, email = :email, password = :password, address = :address
WHERE id = :user_id
""",
                    user_id=user_id,
                    firstname=firstname,
                    lastname=lastname,
                    email=email,
                    password=generate_password_hash(password),
                    address=address,
                )
            else:
                app.db.execute(
                    """
UPDATE Users
SET firstname = :firstname, lastname = :lastname, email = :email, address = :address
WHERE id = :user_id
""",
                    user_id=user_id,
                    firstname=firstname,
                    lastname=lastname,
                    email=email,
                    address=address,
                )
            return True
        except Exception as e:
            print(str(e))
            return False

    # gets by an id or name, both types of queries work
    @staticmethod
    def get_by_id_or_name(query):
        rows = app.db.execute(
            """
SELECT id, email, firstname, lastname, balance
FROM Users
WHERE id::text = :query OR firstname ILIKE :query OR lastname ILIKE :query
""",
            query=f"%{query}%",
        )

        return [User(*row) for row in rows] if rows else []

    # gets the balance history
    @staticmethod
    def get_balance_history(user_id):
        rows = app.db.execute(
            """
SELECT time, balance
FROM BalanceHistory
WHERE user_id = :user_id
ORDER BY time
""",
            user_id=user_id,
        )
        print(rows)

        return [{"time": row[0].isoformat(), "balance": row[1]} for row in rows]

    # updatse the balance history so that it appends it to the table for access later
    @staticmethod
    def update_balance_history(user_id):
        balance = app.db.execute(
            """
SELECT balance
FROM Users
WHERE id = :user_id
""",
            user_id=user_id,
        )[0][0]
        app.db.execute(
            """
INSERT INTO BalanceHistory (user_id, time, balance)
VALUES (:user_id, :time, :balance)
""",
            user_id=user_id,
            time=datetime.utcnow(),
            balance=balance,
        )
