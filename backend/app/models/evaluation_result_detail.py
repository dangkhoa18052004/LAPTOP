from app.extensions import db


class EvaluationResultDetail(db.Model):
    __tablename__ = "evaluation_result_details"

    id = db.Column(db.BigInteger, primary_key=True)

    evaluation_result_id = db.Column(
        db.BigInteger,
        db.ForeignKey("evaluation_results.id", ondelete="CASCADE"),
        nullable=False
    )

    criterion_id = db.Column(
        db.BigInteger,
        db.ForeignKey("ahp_criteria.id", ondelete="CASCADE"),
        nullable=False
    )

    criterion_weight = db.Column(db.Numeric(10, 6), nullable=False)

    laptop_value_raw = db.Column(db.Numeric(10, 6))
    laptop_value_normalized = db.Column(db.Numeric(10, 6), nullable=False)

    criterion_score = db.Column(db.Numeric(10, 6), nullable=False)

    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    criterion = db.relationship("AHPCriterion")

    def to_dict(self):
        return {
            "criterion_id": self.criterion_id,
            "criterion_name": self.criterion.name if self.criterion else None,
            "criterion_weight": float(self.criterion_weight),
            "laptop_value_normalized": float(self.laptop_value_normalized),
            "criterion_score": float(self.criterion_score)
        }