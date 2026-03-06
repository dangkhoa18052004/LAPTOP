from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.brand import Brand
from app.utils.authz import admin_required

brands_bp = Blueprint("brands", __name__)


# 8. GET /api/brands
@brands_bp.get("")
def get_brands():
    brands = Brand.query.order_by(Brand.id.asc()).all()
    return jsonify([brand.to_dict() for brand in brands]), 200


# 9. GET /api/brands/<id>
@brands_bp.get("/<int:brand_id>")
def get_brand_detail(brand_id: int):
    brand = Brand.query.get_or_404(brand_id)
    return jsonify(brand.to_dict()), 200


# 10. POST /api/brands (admin)
@brands_bp.post("")
@jwt_required()
@admin_required
def create_brand():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    logo_url = (data.get("logo_url") or "").strip() or None

    if not name:
        return jsonify({"message": "name là bắt buộc"}), 400

    existing = Brand.query.filter(db.func.lower(Brand.name) == name.lower()).first()
    if existing:
        return jsonify({"message": "Brand đã tồn tại"}), 409

    brand = Brand(name=name, logo_url=logo_url)
    db.session.add(brand)
    db.session.commit()

    return jsonify({
        "message": "Tạo brand thành công",
        "brand": brand.to_dict()
    }), 201


# 11. PUT /api/brands/<id> (admin)
@brands_bp.put("/<int:brand_id>")
@jwt_required()
@admin_required
def update_brand(brand_id: int):
    brand = Brand.query.get_or_404(brand_id)

    data = request.get_json(silent=True) or {}

    if "name" in data:
        new_name = (data.get("name") or "").strip()
        if not new_name:
            return jsonify({"message": "name không được rỗng"}), 400

        existing = Brand.query.filter(
            db.func.lower(Brand.name) == new_name.lower(),
            Brand.id != brand.id
        ).first()
        if existing:
            return jsonify({"message": "Tên brand đã tồn tại"}), 409

        brand.name = new_name

    if "logo_url" in data:
        brand.logo_url = (data.get("logo_url") or "").strip() or None

    db.session.commit()

    return jsonify({
        "message": "Cập nhật brand thành công",
        "brand": brand.to_dict()
    }), 200


# 12. DELETE /api/brands/<id> (admin)
@brands_bp.delete("/<int:brand_id>")
@jwt_required()
@admin_required
def delete_brand(brand_id: int):
    brand = Brand.query.get_or_404(brand_id)

    db.session.delete(brand)
    db.session.commit()

    return jsonify({"message": "Xóa brand thành công"}), 200