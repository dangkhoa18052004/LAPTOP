from app.extensions import db


class EvaluationPairwiseMatrix(db.Model):
    __tablename__ = "evaluation_pairwise_matrix"

    id = db.Column(db.BigInteger, primary_key=True)

    evaluation_session_id = db.Column(
        db.BigInteger,
        db.ForeignKey("evaluation_sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    criterion_1_id = db.Column(
        db.BigInteger,
        db.ForeignKey("ahp_criteria.id", ondelete="CASCADE"),
        nullable=False
    )

    criterion_2_id = db.Column(
        db.BigInteger,
        db.ForeignKey("ahp_criteria.id", ondelete="CASCADE"),
        nullable=False
    )

    comparison_value = db.Column(db.Numeric(10, 6), nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "evaluation_session_id",
            "criterion_1_id",
            "criterion_2_id",
            name="uq_eval_pairwise"
        ),
    )

    criterion_1 = db.relationship("AHPCriterion", foreign_keys=[criterion_1_id])
    criterion_2 = db.relationship("AHPCriterion", foreign_keys=[criterion_2_id])

    def to_dict(self):
        return {
            "id": self.id,
            "evaluation_session_id": self.evaluation_session_id,
            "criterion_1_id": self.criterion_1_id,
            "criterion_2_id": self.criterion_2_id,
            "comparison_value": float(self.comparison_value),
            "criterion_1": self.criterion_1.to_dict() if self.criterion_1 else None,
            "criterion_2": self.criterion_2.to_dict() if self.criterion_2 else None,
        }