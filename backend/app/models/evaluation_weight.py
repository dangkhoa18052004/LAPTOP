from app.extensions import db


class EvaluationWeight(db.Model):
    __tablename__ = "evaluation_weights"

    id = db.Column(db.BigInteger, primary_key=True)

    evaluation_session_id = db.Column(
        db.BigInteger,
        db.ForeignKey("evaluation_sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    criterion_id = db.Column(
        db.BigInteger,
        db.ForeignKey("ahp_criteria.id", ondelete="CASCADE"),
        nullable=False
    )

    ai_suggested_weight = db.Column(db.Numeric(10, 6))
    user_final_weight = db.Column(db.Numeric(10, 6), nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "evaluation_session_id",
            "criterion_id",
            name="uq_eval_weight"
        ),
    )

    criterion = db.relationship("AHPCriterion")

    def to_dict(self):
        return {
            "id": self.id,
            "evaluation_session_id": self.evaluation_session_id,
            "criterion_id": self.criterion_id,
            "ai_suggested_weight": float(self.ai_suggested_weight) if self.ai_suggested_weight is not None else None,
            "user_final_weight": float(self.user_final_weight) if self.user_final_weight is not None else None,
            "criterion": self.criterion.to_dict() if self.criterion else None,
        }