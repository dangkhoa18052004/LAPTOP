from flask import Blueprint, jsonify
chat_bp = Blueprint("chat", __name__)
@chat_bp.get("/")
def stub(): return jsonify([]), 200