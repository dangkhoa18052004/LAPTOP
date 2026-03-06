import math
import pandas as pd

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.brand import Brand
from app.models.laptop import Laptop
from app.models.laptop_import_log import LaptopImportLog
from app.utils.authz import admin_required

imports_bp = Blueprint("imports", __name__)


def clean_value(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value if value != "" else None
    return value


def to_int(value, default=None):
    value = clean_value(value)
    if value is None:
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def to_float(value, default=None):
    value = clean_value(value)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_bool(value, default=True):
    value = clean_value(value)
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    if isinstance(value, str):
        v = value.lower()
        if v in ["true", "1", "yes", "y"]:
            return True
        if v in ["false", "0", "no", "n"]:
            return False

    return default


def get_or_create_brand(brand_name):
    brand_name = clean_value(brand_name)
    if not brand_name:
        return None

    brand = Brand.query.filter(db.func.lower(Brand.name) == str(brand_name).lower()).first()
    if brand:
        return brand

    brand = Brand(name=str(brand_name).strip())
    db.session.add(brand)
    db.session.flush()
    return brand


def find_existing_laptop(name, model_code, cpu=None, ram_gb=None, ssd_gb=None):
    name = clean_value(name)
    model_code = clean_value(model_code)

    if name and model_code:
        existing = Laptop.query.filter(
            db.func.lower(Laptop.name) == str(name).lower(),
            db.func.lower(Laptop.model_code) == str(model_code).lower()
        ).first()
        if existing:
            return existing

    if name and cpu and ram_gb is not None and ssd_gb is not None:
        existing = Laptop.query.filter(
            db.func.lower(Laptop.name) == str(name).lower(),
            db.func.lower(Laptop.cpu) == str(cpu).lower(),
            Laptop.ram_gb == ram_gb,
            Laptop.ssd_gb == ssd_gb
        ).first()
        if existing:
            return existing

    return None


@imports_bp.post("/laptops-excel")
@jwt_required()
@admin_required
def import_laptops_excel():
    user_id = int(get_jwt_identity())

    if "file" not in request.files:
        return jsonify({"message": "Thiếu file upload (field name phải là 'file')"}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"message": "File không hợp lệ"}), 400

    if not file.filename.lower().endswith((".xlsx", ".xls")):
        return jsonify({"message": "Chỉ hỗ trợ file Excel .xlsx hoặc .xls"}), 400

    try:
        df = pd.read_excel(file, sheet_name="Laptop_Data")
    except ValueError:
        return jsonify({"message": "Không tìm thấy sheet 'Laptop_Data'"}), 400
    except Exception as e:
        return jsonify({"message": f"Không đọc được file Excel: {str(e)}"}), 400

    if df.empty:
        return jsonify({"message": "Sheet 'Laptop_Data' không có dữ liệu"}), 400

    df.columns = [str(col).strip() for col in df.columns]

    required_columns = [
        "Company",
        "Full Name",
        "TypeName",
        "Release Year",
        "Condition",
        "Price (VND)",
        "SSD (GB)",
        "RAM (GB)",
        "CPU_Company",
        "CPU_Type"
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return jsonify({
            "message": "Thiếu cột bắt buộc trong file Excel",
            "missing_columns": missing_columns
        }), 400

    total_rows = len(df)
    success_rows = 0
    failed_rows = 0
    error_messages = []

    try:
        for index, row in df.iterrows():
            row_no = index + 2

            try:
                brand_name = clean_value(row.get("Company"))
                name = clean_value(row.get("Full Name")) or clean_value(row.get("Product"))
                model_code = clean_value(row.get("TypeName"))

                cpu_company = clean_value(row.get("CPU_Company"))
                cpu_type = clean_value(row.get("CPU_Type"))
                cpu = " ".join([x for x in [cpu_company, cpu_type] if x])

                gpu_company = clean_value(row.get("GPU_Company"))
                gpu_type = clean_value(row.get("GPU_Type"))
                gpu = " ".join([x for x in [gpu_company, gpu_type] if x]) or None

                ram_gb = to_int(row.get("RAM (GB)"))
                ssd_gb = to_int(row.get("SSD (GB)"))
                price = to_float(row.get("Price (VND)"))

                if not name or not cpu or ram_gb is None or ssd_gb is None or price is None:
                    raise ValueError("Thiếu dữ liệu bắt buộc: name/cpu/ram_gb/ssd_gb/price")

                brand = get_or_create_brand(brand_name)

                laptop = find_existing_laptop(
                    name=name,
                    model_code=model_code,
                    cpu=cpu,
                    ram_gb=ram_gb,
                    ssd_gb=ssd_gb
                )

                laptop_data = {
                    "brand_id": brand.id if brand else None,
                    "name": name,
                    "model_code": model_code,
                    "cpu": cpu,
                    "gpu": gpu,
                    "ram_gb": ram_gb,
                    "ssd_gb": ssd_gb,
                    "screen_size": to_float(row.get("Inches")),
                    "screen_resolution": clean_value(row.get("ScreenResolution")),
                    "weight_kg": to_float(row.get("Weight (kg)")),
                    "battery_hours": to_float(row.get("Battery (hrs)")),
                    "durability_score": to_float(row.get("Durability (1-10)")),
                    "upgradeability_score": to_float(row.get("Upgradability (1-10)")),
                    "price": price,
                    "stock_quantity": 0,
                    "release_year": to_int(row.get("Release Year")),
                    "ports_count": to_int(row.get("Ports (#)"), 0),
                    "condition_status": clean_value(row.get("Condition")) or "new",
                    "description": None,
                    "image_url": None,
                    "norm_cpu": to_float(row.get("Norm_CPU")),
                    "norm_ram": to_float(row.get("Norm_RAM")),
                    "norm_gpu": to_float(row.get("Norm_GPU")),
                    "norm_screen": to_float(row.get("Norm_Screen")),
                    "norm_weight": to_float(row.get("Norm_Weight")),
                    "norm_battery": to_float(row.get("Norm_Battery")),
                    "norm_durability": to_float(row.get("Norm_Durability")),
                    "norm_upgradeability": to_float(row.get("Norm_Upgrade")),
                    "ahp_score": to_float(row.get("AHP Score")),
                    "is_active": True
                }

                if laptop:
                    for key, value in laptop_data.items():
                        setattr(laptop, key, value)
                else:
                    laptop = Laptop(**laptop_data)
                    db.session.add(laptop)

                success_rows += 1

            except Exception as row_error:
                failed_rows += 1
                error_messages.append(f"Dòng {row_no}: {str(row_error)}")

        note = None
        if error_messages:
            note = " | ".join(error_messages[:20])

        log = LaptopImportLog(
            file_name=file.filename,
            imported_by=user_id,
            total_rows=total_rows,
            success_rows=success_rows,
            failed_rows=failed_rows,
            note=note
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "message": "Import Excel thành công",
            "summary": {
                "file_name": file.filename,
                "total_rows": total_rows,
                "success_rows": success_rows,
                "failed_rows": failed_rows
            },
            "errors": error_messages[:20],
            "log": log.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Lỗi trong quá trình import: {str(e)}"}), 500


@imports_bp.get("/logs")
@jwt_required()
@admin_required
def get_import_logs():
    logs = LaptopImportLog.query.order_by(LaptopImportLog.id.desc()).all()
    return jsonify([log.to_dict() for log in logs]), 200