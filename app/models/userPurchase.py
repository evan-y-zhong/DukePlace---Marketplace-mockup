from datetime import datetime
import sys
from flask import current_app as app


# template class
class UserPurchase:
    def __init__(self, id, uid, pid, time_purchased, name, price):
        self.id = id
        self.uid = uid
        self.pid = pid
        self.time_purchased = time_purchased
        self.name = name
        self.price = price
