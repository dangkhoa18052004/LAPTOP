from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.ahp_criterion import AHPCriterion
from app.utils.authz import admin_required

criteria_bp = Blueprint("criteria", __name__)
admin_criteria_bp = Blueprint("admin_criteria", __name__)


# GET /api/ahp/criteria
@criteria_bp.get("/criteria")
def get_criteria():
    criteria = AHPCriterion.query.order_by(AHPCriterion.id.asc()).all()
    return jsonify([item.to_dict() for item in criteria]), 200


# POST /api/admin/ahp/criteria
@admin_criteria_bp.post("/ahp/criteria")
@jwt_required()
@admin_required
def create_criterion():
    data = request.get_json(silent=True) or {}

    code = (data.get("code") or "").strip().lower()
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip() or None

    if not code or not name:
        return jsonify({"message": "code và name là bắt buộc"}), 400

    exists = AHPCriterion.query.filter(
        db.func.lower(AHPCriterion.code) == code.lower()
    ).first()
    if exists:
        return jsonify({"message": "code đã tồn tại"}), 409

    criterion = AHPCriterion(code=code, name=name, description=description)
    db.session.add(criterion)
    db.session.commit()

    return jsonify({
        "message": "Tạo tiêu chí thành công",
        "criterion": criterion.to_dict()
    }), 201


# PUT /api/admin/ahp/criteria/<id>
@admin_criteria_bp.put("/ahp/criteria/<int:criterion_id>")
@jwt_required()
@admin_required
def update_criterion(criterion_id: int):
    criterion = AHPCriterion.query.get_or_404(criterion_id)
    data = request.get_json(silent=True) or {}

    if "code" in data:
        new_code = (data.get("code") or "").strip().lower()
        if not new_code:
            return jsonify({"message": "code không được rỗng"}), 400

        exists = AHPCriterion.query.filter(
            db.func.lower(AHPCriterion.code) == new_code.lower(),
            AHPCriterion.id != criterion.id
        ).first()
        if exists:
            return jsonify({"message": "code đã tồn tại"}), 409

        criterion.code = new_code

    if "name" in data:
        new_name = (data.get("name") or "").strip()
        if not new_name:
            return jsonify({"message": "name không được rỗng"}), 400
        criterion.name = new_name

    if "description" in data:
        criterion.description = (data.get("description") or "").strip() or None

    db.session.commit()

    return jsonify({
        "message": "Cập nhật tiêu chí thành công",
        "criterion": criterion.to_dict()
    }), 200


# DELETE /api/admin/ahp/criteria/<id>
@admin_criteria_bp.delete("/ahp/criteria/<int:criterion_id>")
@jwt_required()
@admin_required
def delete_criterion(criterion_id: int):
    criterion = AHPCriterion.query.get_or_404(criterion_id)

    db.session.delete(criterion)
    db.session.commit()

    return jsonify({"message": "Xóa tiêu chí thành công"}), 200