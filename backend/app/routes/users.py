from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user import User

users_bp = Blueprint("users", __name__)

@users_bp.get("/me")
@jwt_required()
def get_me():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200

@users_bp.put("/me")
@jwt_required()
def update_me():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    data = request.get_json(silent=True) or {}
    if "full_name" in data:
        user.full_name = (data.get("full_name") or "").strip()
    if "phone" in data or "phone_number" in data:
        user.phone_number = (data.get("phone") or data.get("phone_number") or "").strip() or None
    if "address" in data:
        user.address = (data.get("address") or "").strip() or None

    if not user.full_name:
        return jsonify({"message": "full_name không được rỗng"}), 400

    db.session.commit()
    return jsonify({"message": "Cập nhật thành công", "user": user.to_dict()}), 200

@users_bp.put("/me/password")
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password") or ""
    new_password = data.get("new_password") or ""

    if not old_password or not new_password:
        return jsonify({"message": "old_password và new_password là bắt buộc"}), 400
    if len(new_password) < 6:
        return jsonify({"message": "Mật khẩu mới phải >= 6 ký tự"}), 400
    if not user.check_password(old_password):
        return jsonify({"message": "Mật khẩu cũ không đúng"}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Đổi mật khẩu thành công"}), 200