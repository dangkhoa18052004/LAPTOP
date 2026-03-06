from app.extensions import db


class EvaluationSession(db.Model):
    __tablename__ = "evaluation_sessions"

    id = db.Column(db.BigInteger, primary_key=True)

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    student_major = db.Column(db.String(100))
    usage_needs = db.Column(db.String(255))
    budget_min = db.Column(db.Numeric(15, 2))
    budget_max = db.Column(db.Numeric(15, 2))

    prefer_battery = db.Column(db.Boolean, default=False)
    prefer_lightweight = db.Column(db.Boolean, default=False)
    prefer_performance = db.Column(db.Boolean, default=False)
    prefer_durability = db.Column(db.Boolean, default=False)
    prefer_upgradeability = db.Column(db.Boolean, default=False)

    ai_enabled = db.Column(db.Boolean, default=False)
    cr_value = db.Column(db.Numeric(10, 6))
    ci_value = db.Column(db.Numeric(10, 6))
    is_consistent = db.Column(db.Boolean, default=False)

    recommended_laptop_id = db.Column(
        db.BigInteger,
        db.ForeignKey("laptops.id", ondelete="SET NULL"),
        nullable=True
    )

    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    user = db.relationship("User", backref=db.backref("evaluation_sessions", lazy=True))
    recommended_laptop = db.relationship("Laptop", foreign_keys=[recommended_laptop_id])

    def to_dict(self, include_recommended=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "student_major": self.student_major,
            "usage_needs": self.usage_needs,
            "budget_min": float(self.budget_min) if self.budget_min is not None else None,
            "budget_max": float(self.budget_max) if self.budget_max is not None else None,
            "prefer_battery": self.prefer_battery,
            "prefer_lightweight": self.prefer_lightweight,
            "prefer_performance": self.prefer_performance,
            "prefer_durability": self.prefer_durability,
            "prefer_upgradeability": self.prefer_upgradeability,
            "ai_enabled": self.ai_enabled,
            "cr_value": float(self.cr_value) if self.cr_value is not None else None,
            "ci_value": float(self.ci_value) if self.ci_value is not None else None,
            "is_consistent": self.is_consistent,
            "recommended_laptop_id": self.recommended_laptop_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_recommended:
            data["recommended_laptop"] = (
                self.recommended_laptop.to_dict(include_brand=True)
                if self.recommended_laptop else None
            )

        return data