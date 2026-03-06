from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.brand import Brand
from app.models.evaluation_session import EvaluationSession
from app.models.evaluation_filter import EvaluationFilter
from app.models.laptop import Laptop
from app.models.evaluation_result import EvaluationResult
from app.models.ahp_criterion import AHPCriterion
from app.models.evaluation_pairwise_matrix import EvaluationPairwiseMatrix
from app.models.evaluation_weight import EvaluationWeight
from app.models.evaluation_result_detail import EvaluationResultDetail
from app.services.ai_model import predict_scores
from app.services.ahp import build_pairwise_matrix, calculate_ahp_weights

evaluations_bp = Blueprint("evaluations", __name__)


def to_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ["true", "1", "yes", "y"]:
            return True
        if v in ["false", "0", "no", "n"]:
            return False
    return default


def get_user_session_or_404(session_id: int, user_id: int):
    return EvaluationSession.query.filter_by(id=session_id, user_id=user_id).first()


def validate_filter_data(data):
    brand_id = data.get("brand_id")

    if brand_id is not None:
        brand = Brand.query.get(brand_id)
        if not brand:
            return "brand_id không tồn tại"

    pairs = [
        ("min_price", "max_price"),
        ("min_ssd_gb", "max_ssd_gb"),
        ("min_release_year", "max_release_year"),
        ("min_screen_size", "max_screen_size"),
    ]

    for min_field, max_field in pairs:
        min_value = data.get(min_field)
        max_value = data.get(max_field)
        if min_value is not None and max_value is not None:
            try:
                if float(min_value) > float(max_value):
                    return f"{min_field} không được lớn hơn {max_field}"
            except (TypeError, ValueError):
                return f"{min_field}/{max_field} không hợp lệ"

    return None


# =========================
# F) EVALUATION SESSION
# =========================

@evaluations_bp.post("")
@jwt_required()
def create_evaluation_session():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    budget_min = data.get("budget_min")
    budget_max = data.get("budget_max")

    if budget_min is not None and budget_max is not None:
        try:
            if float(budget_min) > float(budget_max):
                return jsonify({"message": "budget_min không được lớn hơn budget_max"}), 400
        except (TypeError, ValueError):
            return jsonify({"message": "budget_min / budget_max không hợp lệ"}), 400

    session = EvaluationSession(
        user_id=user_id,
        student_major=(data.get("student_major") or "").strip() or None,
        usage_needs=(data.get("usage_needs") or "").strip() or None,
        budget_min=budget_min,
        budget_max=budget_max,
        prefer_battery=to_bool(data.get("prefer_battery"), False),
        prefer_lightweight=to_bool(data.get("prefer_lightweight"), False),
        prefer_performance=to_bool(data.get("prefer_performance"), False),
        prefer_durability=to_bool(data.get("prefer_durability"), False),
        prefer_upgradeability=to_bool(data.get("prefer_upgradeability"), False),
        ai_enabled=to_bool(data.get("ai_enabled"), False),
    )

    db.session.add(session)
    db.session.commit()

    return jsonify({
        "message": "Tạo evaluation session thành công",
        "session": session.to_dict(include_recommended=True)
    }), 201


@evaluations_bp.get("")
@jwt_required()
def get_my_evaluation_sessions():
    user_id = int(get_jwt_identity())

    sessions = (
        EvaluationSession.query
        .filter_by(user_id=user_id)
        .order_by(EvaluationSession.id.desc())
        .all()
    )

    return jsonify([session.to_dict(include_recommended=True) for session in sessions]), 200


@evaluations_bp.get("/<int:session_id>")
@jwt_required()
def get_evaluation_session_detail(session_id: int):
    user_id = int(get_jwt_identity())

    session = EvaluationSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    return jsonify(session.to_dict(include_recommended=True)), 200


@evaluations_bp.delete("/<int:session_id>")
@jwt_required()
def delete_evaluation_session(session_id: int):
    user_id = int(get_jwt_identity())

    session = EvaluationSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    db.session.delete(session)
    db.session.commit()

    return jsonify({"message": "Xóa evaluation session thành công"}), 200


# =========================
# G) FILTER THEO NHU CẦU
# =========================

