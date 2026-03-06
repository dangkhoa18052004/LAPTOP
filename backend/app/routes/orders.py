from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.laptop import Laptop
from app.utils.authz import admin_required

orders_bp = Blueprint("orders", __name__)


VALID_ORDER_STATUS = ["pending", "processing", "shipped", "delivered", "cancelled"]
VALID_PAYMENT_STATUS = ["unpaid", "paid"]
VALID_PAYMENT_METHOD = ["cod", "banking"]


# 42. POST /api/orders
@orders_bp.post("")
@jwt_required()
def create_order():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    shipping_address = (data.get("shipping_address") or "").strip()
    shipping_phone = (data.get("shipping_phone") or "").strip()
    payment_method = (data.get("payment_method") or "cod").strip().lower()
    items = data.get("items") or []

    if not shipping_address or not shipping_phone:
        return jsonify({"message": "shipping_address và shipping_phone là bắt buộc"}), 400

    if payment_method not in VALID_PAYMENT_METHOD:
        return jsonify({"message": "payment_method chỉ được 'cod' hoặc 'banking'"}), 400

    if not isinstance(items, list) or not items:
        return jsonify({"message": "items là bắt buộc và phải là mảng"}), 400

    total_amount = 0
    order_items_to_create = []

    try:
        for item in items:
            laptop_id = item.get("laptop_id")
            quantity = item.get("quantity", 1)

            if laptop_id is None:
                return jsonify({"message": "Thiếu laptop_id trong items"}), 400

            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                return jsonify({"message": "quantity phải là số nguyên"}), 400

            if quantity <= 0:
                return jsonify({"message": "quantity phải > 0"}), 400

            laptop = Laptop.query.get(laptop_id)
            if not laptop:
                return jsonify({"message": f"Laptop id={laptop_id} không tồn tại"}), 404

            if not laptop.is_active:
                return jsonify({"message": f"Laptop id={laptop_id} đang bị ẩn"}), 400

            # tùy chọn: check tồn kho
            if laptop.stock_quantity is not None and laptop.stock_quantity < quantity:
                return jsonify({"message": f"Laptop id={laptop_id} không đủ tồn kho"}), 400

            line_total = float(laptop.price) * quantity
            total_amount += line_total

            order_items_to_create.append({
                "laptop": laptop,
                "quantity": quantity,
                "price_at_purchase": float(laptop.price)
            })

        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            status="pending",
            shipping_address=shipping_address,
            shipping_phone=shipping_phone,
            payment_method=payment_method,
            payment_status="unpaid"
        )
        db.session.add(order)
        db.session.flush()

        for item_data in order_items_to_create:
            order_item = OrderItem(
                order_id=order.id,
                laptop_id=item_data["laptop"].id,
                quantity=item_data["quantity"],
                price_at_purchase=item_data["price_at_purchase"]
            )
            db.session.add(order_item)

            # tùy chọn: trừ tồn kho
            item_data["laptop"].stock_quantity -= item_data["quantity"]

        db.session.commit()

        return jsonify({
            "message": "Tạo order thành công",
            "order": order.to_dict(include_items=True)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Lỗi khi tạo order: {str(e)}"}), 500


# 43. GET /api/orders
@orders_bp.get("")
@jwt_required()
def get_my_orders():
    user_id = int(get_jwt_identity())

    orders = (
        Order.query
        .filter_by(user_id=user_id)
        .order_by(Order.id.desc())
        .all()
    )

    return jsonify([order.to_dict(include_items=False) for order in orders]), 200


# 44. GET /api/orders/<order_id>
@orders_bp.get("/<int:order_id>")
@jwt_required()
def get_order_detail(order_id: int):
    user_id = int(get_jwt_identity())

    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"message": "Không tìm thấy order"}), 404

    return jsonify(order.to_dict(include_items=True)), 200


# 45. PUT /api/orders/<order_id>/status (admin)
@orders_bp.put("/<int:order_id>/status")
@jwt_required()
@admin_required
def update_order_status(order_id: int):
    order = Order.query.get_or_404(order_id)
    data = request.get_json(silent=True) or {}

    status = (data.get("status") or "").strip().lower()
    if status not in VALID_ORDER_STATUS:
        return jsonify({"message": f"status phải thuộc {VALID_ORDER_STATUS}"}), 400

    order.status = status
    db.session.commit()

    return jsonify({
        "message": "Cập nhật trạng thái order thành công",
        "order": order.to_dict(include_items=True)
    }), 200


# 46. PUT /api/orders/<order_id>/payment (admin)
@orders_bp.put("/<int:order_id>/payment")
@jwt_required()
@admin_required
def update_order_payment(order_id: int):
    order = Order.query.get_or_404(order_id)
    data = request.get_json(silent=True) or {}

    payment_status = (data.get("payment_status") or "").strip().lower()
    if payment_status not in VALID_PAYMENT_STATUS:
        return jsonify({"message": f"payment_status phải thuộc {VALID_PAYMENT_STATUS}"}), 400

    order.payment_status = payment_status
    db.session.commit()

    return jsonify({
        "message": "Cập nhật payment_status thành công",
        "order": order.to_dict(include_items=True)
    }), 200