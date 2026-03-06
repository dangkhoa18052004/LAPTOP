from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.review import Review
from app.models.laptop import Laptop

reviews_bp = Blueprint("reviews", __name__)

@reviews_bp.post("/laptops/<int:laptop_id>")
@jwt_required()
def create_review(laptop_id):
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    rating = data.get("rating")
    comment = data.get("comment")

    if rating is None or not (1 <= int(rating) <= 5):
        return jsonify({"message": "rating phải từ 1 đến 5"}), 400

    laptop = Laptop.query.get(laptop_id)
    if not laptop:
        return jsonify({"message": "Laptop không tồn tại"}), 404

    # mỗi user chỉ review 1 lần
    existing = Review.query.filter_by(
        user_id=user_id,
        laptop_id=laptop_id
    ).first()

    if existing:
        return jsonify({"message": "Bạn đã review laptop này"}), 409

    review = Review(
        user_id=user_id,
        laptop_id=laptop_id,
        rating=rating,
        comment=comment
    )

    db.session.add(review)
    db.session.commit()

    return jsonify({
        "message": "Tạo review thành công",
        "review": review.to_dict()
    }), 201

@reviews_bp.get("/laptops/<int:laptop_id>")
def get_laptop_reviews(laptop_id):

    reviews = (
        Review.query
        .filter_by(laptop_id=laptop_id)
        .order_by(Review.created_at.desc())
        .all()
    )

    return jsonify([r.to_dict() for r in reviews]), 200

@reviews_bp.put("/<int:review_id>")
@jwt_required()
def update_review(review_id):

    user_id = int(get_jwt_identity())
    review = Review.query.get_or_404(review_id)

    if review.user_id != user_id:
        return jsonify({"message": "Không có quyền sửa review này"}), 403

    data = request.get_json() or {}

    rating = data.get("rating")
    comment = data.get("comment")

    if rating is not None:
        if not (1 <= int(rating) <= 5):
            return jsonify({"message": "rating phải từ 1 đến 5"}), 400
        review.rating = rating

    if comment is not None:
        review.comment = comment

    db.session.commit()

    return jsonify({
        "message": "Cập nhật review thành công",
        "review": review.to_dict()
    }), 200

@reviews_bp.delete("/<int:review_id>")
@jwt_required()
def delete_review(review_id):

    user_id = int(get_jwt_identity())
    review = Review.query.get_or_404(review_id)

    if review.user_id != user_id:
        return jsonify({"message": "Không có quyền xóa review"}), 403

    db.session.delete(review)
    db.session.commit()

    return jsonify({"message": "Xóa review thành công"}), 200