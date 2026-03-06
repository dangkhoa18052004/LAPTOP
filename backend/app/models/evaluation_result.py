from app.extensions import db


class EvaluationResult(db.Model):
    __tablename__ = "evaluation_results"

    id = db.Column(db.BigInteger, primary_key=True)

    evaluation_session_id = db.Column(
        db.BigInteger,
        db.ForeignKey("evaluation_sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    laptop_id = db.Column(
        db.BigInteger,
        db.ForeignKey("laptops.id", ondelete="CASCADE"),
        nullable=False
    )

    total_score = db.Column(db.Numeric(10, 6), nullable=False)
    rank_position = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    laptop = db.relationship("Laptop")

    def to_dict(self):
        return {
            "id": self.id,
            "evaluation_session_id": self.evaluation_session_id,
            "laptop_id": self.laptop_id,
            "total_score": float(self.total_score),
            "rank_position": self.rank_position,
            "laptop": self.laptop.to_dict(include_brand=True) if self.laptop else None
        }