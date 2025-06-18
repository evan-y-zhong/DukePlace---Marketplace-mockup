from datetime import timedelta
from werkzeug.security import generate_password_hash
import csv
from faker import Faker
import pandas as pd
import random

num_users = 100
categories = [
    "Electronics",
    "Books",
    "Clothing",
    "Home Appliances",
    "Toys",
    "Sports Equipment",
]
num_products = 2000
num_purchases = 2500
num_feedback = 2000
num_coupons = 100

Faker.seed(0)
fake = Faker()


def get_csv_writer(f):
    return csv.writer(f, dialect="unix")


def gen_users(num_users):
    with open("Users.csv", "w") as f:
        writer = get_csv_writer(f)
        print("Users...", end=" ", flush=True)
        for uid in range(num_users):
            if uid % 10 == 0:
                print(f"{uid}", end=" ", flush=True)
            profile = fake.profile()
            email = profile["mail"]
            plain_password = f"pass{uid}"
            password = generate_password_hash(plain_password)
            name_components = profile["name"].split(" ")
            firstname = name_components[0]
            lastname = name_components[-1]
            balance = fake.random_int(min=0, max=10000)
            address = fake.address()
            writer.writerow(
                [uid, email, password, firstname, lastname, balance, True, address]
            )
        print(f"{num_users} generated")
    return


######################################
def gen_products(num_products, categories):
    available_pids = []
    with open("Products.csv", "w", newline="") as f:
        writer = csv.writer(f, dialect="unix")
        print("Products...", end=" ", flush=True)

        for pid in range(0, num_products + 1):  # Ensure IDs start from 0
            if pid % 100 == 0:
                print(f"{pid}", end=" ", flush=True)
            name = f"{fake.sentence(nb_words=3)[:-1]}_{pid}"  # Append ID to ensure uniqueness
            description = fake.text(max_nb_chars=200)
            creator_id = fake.random_int(min=0, max=num_users - 1)
            price = f"{fake.random_number(digits=2)}.{fake.random_number(digits=2):02}"  # Correct formatting
            available = fake.random_element(elements=("true", "false"))
            category = fake.random_element(elements=categories)
            # image_url = f"https://placeimg.com/640/480/{category.lower().replace(' ', '_')}"  # URL friendly string
            image_url = (
                f"https://picsum.photos/id/{pid % 900}/640/480"  # URL friendly string
            )
            writer.writerow(
                [
                    pid,
                    name,
                    description,
                    creator_id,
                    price,
                    available,
                    category,
                    image_url,
                ]
            )
            if available == "true":
                available_pids.append(pid)

        print(f"\n{num_products} products generated; {len(available_pids)} available")

    return available_pids


###################################################


def gen_purchases(num_purchases, available_pids):
    with open("Purchases.csv", "w") as f:
        writer = get_csv_writer(f)
        print("Purchases...", end=" ", flush=True)
        for id in range(num_purchases):
            if id % 100 == 0:
                print(f"{id}", end=" ", flush=True)
            uid = fake.random_int(min=0, max=num_users - 1)
            pid = fake.random_element(elements=available_pids)
            time_purchased = fake.date_time()
            writer.writerow([id, uid, pid, time_purchased])
        print(f"{num_purchases} generated")
    return


gen_products(num_products, categories)


