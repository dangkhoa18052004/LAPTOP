from app.extensions import db


class EvaluationFilter(db.Model):
    __tablename__ = "evaluation_filters"

    id = db.Column(db.BigInteger, primary_key=True)

    evaluation_session_id = db.Column(
        db.BigInteger,
        db.ForeignKey("evaluation_sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    brand_id = db.Column(
        db.BigInteger,
        db.ForeignKey("brands.id", ondelete="SET NULL"),
        nullable=True
    )

    min_price = db.Column(db.Numeric(15, 2))
    max_price = db.Column(db.Numeric(15, 2))

    min_ssd_gb = db.Column(db.Integer)
    max_ssd_gb = db.Column(db.Integer)

    min_release_year = db.Column(db.Integer)
    max_release_year = db.Column(db.Integer)

    min_screen_size = db.Column(db.Numeric(4, 1))
    max_screen_size = db.Column(db.Numeric(4, 1))

    min_ports_count = db.Column(db.Integer)
    condition_status = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    session = db.relationship("EvaluationSession", backref=db.backref("filters", lazy=True))
    brand = db.relationship("Brand")

    def to_dict(self, include_brand=False):
        data = {
            "id": self.id,
            "evaluation_session_id": self.evaluation_session_id,
            "brand_id": self.brand_id,
            "min_price": float(self.min_price) if self.min_price is not None else None,
            "max_price": float(self.max_price) if self.max_price is not None else None,
            "min_ssd_gb": self.min_ssd_gb,
            "max_ssd_gb": self.max_ssd_gb,
            "min_release_year": self.min_release_year,
            "max_release_year": self.max_release_year,
            "min_screen_size": float(self.min_screen_size) if self.min_screen_size is not None else None,
            "max_screen_size": float(self.max_screen_size) if self.max_screen_size is not None else None,
            "min_ports_count": self.min_ports_count,
            "condition_status": self.condition_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_brand:
            data["brand"] = self.brand.to_dict() if self.brand else None

        return data