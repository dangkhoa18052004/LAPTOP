from flask import Blueprint, jsonify
evaluations_bp = Blueprint("evaluations", __name__)
@evaluations_bp.get("/")
def stub(): return jsonify([]), 200