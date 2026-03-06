from flask import Blueprint, jsonify
reviews_bp = Blueprint("reviews", __name__)
@reviews_bp.get("/")
def stub(): return jsonify([]), 200