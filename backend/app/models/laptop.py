from app.extensions import db


class Laptop(db.Model):
    __tablename__ = "laptops"

    id = db.Column(db.BigInteger, primary_key=True)

    brand_id = db.Column(
        db.BigInteger,
        db.ForeignKey("brands.id", ondelete="SET NULL"),
        nullable=True
    )

    name = db.Column(db.String(255), nullable=False)
    model_code = db.Column(db.String(100))

    cpu = db.Column(db.String(150), nullable=False)
    ram_gb = db.Column(db.Integer, nullable=False)
    gpu = db.Column(db.String(150))
    ssd_gb = db.Column(db.Integer, nullable=False)
    screen_size = db.Column(db.Numeric(4, 1))
    screen_resolution = db.Column(db.String(50))
    weight_kg = db.Column(db.Numeric(4, 2))
    battery_hours = db.Column(db.Numeric(4, 1))
    durability_score = db.Column(db.Numeric(4, 2))
    upgradeability_score = db.Column(db.Numeric(4, 2))

    price = db.Column(db.Numeric(15, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    release_year = db.Column(db.Integer)
    ports_count = db.Column(db.Integer, default=0)
    condition_status = db.Column(db.String(20), nullable=False, default="new")

    description = db.Column(db.Text)
    image_url = db.Column(db.Text)

    norm_cpu = db.Column(db.Numeric(10, 6))
    norm_ram = db.Column(db.Numeric(10, 6))
    norm_gpu = db.Column(db.Numeric(10, 6))
    norm_screen = db.Column(db.Numeric(10, 6))
    norm_weight = db.Column(db.Numeric(10, 6))
    norm_battery = db.Column(db.Numeric(10, 6))
    norm_durability = db.Column(db.Numeric(10, 6))
    norm_upgradeability = db.Column(db.Numeric(10, 6))

    ahp_score = db.Column(db.Numeric(10, 6))

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    brand = db.relationship("Brand", backref=db.backref("laptops", lazy=True))

    def to_dict(self, include_brand=False):
        data = {
            "id": self.id,
            "brand_id": self.brand_id,
            "name": self.name,
            "model_code": self.model_code,
            "cpu": self.cpu,
            "ram_gb": self.ram_gb,
            "gpu": self.gpu,
            "ssd_gb": self.ssd_gb,
            "screen_size": float(self.screen_size) if self.screen_size is not None else None,
            "screen_resolution": self.screen_resolution,
            "weight_kg": float(self.weight_kg) if self.weight_kg is not None else None,
            "battery_hours": float(self.battery_hours) if self.battery_hours is not None else None,
            "durability_score": float(self.durability_score) if self.durability_score is not None else None,
            "upgradeability_score": float(self.upgradeability_score) if self.upgradeability_score is not None else None,
            "price": float(self.price) if self.price is not None else None,
            "stock_quantity": self.stock_quantity,
            "release_year": self.release_year,
            "ports_count": self.ports_count,
            "condition_status": self.condition_status,
            "description": self.description,
            "image_url": self.image_url,
            "norm_cpu": float(self.norm_cpu) if self.norm_cpu is not None else None,
            "norm_ram": float(self.norm_ram) if self.norm_ram is not None else None,
            "norm_gpu": float(self.norm_gpu) if self.norm_gpu is not None else None,
            "norm_screen": float(self.norm_screen) if self.norm_screen is not None else None,
            "norm_weight": float(self.norm_weight) if self.norm_weight is not None else None,
            "norm_battery": float(self.norm_battery) if self.norm_battery is not None else None,
            "norm_durability": float(self.norm_durability) if self.norm_durability is not None else None,
            "norm_upgradeability": float(self.norm_upgradeability) if self.norm_upgradeability is not None else None,
            "ahp_score": float(self.ahp_score) if self.ahp_score is not None else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_brand:
            data["brand"] = self.brand.to_dict() if self.brand else None

        return data