@evaluations_bp.post("/<int:session_id>/filters")
@jwt_required()
def create_evaluation_filter(session_id: int):
    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    existing_filter = EvaluationFilter.query.filter_by(evaluation_session_id=session_id).first()
    if existing_filter:
        return jsonify({"message": "Session này đã có filter, hãy dùng PUT để cập nhật"}), 409

    data = request.get_json(silent=True) or {}
    error = validate_filter_data(data)
    if error:
        return jsonify({"message": error}), 400

    filter_obj = EvaluationFilter(
        evaluation_session_id=session_id,
        brand_id=data.get("brand_id"),
        min_price=data.get("min_price"),
        max_price=data.get("max_price"),
        min_ssd_gb=data.get("min_ssd_gb"),
        max_ssd_gb=data.get("max_ssd_gb"),
        min_release_year=data.get("min_release_year"),
        max_release_year=data.get("max_release_year"),
        min_screen_size=data.get("min_screen_size"),
        max_screen_size=data.get("max_screen_size"),
        min_ports_count=data.get("min_ports_count"),
        condition_status=(data.get("condition_status") or "").strip() or None,
    )

    db.session.add(filter_obj)
    db.session.commit()

    return jsonify({
        "message": "Lưu filter thành công",
        "filter": filter_obj.to_dict(include_brand=True)
    }), 201


@evaluations_bp.put("/<int:session_id>/filters")
@jwt_required()
def update_evaluation_filter(session_id: int):
    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    filter_obj = EvaluationFilter.query.filter_by(evaluation_session_id=session_id).first()
    if not filter_obj:
        return jsonify({"message": "Session này chưa có filter, hãy dùng POST để tạo mới"}), 404

    data = request.get_json(silent=True) or {}
    error = validate_filter_data(data)
    if error:
        return jsonify({"message": error}), 400

    if "brand_id" in data:
        filter_obj.brand_id = data.get("brand_id")
    if "min_price" in data:
        filter_obj.min_price = data.get("min_price")
    if "max_price" in data:
        filter_obj.max_price = data.get("max_price")
    if "min_ssd_gb" in data:
        filter_obj.min_ssd_gb = data.get("min_ssd_gb")
    if "max_ssd_gb" in data:
        filter_obj.max_ssd_gb = data.get("max_ssd_gb")
    if "min_release_year" in data:
        filter_obj.min_release_year = data.get("min_release_year")
    if "max_release_year" in data:
        filter_obj.max_release_year = data.get("max_release_year")
    if "min_screen_size" in data:
        filter_obj.min_screen_size = data.get("min_screen_size")
    if "max_screen_size" in data:
        filter_obj.max_screen_size = data.get("max_screen_size")
    if "min_ports_count" in data:
        filter_obj.min_ports_count = data.get("min_ports_count")
    if "condition_status" in data:
        filter_obj.condition_status = (data.get("condition_status") or "").strip() or None

    db.session.commit()

    return jsonify({
        "message": "Cập nhật filter thành công",
        "filter": filter_obj.to_dict(include_brand=True)
    }), 200


@evaluations_bp.get("/<int:session_id>/filters")
@jwt_required()
def get_evaluation_filter(session_id: int):
    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    filter_obj = EvaluationFilter.query.filter_by(evaluation_session_id=session_id).first()
    if not filter_obj:
        return jsonify({"message": "Session này chưa có filter"}), 404

    return jsonify(filter_obj.to_dict(include_brand=True)), 200


@evaluations_bp.delete("/<int:session_id>/filters")
@jwt_required()
def delete_evaluation_filter(session_id: int):
    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    filter_obj = EvaluationFilter.query.filter_by(evaluation_session_id=session_id).first()
    if not filter_obj:
        return jsonify({"message": "Session này chưa có filter"}), 404

    db.session.delete(filter_obj)
    db.session.commit()

    return jsonify({"message": "Xóa filter thành công"}), 200


# =========================
# H) AI RECOMMEND SAU KHI LỌC
# =========================

