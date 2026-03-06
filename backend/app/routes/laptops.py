from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.brand import Brand
from app.models.laptop import Laptop
from app.utils.authz import admin_required

laptops_bp = Blueprint("laptops", __name__)


def parse_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# 13. GET /api/laptops
@laptops_bp.get("")
def get_laptops():
    query = Laptop.query.outerjoin(Brand, Laptop.brand_id == Brand.id)

    # query params
    keyword = (request.args.get("keyword") or "").strip()
    brand_id = parse_int(request.args.get("brand_id"))
    min_price = parse_float(request.args.get("min_price"))
    max_price = parse_float(request.args.get("max_price"))
    min_ssd = parse_int(request.args.get("min_ssd"))
    max_ssd = parse_int(request.args.get("max_ssd"))
    year = parse_int(request.args.get("year"))
    min_year = parse_int(request.args.get("min_year"))
    max_year = parse_int(request.args.get("max_year"))
    screen = parse_float(request.args.get("screen"))
    min_screen = parse_float(request.args.get("min_screen"))
    max_screen = parse_float(request.args.get("max_screen"))
    condition_status = (request.args.get("condition") or request.args.get("condition_status") or "").strip()
    is_active = request.args.get("is_active")

    if keyword:
        like_keyword = f"%{keyword}%"
        query = query.filter(
            db.or_(
                Laptop.name.ilike(like_keyword),
                Laptop.model_code.ilike(like_keyword),
                Laptop.cpu.ilike(like_keyword),
                Laptop.gpu.ilike(like_keyword),
                Brand.name.ilike(like_keyword)
            )
        )

    if brand_id is not None:
        query = query.filter(Laptop.brand_id == brand_id)

    if min_price is not None:
        query = query.filter(Laptop.price >= min_price)

    if max_price is not None:
        query = query.filter(Laptop.price <= max_price)

    if min_ssd is not None:
        query = query.filter(Laptop.ssd_gb >= min_ssd)

    if max_ssd is not None:
        query = query.filter(Laptop.ssd_gb <= max_ssd)

    if year is not None:
        query = query.filter(Laptop.release_year == year)

    if min_year is not None:
        query = query.filter(Laptop.release_year >= min_year)

    if max_year is not None:
        query = query.filter(Laptop.release_year <= max_year)

    if screen is not None:
        query = query.filter(Laptop.screen_size == screen)

    if min_screen is not None:
        query = query.filter(Laptop.screen_size >= min_screen)

    if max_screen is not None:
        query = query.filter(Laptop.screen_size <= max_screen)

    if condition_status:
        query = query.filter(Laptop.condition_status == condition_status)

    # mặc định chỉ lấy laptop đang active cho public
    if is_active is None:
        query = query.filter(Laptop.is_active.is_(True))
    else:
        if is_active.lower() in ["true", "1"]:
            query = query.filter(Laptop.is_active.is_(True))
        elif is_active.lower() in ["false", "0"]:
            query = query.filter(Laptop.is_active.is_(False))

    laptops = query.order_by(Laptop.id.desc()).all()
    return jsonify([laptop.to_dict(include_brand=True) for laptop in laptops]), 200


# 14. GET /api/laptops/<id>
@laptops_bp.get("/<int:laptop_id>")
def get_laptop_detail(laptop_id: int):
    laptop = Laptop.query.get_or_404(laptop_id)
    return jsonify(laptop.to_dict(include_brand=True)), 200


# 15. POST /api/laptops (admin)
@laptops_bp.post("")
@jwt_required()
@admin_required
def create_laptop():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    cpu = (data.get("cpu") or "").strip()
    ram_gb = data.get("ram_gb")
    ssd_gb = data.get("ssd_gb")
    price = data.get("price")

    if not name or not cpu or ram_gb is None or ssd_gb is None or price is None:
        return jsonify({"message": "name, cpu, ram_gb, ssd_gb, price là bắt buộc"}), 400

    brand_id = data.get("brand_id")
    if brand_id is not None:
        brand = Brand.query.get(brand_id)
        if not brand:
            return jsonify({"message": "brand_id không tồn tại"}), 400

    laptop = Laptop(
        brand_id=brand_id,
        name=name,
        model_code=(data.get("model_code") or "").strip() or None,
        cpu=cpu,
        ram_gb=ram_gb,
        gpu=(data.get("gpu") or "").strip() or None,
        ssd_gb=ssd_gb,
        screen_size=data.get("screen_size"),
        screen_resolution=(data.get("screen_resolution") or "").strip() or None,
        weight_kg=data.get("weight_kg"),
        battery_hours=data.get("battery_hours"),
        durability_score=data.get("durability_score"),
        upgradeability_score=data.get("upgradeability_score"),
        price=price,
        stock_quantity=data.get("stock_quantity", 0),
        release_year=data.get("release_year"),
        ports_count=data.get("ports_count", 0),
        condition_status=(data.get("condition_status") or "new").strip(),
        description=(data.get("description") or "").strip() or None,
        image_url=(data.get("image_url") or "").strip() or None,
        norm_cpu=data.get("norm_cpu"),
        norm_ram=data.get("norm_ram"),
        norm_gpu=data.get("norm_gpu"),
        norm_screen=data.get("norm_screen"),
        norm_weight=data.get("norm_weight"),
        norm_battery=data.get("norm_battery"),
        norm_durability=data.get("norm_durability"),
        norm_upgradeability=data.get("norm_upgradeability"),
        ahp_score=data.get("ahp_score"),
        is_active=data.get("is_active", True),
    )

    db.session.add(laptop)
    db.session.commit()

    return jsonify({
        "message": "Tạo laptop thành công",
        "laptop": laptop.to_dict(include_brand=True)
    }), 201