def gen_inventories():
    users_df = pd.read_csv(
        "Users.csv",
        names=[
            "id",
            "email",
            "password",
            "firstname",
            "lastname",
            "balance",
            "is_seller",
            "address",
        ],
    )
    products_df = pd.read_csv(
        "Products.csv",
        names=[
            "id",
            "name",
            "description",
            "creator_id",
            "price",
            "available",
            "category",
            "url",
        ],
    )

    with open("Inventory.csv", "w") as f:
        writer = get_csv_writer(f)
        print("Inventory...", end=" ", flush=True)

        inventory_id = 0
        for user_id in users_df["id"]:
            num_products = random.randint(1, len(products_df) // 50)
            selected_products = products_df.sample(num_products)

            for _, product_row in selected_products.iterrows():
                product_id = product_row["id"]
                # random quantity
                quantity = random.randint(1, 100)

                writer.writerow([inventory_id, user_id, product_id, quantity])
                inventory_id += 1

        print(f"{inventory_id} inventory records generated")


def gen_feedback():
    inventory_df = pd.read_csv(
        "Inventory.csv", names=["inventory_id", "user_id", "product_id", "quantity"]
    )
    products_df = pd.read_csv(
        "Products.csv",
        names=[
            "pid",
            "name",
            "description",
            "creator_id",
            "price",
            "available",
            "category",
            "url",
        ],
    )
    user_ids = inventory_df["user_id"].tolist()
    product_ids = products_df["pid"].tolist()

    unique_pairs = set()

    with open("Feedback.csv", "w") as f:
        writer = get_csv_writer(f)

        for feedback_id in range(num_feedback):
            uid = random.choice(user_ids)
            pid = random.choice(product_ids)

            if (uid, pid) not in unique_pairs:
                unique_pairs.add((uid, pid))  # Mark this pair as used
                rating = random.randint(1, 5)
                comment = fake.sentence(nb_words=4)[:-1]
                time_purchased = fake.date_time()
                writer.writerow(
                    [feedback_id, uid, pid, rating, comment, time_purchased]
                )


def gen_balance_history():
    users_df = pd.read_csv(
        "Users.csv",
        names=[
            "id",
            "email",
            "password",
            "firstname",
            "lastname",
            "balance",
            "is_seller",
            "address",
        ],
    )

    with open("BalanceHistory.csv", "w") as f:
        writer = get_csv_writer(f)
        print("BalanceHistory...", end=" ", flush=True)

        balance_history_id = 0
        for _, user_row in users_df.iterrows():
            user_id = user_row["id"]
            balance = user_row["balance"]
            num_entries = random.randint(5, 15)
            start_date = fake.date_time_between(start_date="-1y", end_date="-6m")

            for _ in range(num_entries):
                time = start_date + timedelta(days=random.randint(1, 30))
                balance_change = random.uniform(-1000, 1000)
                balance = max(0, balance + balance_change)
                writer.writerow([balance_history_id, user_id, time, round(balance, 2)])
                balance_history_id += 1
                start_date = time

        print(f"{balance_history_id} balance history records generated")
    return


def gen_coupons(num_coupons, available_pids, categories):
    with open("Coupons.csv", "w") as f:
        writer = get_csv_writer(f)
        print("Coupons...", end=" ", flush=True)

        for coupon_id in range(num_coupons):
            if coupon_id % 10 == 0:
                print(f"{coupon_id}", end=" ", flush=True)

            # Generate a random coupon code
            code = f"COUPON{coupon_id:05}"  # Ensures unique and readable codes like COUPON00001

            # Randomly assign a discount type
            discount_type = fake.random_element(elements=("item", "group", "cart"))

            # Determine the discount value and applicable products
            if discount_type == "item":
                discount_value = random.uniform(5, 20)  # Flat discount on a single item
                applicable_product_ids = [
                    random.choice(available_pids)
                ]  # One random product ID
            elif discount_type == "group":
                discount_value = random.uniform(
                    10, 30
                )  # Percentage discount for a group
                applicable_product_ids = random.sample(
                    available_pids, k=min(5, len(available_pids))
                )  # Randomly choose up to 5 products
            else:  # 'cart'
                discount_value = random.uniform(
                    10, 25
                )  # Percentage discount on the cart
                applicable_product_ids = (
                    None  # No applicable product IDs for cart-wide discounts
                )

            # Set expiration date for the coupon
            expiration_date = fake.date_time_between(start_date="now", end_date="+1y")

            # Format applicable_product_ids for PostgreSQL
            if applicable_product_ids is None:
                applicable_product_ids_str = "{}"  # Use NULL for cart-wide discounts
            else:
                applicable_product_ids_str = (
                    "{" + ",".join(map(str, applicable_product_ids)) + "}"
                )

            # Write coupon details to the CSV
            writer.writerow(
                [
                    coupon_id,  # Unique ID
                    code,  # Coupon code
                    discount_type,  # Type of discount
                    round(discount_value, 2),  # Discount value (rounded)
                    applicable_product_ids_str,  # Product IDs as a PostgreSQL array string or NULL
                    expiration_date,  # Expiration date
                    True,  # Active status
                ]
            )

        print(f"\n{num_coupons} coupons generated")


gen_users(num_users)
available_pids = gen_products(num_products, categories)
gen_purchases(num_purchases, available_pids)
gen_inventories()
gen_feedback()
gen_purchases(num_purchases, available_pids)
gen_balance_history()
gen_coupons(num_coupons, available_pids, categories)