@evaluations_bp.post("/<int:session_id>/ai-rank")
@jwt_required()
def ai_rank_laptops(session_id: int):
    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    data = request.get_json(silent=True) or {}

    # ưu tiên filter gửi trực tiếp; nếu không có thì dùng filter đã lưu
    direct_filter = data.get("filter")
    if direct_filter:
        error = validate_filter_data(direct_filter)
        if error:
            return jsonify({"message": error}), 400

        filter_data = direct_filter
    else:
        filter_obj = EvaluationFilter.query.filter_by(evaluation_session_id=session_id).first()
        if not filter_obj:
            return jsonify({"message": "Session chưa có filter"}), 400

        filter_data = {
            "brand_id": filter_obj.brand_id,
            "min_price": filter_obj.min_price,
            "max_price": filter_obj.max_price,
            "min_ssd_gb": filter_obj.min_ssd_gb,
            "max_ssd_gb": filter_obj.max_ssd_gb,
            "min_release_year": filter_obj.min_release_year,
            "max_release_year": filter_obj.max_release_year,
            "min_screen_size": filter_obj.min_screen_size,
            "max_screen_size": filter_obj.max_screen_size,
            "min_ports_count": filter_obj.min_ports_count,
            "condition_status": filter_obj.condition_status,
        }

    query = Laptop.query.filter(Laptop.is_active.is_(True))

    if filter_data.get("brand_id") is not None:
        query = query.filter(Laptop.brand_id == filter_data["brand_id"])

    if filter_data.get("min_price") is not None:
        query = query.filter(Laptop.price >= filter_data["min_price"])

    if filter_data.get("max_price") is not None:
        query = query.filter(Laptop.price <= filter_data["max_price"])

    if filter_data.get("min_ssd_gb") is not None:
        query = query.filter(Laptop.ssd_gb >= filter_data["min_ssd_gb"])

    if filter_data.get("max_ssd_gb") is not None:
        query = query.filter(Laptop.ssd_gb <= filter_data["max_ssd_gb"])

    if filter_data.get("min_release_year") is not None:
        query = query.filter(Laptop.release_year >= filter_data["min_release_year"])

    if filter_data.get("max_release_year") is not None:
        query = query.filter(Laptop.release_year <= filter_data["max_release_year"])

    if filter_data.get("min_screen_size") is not None:
        query = query.filter(Laptop.screen_size >= filter_data["min_screen_size"])

    if filter_data.get("max_screen_size") is not None:
        query = query.filter(Laptop.screen_size <= filter_data["max_screen_size"])

    if filter_data.get("min_ports_count") is not None:
        query = query.filter(Laptop.ports_count >= filter_data["min_ports_count"])

    if filter_data.get("condition_status"):
        query = query.filter(Laptop.condition_status == filter_data["condition_status"])

    laptops = query.all()

    if not laptops:
        return jsonify({"message": "Không có laptop phù hợp với bộ lọc"}), 404

    valid_laptops = []
    for laptop in laptops:
        needed = [
            laptop.norm_cpu,
            laptop.norm_ram,
            laptop.norm_gpu,
            laptop.norm_screen,
            laptop.norm_weight,
            laptop.norm_battery,
            laptop.norm_durability,
            laptop.norm_upgradeability,
            laptop.price,
        ]
        if all(v is not None for v in needed):
            valid_laptops.append(laptop)

    if not valid_laptops:
        return jsonify({"message": "Không có laptop đủ dữ liệu norm_* và price để AI xếp hạng"}), 400

    scores = predict_scores(valid_laptops)

    ranking = sorted(
        zip(valid_laptops, scores),
        key=lambda x: x[1],
        reverse=True
    )

    EvaluationResult.query.filter_by(evaluation_session_id=session_id).delete()

    created_results = []
    for idx, (laptop, score) in enumerate(ranking, start=1):
        result = EvaluationResult(
            evaluation_session_id=session_id,
            laptop_id=laptop.id,
            total_score=float(score),
            rank_position=idx
        )
        db.session.add(result)
        created_results.append({
            "laptop_id": laptop.id,
            "laptop_name": laptop.name,
            "score": float(score),
            "rank_position": idx
        })

    top_laptop = ranking[0][0]
    session.recommended_laptop_id = top_laptop.id
    session.ai_enabled = True

    db.session.commit()

    return jsonify({
        "message": "AI xếp hạng thành công",
        "recommended_laptop_id": top_laptop.id,
        "total_candidates": len(ranking),
        "results_preview": created_results[:10]
    }), 200

