from flask import Blueprint, jsonify
orders_bp = Blueprint("orders", __name__)
@orders_bp.get("/")
def stub(): return jsonify([]), 200