from flask import Blueprint

# 同样，假设 transactions.html 在 app/templates/ 下
transactions_bp = Blueprint('transactions_bp', __name__)

from . import routes 