# 16. PUT /api/laptops/<id> (admin)
@laptops_bp.put("/<int:laptop_id>")
@jwt_required()
@admin_required
def update_laptop(laptop_id: int):
    laptop = Laptop.query.get_or_404(laptop_id)
    data = request.get_json(silent=True) or {}

    if "brand_id" in data:
        brand_id = data.get("brand_id")
        if brand_id is not None:
            brand = Brand.query.get(brand_id)
            if not brand:
                return jsonify({"message": "brand_id không tồn tại"}), 400
        laptop.brand_id = brand_id

    if "name" in data:
        laptop.name = (data.get("name") or "").strip()
        if not laptop.name:
            return jsonify({"message": "name không được rỗng"}), 400

    if "model_code" in data:
        laptop.model_code = (data.get("model_code") or "").strip() or None

    if "cpu" in data:
        laptop.cpu = (data.get("cpu") or "").strip()
        if not laptop.cpu:
            return jsonify({"message": "cpu không được rỗng"}), 400

    if "ram_gb" in data:
        laptop.ram_gb = data.get("ram_gb")

    if "gpu" in data:
        laptop.gpu = (data.get("gpu") or "").strip() or None

    if "ssd_gb" in data:
        laptop.ssd_gb = data.get("ssd_gb")

    if "screen_size" in data:
        laptop.screen_size = data.get("screen_size")

    if "screen_resolution" in data:
        laptop.screen_resolution = (data.get("screen_resolution") or "").strip() or None

    if "weight_kg" in data:
        laptop.weight_kg = data.get("weight_kg")

    if "battery_hours" in data:
        laptop.battery_hours = data.get("battery_hours")

    if "durability_score" in data:
        laptop.durability_score = data.get("durability_score")

    if "upgradeability_score" in data:
        laptop.upgradeability_score = data.get("upgradeability_score")

    if "price" in data:
        laptop.price = data.get("price")

    if "stock_quantity" in data:
        laptop.stock_quantity = data.get("stock_quantity")

    if "release_year" in data:
        laptop.release_year = data.get("release_year")

    if "ports_count" in data:
        laptop.ports_count = data.get("ports_count")

    if "condition_status" in data:
        laptop.condition_status = (data.get("condition_status") or "").strip()

    if "description" in data:
        laptop.description = (data.get("description") or "").strip() or None

    if "image_url" in data:
        laptop.image_url = (data.get("image_url") or "").strip() or None

    if "norm_cpu" in data:
        laptop.norm_cpu = data.get("norm_cpu")
    if "norm_ram" in data:
        laptop.norm_ram = data.get("norm_ram")
    if "norm_gpu" in data:
        laptop.norm_gpu = data.get("norm_gpu")
    if "norm_screen" in data:
        laptop.norm_screen = data.get("norm_screen")
    if "norm_weight" in data:
        laptop.norm_weight = data.get("norm_weight")
    if "norm_battery" in data:
        laptop.norm_battery = data.get("norm_battery")
    if "norm_durability" in data:
        laptop.norm_durability = data.get("norm_durability")
    if "norm_upgradeability" in data:
        laptop.norm_upgradeability = data.get("norm_upgradeability")
    if "ahp_score" in data:
        laptop.ahp_score = data.get("ahp_score")

    if "is_active" in data:
        laptop.is_active = bool(data.get("is_active"))

    db.session.commit()

    return jsonify({
        "message": "Cập nhật laptop thành công",
        "laptop": laptop.to_dict(include_brand=True)
    }), 200


# 17. DELETE /api/laptops/<id> (admin)
@laptops_bp.delete("/<int:laptop_id>")
@jwt_required()
@admin_required
def delete_laptop(laptop_id: int):
    laptop = Laptop.query.get_or_404(laptop_id)

    db.session.delete(laptop)
    db.session.commit()

    return jsonify({"message": "Xóa laptop thành công"}), 200


# 18. PATCH /api/laptops/<id>/stock (admin)
@laptops_bp.patch("/<int:laptop_id>/stock")
@jwt_required()
@admin_required
def update_laptop_stock(laptop_id: int):
    laptop = Laptop.query.get_or_404(laptop_id)
    data = request.get_json(silent=True) or {}

    if "stock_quantity" not in data:
        return jsonify({"message": "stock_quantity là bắt buộc"}), 400

    stock_quantity = data.get("stock_quantity")
    if not isinstance(stock_quantity, int) or stock_quantity < 0:
        return jsonify({"message": "stock_quantity phải là số nguyên >= 0"}), 400

    laptop.stock_quantity = stock_quantity
    db.session.commit()

    return jsonify({
        "message": "Cập nhật tồn kho thành công",
        "laptop": laptop.to_dict(include_brand=True)
    }), 200


# 19. PATCH /api/laptops/<id>/active (admin)
@laptops_bp.patch("/<int:laptop_id>/active")
@jwt_required()
@admin_required
def update_laptop_active(laptop_id: int):
    laptop = Laptop.query.get_or_404(laptop_id)
    data = request.get_json(silent=True) or {}

    if "is_active" not in data:
        return jsonify({"message": "is_active là bắt buộc"}), 400

    laptop.is_active = bool(data.get("is_active"))
    db.session.commit()

    return jsonify({
        "message": "Cập nhật trạng thái hiển thị thành công",
        "laptop": laptop.to_dict(include_brand=True)
    }), 200