# 32. GET /api/evaluations/<session_id>/results
@evaluations_bp.get("/<int:session_id>/results")
@jwt_required()
def get_evaluation_results(session_id: int):
    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    results = (
        EvaluationResult.query
        .filter_by(evaluation_session_id=session_id)
        .order_by(EvaluationResult.rank_position.asc())
        .all()
    )

    return jsonify([result.to_dict() for result in results]), 200


# 33. GET /api/evaluations/<session_id>/recommended
@evaluations_bp.get("/<int:session_id>/recommended")
@jwt_required()
def get_recommended_laptop(session_id: int):
    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    if not session.recommended_laptop_id or not session.recommended_laptop:
        return jsonify({"message": "Session này chưa có laptop đề xuất"}), 404

    return jsonify({
        "session_id": session.id,
        "recommended_laptop_id": session.recommended_laptop_id,
        "recommended_laptop": session.recommended_laptop.to_dict(include_brand=True)
    }), 200


# 34. GET /api/evaluations/<session_id>/results/top?limit=10
@evaluations_bp.get("/<int:session_id>/results/top")
@jwt_required()
def get_top_evaluation_results(session_id: int):
    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    try:
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"message": "limit không hợp lệ"}), 400

    if limit <= 0:
        return jsonify({"message": "limit phải > 0"}), 400

    results = (
        EvaluationResult.query
        .filter_by(evaluation_session_id=session_id)
        .order_by(EvaluationResult.rank_position.asc())
        .limit(limit)
        .all()
    )

    return jsonify({
        "session_id": session_id,
        "limit": limit,
        "items": [result.to_dict() for result in results]
    }), 200


