from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.user import User
from app.utils.authz import admin_required

admin_users_bp = Blueprint("admin_users", __name__)

# ✅ (đã có) list users
@admin_users_bp.get("/users")
@jwt_required()
@admin_required
def list_users():
    users = User.query.order_by(User.id.desc()).all()
    return jsonify([u.to_dict() for u in users]), 200


# ✅ NEW: admin tạo user
@admin_users_bp.post("/users")
@jwt_required()
@admin_required
def admin_create_user():
    data = request.get_json(silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "user").strip().lower()

    phone_number = (data.get("phone_number") or data.get("phone") or "").strip() or None
    address = (data.get("address") or "").strip() or None

    if not full_name or not email or not password:
        return jsonify({"message": "full_name, email, password là bắt buộc"}), 400
    if role not in ["admin", "user"]:
        return jsonify({"message": "role chỉ được 'admin' hoặc 'user'"}), 400
    if len(password) < 6:
        return jsonify({"message": "Mật khẩu phải >= 6 ký tự"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email đã tồn tại"}), 409

    user = User(full_name=full_name, email=email, role=role)
    user.phone_number = phone_number
    user.address = address
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Tạo user thành công", "user": user.to_dict()}), 201


# ✅ NEW: admin sửa user
@admin_users_bp.put("/users/<int:user_id>")
@jwt_required()
@admin_required
def admin_update_user(user_id: int):
    user = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}

    if "full_name" in data:
        user.full_name = (data.get("full_name") or "").strip()
        if not user.full_name:
            return jsonify({"message": "full_name không được rỗng"}), 400

    # optional: cho đổi email
    if "email" in data:
        new_email = (data.get("email") or "").strip().lower()
        if not new_email:
            return jsonify({"message": "email không được rỗng"}), 400
        exists = User.query.filter(User.email == new_email, User.id != user.id).first()
        if exists:
            return jsonify({"message": "Email đã tồn tại"}), 409
        user.email = new_email

    if "phone_number" in data or "phone" in data:
        user.phone_number = (data.get("phone_number") or data.get("phone") or "").strip() or None

    if "address" in data:
        user.address = (data.get("address") or "").strip() or None

    # optional: cho đổi role ngay trong update
    if "role" in data:
        role = (data.get("role") or "").strip().lower()
        if role not in ["admin", "user"]:
            return jsonify({"message": "role chỉ được 'admin' hoặc 'user'"}), 400
        user.role = role

    db.session.commit()
    return jsonify({"message": "Cập nhật user thành công", "user": user.to_dict()}), 200


# ✅ (đã có) đổi role riêng
@admin_users_bp.put("/users/<int:user_id>/role")
@jwt_required()
@admin_required
def update_role(user_id: int):
    user = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}
    role = (data.get("role") or "").strip().lower()

    if role not in ["admin", "user"]:
        return jsonify({"message": "role chỉ được 'admin' hoặc 'user'"}), 400

    user.role = role
    db.session.commit()
    return jsonify({"message": "Cập nhật role thành công", "user": user.to_dict()}), 200


# ✅ NEW: admin xóa user
@admin_users_bp.delete("/users/<int:user_id>")
@jwt_required()
@admin_required
def admin_delete_user(user_id: int):
    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "Xóa user thành công"}), 200