from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.extensions import db
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not full_name or not email or not password:
        return jsonify({"message": "full_name, email, password là bắt buộc"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email đã tồn tại"}), 409

    user = User(full_name=full_name, email=email, role="user")
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Tạo tài khoản thành công", "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "email và password là bắt buộc"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"message": "Sai email hoặc mật khẩu"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )

    return jsonify({"access_token": access_token, "user": user.to_dict()}), 200