# 35. POST /api/evaluations/<session_id>/pairwise
@evaluations_bp.post("/<int:session_id>/pairwise")
@jwt_required()
def save_pairwise_matrix(session_id: int):
    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    data = request.get_json(silent=True) or {}
    items = data.get("items") or []

    if not isinstance(items, list) or not items:
        return jsonify({"message": "items là bắt buộc và phải là mảng"}), 400

    criterion_ids = {c.id for c in AHPCriterion.query.all()}

    try:
        EvaluationPairwiseMatrix.query.filter_by(evaluation_session_id=session_id).delete()

        for item in items:
            c1 = item.get("criterion_1_id")
            c2 = item.get("criterion_2_id")
            value = item.get("comparison_value")

            if c1 not in criterion_ids or c2 not in criterion_ids:
                return jsonify({"message": "criterion_1_id hoặc criterion_2_id không tồn tại"}), 400

            if c1 == c2:
                return jsonify({"message": "criterion_1_id không được trùng criterion_2_id"}), 400

            try:
                value = float(value)
            except (TypeError, ValueError):
                return jsonify({"message": "comparison_value không hợp lệ"}), 400

            if value <= 0:
                return jsonify({"message": "comparison_value phải > 0"}), 400

            row = EvaluationPairwiseMatrix(
                evaluation_session_id=session_id,
                criterion_1_id=c1,
                criterion_2_id=c2,
                comparison_value=value
            )
            db.session.add(row)

        db.session.commit()

        saved = (
            EvaluationPairwiseMatrix.query
            .filter_by(evaluation_session_id=session_id)
            .order_by(
                EvaluationPairwiseMatrix.criterion_1_id.asc(),
                EvaluationPairwiseMatrix.criterion_2_id.asc()
            )
            .all()
        )

        return jsonify({
            "message": "Lưu pairwise matrix thành công",
            "items": [x.to_dict() for x in saved]
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Lỗi khi lưu pairwise matrix: {str(e)}"}), 500


# 36. GET /api/evaluations/<session_id>/pairwise
@evaluations_bp.get("/<int:session_id>/pairwise")
@jwt_required()
def get_pairwise_matrix(session_id: int):
    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    items = (
        EvaluationPairwiseMatrix.query
        .filter_by(evaluation_session_id=session_id)
        .order_by(
            EvaluationPairwiseMatrix.criterion_1_id.asc(),
            EvaluationPairwiseMatrix.criterion_2_id.asc()
        )
        .all()
    )

    return jsonify([x.to_dict() for x in items]), 200


# 37. POST /api/evaluations/<session_id>/calculate-cr
@evaluations_bp.post("/<int:session_id>/calculate-cr")
@jwt_required()
def calculate_cr(session_id: int):
    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    criteria = AHPCriterion.query.order_by(AHPCriterion.id.asc()).all()
    if not criteria:
        return jsonify({"message": "Không có tiêu chí AHP"}), 400

    pairwise_rows = EvaluationPairwiseMatrix.query.filter_by(
        evaluation_session_id=session_id
    ).all()

    if not pairwise_rows:
        return jsonify({"message": "Session chưa có pairwise matrix"}), 400

    pairwise_items = [
        {
            "criterion_1_id": row.criterion_1_id,
            "criterion_2_id": row.criterion_2_id,
            "comparison_value": float(row.comparison_value),
        }
        for row in pairwise_rows
    ]

    matrix = build_pairwise_matrix(
        criteria_ids=[c.id for c in criteria],
        pairwise_items=pairwise_items
    )

    ahp_result = calculate_ahp_weights(matrix)

    # xóa weights cũ rồi lưu weights mới
    EvaluationWeight.query.filter_by(evaluation_session_id=session_id).delete()

    for criterion, weight in zip(criteria, ahp_result["weights"]):
        row = EvaluationWeight(
            evaluation_session_id=session_id,
            criterion_id=criterion.id,
            ai_suggested_weight=float(weight),
            user_final_weight=float(weight),
        )
        db.session.add(row)

    session.ci_value = ahp_result["ci"]
    session.cr_value = ahp_result["cr"]
    session.is_consistent = ahp_result["is_consistent"]

    db.session.commit()

    return jsonify({
        "message": "Tính CR/CI thành công",
        "lambda_max": ahp_result["lambda_max"],
        "ci": ahp_result["ci"],
        "cr": ahp_result["cr"],
        "is_consistent": ahp_result["is_consistent"],
        "weights": [
            {
                "criterion_id": criterion.id,
                "criterion_code": criterion.code,
                "criterion_name": criterion.name,
                "weight": weight
            }
            for criterion, weight in zip(criteria, ahp_result["weights"])
        ]
    }), 200


# 38. GET /api/evaluations/<session_id>/weights
@evaluations_bp.get("/<int:session_id>/weights")
@jwt_required()
def get_evaluation_weights(session_id: int):
    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    weights = (
        EvaluationWeight.query
        .filter_by(evaluation_session_id=session_id)
        .order_by(EvaluationWeight.criterion_id.asc())
        .all()
    )

    return jsonify([w.to_dict() for w in weights]), 200


# 39. PUT /api/evaluations/<session_id>/weights
@evaluations_bp.put("/<int:session_id>/weights")
@jwt_required()
def update_evaluation_weights(session_id: int):
    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    data = request.get_json(silent=True) or {}
    items = data.get("items") or []

    if not isinstance(items, list) or not items:
        return jsonify({"message": "items là bắt buộc và phải là mảng"}), 400

    existing_weights = {
        w.criterion_id: w
        for w in EvaluationWeight.query.filter_by(evaluation_session_id=session_id).all()
    }

    total = 0.0

    try:
        for item in items:
            criterion_id = item.get("criterion_id")
            if criterion_id not in existing_weights:
                return jsonify({"message": f"criterion_id {criterion_id} chưa có weight"}), 404

            if "user_final_weight" not in item:
                return jsonify({"message": "Thiếu user_final_weight"}), 400

            try:
                user_final_weight = float(item.get("user_final_weight"))
            except (TypeError, ValueError):
                return jsonify({"message": "user_final_weight không hợp lệ"}), 400

            if user_final_weight < 0:
                return jsonify({"message": "user_final_weight phải >= 0"}), 400

            total += user_final_weight

        # cập nhật sau khi validate xong
        for item in items:
            criterion_id = item.get("criterion_id")
            row = existing_weights[criterion_id]

            if "ai_suggested_weight" in item and item.get("ai_suggested_weight") is not None:
                row.ai_suggested_weight = float(item.get("ai_suggested_weight"))

            row.user_final_weight = float(item.get("user_final_weight"))

        db.session.commit()

        updated = (
            EvaluationWeight.query
            .filter_by(evaluation_session_id=session_id)
            .order_by(EvaluationWeight.criterion_id.asc())
            .all()
        )

        return jsonify({
            "message": "Cập nhật weights thành công",
            "sum_user_final_weight": total,
            "items": [w.to_dict() for w in updated]
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Lỗi khi cập nhật weights: {str(e)}"}), 500
    

# =========================
# K) XẾP HẠNG THEO AHP
# =========================

@evaluations_bp.post("/<int:session_id>/ahp-rank")
@jwt_required()
def ahp_rank_laptops(session_id: int):

    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Không tìm thấy session"}), 404

    filter_obj = EvaluationFilter.query.filter_by(
        evaluation_session_id=session_id
    ).first()

    weights = EvaluationWeight.query.filter_by(
        evaluation_session_id=session_id
    ).all()

    if not weights:
        return jsonify({"message": "Session chưa có weights"}), 400

    weight_map = {w.criterion.code: float(w.user_final_weight) for w in weights}

    query = Laptop.query.filter(Laptop.is_active == True)

    if filter_obj:
        if filter_obj.min_price:
            query = query.filter(Laptop.price >= filter_obj.min_price)
        if filter_obj.max_price:
            query = query.filter(Laptop.price <= filter_obj.max_price)

    laptops = query.all()

    if not laptops:
        return jsonify({"message": "Không có laptop phù hợp"}), 404

    # xóa ranking cũ
    EvaluationResult.query.filter_by(
        evaluation_session_id=session_id
    ).delete()

    results = []

    for laptop in laptops:

        score = 0
        details = []

        mapping = {
            "cpu": laptop.norm_cpu,
            "ram": laptop.norm_ram,
            "gpu": laptop.norm_gpu,
            "screen": laptop.norm_screen,
            "weight": laptop.norm_weight,
            "battery": laptop.norm_battery,
            "durability": laptop.norm_durability,
            "upgradeability": laptop.norm_upgradeability
        }

        for code, value in mapping.items():

            weight = weight_map.get(code, 0)

            if value is None:
                continue

            criterion_score = weight * float(value)

            score += criterion_score

            details.append({
                "criterion_code": code,
                "weight": weight,
                "value": float(value),
                "score": criterion_score
            })

        result = EvaluationResult(
            evaluation_session_id=session_id,
            laptop_id=laptop.id,
            total_score=score,
            rank_position=0
        )

        db.session.add(result)
        db.session.flush()

        for d in details:

            criterion = AHPCriterion.query.filter_by(code=d["criterion_code"]).first()

            row = EvaluationResultDetail(
                evaluation_result_id=result.id,
                criterion_id=criterion.id,
                criterion_weight=d["weight"],
                laptop_value_normalized=d["value"],
                criterion_score=d["score"]
            )

            db.session.add(row)

        results.append((result, score))

    # sort ranking
    results.sort(key=lambda x: x[1], reverse=True)

    for i, (result, _) in enumerate(results, start=1):
        result.rank_position = i

    session.recommended_laptop_id = results[0][0].laptop_id

    db.session.commit()

    return jsonify({
        "message": "AHP ranking completed",
        "recommended_laptop_id": session.recommended_laptop_id,
        "total_candidates": len(results)
    }), 200

@evaluations_bp.get("/<int:session_id>/results/<int:result_id>/details")
@jwt_required()
def get_result_details(session_id: int, result_id: int):

    user_id = int(get_jwt_identity())

    session = get_user_session_or_404(session_id, user_id)
    if not session:
        return jsonify({"message": "Session không tồn tại"}), 404

    details = EvaluationResultDetail.query.filter_by(
        evaluation_result_id=result_id
    ).all()

    return jsonify([d.to_dict() for d in details])