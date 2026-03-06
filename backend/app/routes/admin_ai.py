from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.utils.authz import admin_required
from app.extensions import db
from app.models.laptop import Laptop
from app.services.ai_model import predict_scores

admin_ai_bp = Blueprint("admin_ai", __name__)


@admin_ai_bp.post("/ai/recompute-scores")
@jwt_required()
@admin_required
def recompute_scores():

    laptops = Laptop.query.filter_by(is_active=True).all()

    scores = predict_scores(laptops)

    for laptop, score in zip(laptops, scores):
        laptop.ahp_score = float(score)

    db.session.commit()

    return jsonify({
        "message": "Recomputed scores",
        "count": len(laptops)
    })