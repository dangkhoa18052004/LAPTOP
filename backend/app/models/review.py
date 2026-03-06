from app.extensions import db


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.BigInteger, primary_key=True)

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    laptop_id = db.Column(
        db.BigInteger,
        db.ForeignKey("laptops.id", ondelete="CASCADE"),
        nullable=False
    )

    rating = db.Column(db.Integer, nullable=False)  # 1 -> 5
    comment = db.Column(db.Text)

    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    user = db.relationship("User")
    laptop = db.relationship("Laptop")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "laptop_id": self.laptop_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user": {
                "id": self.user.id,
                "full_name": self.user.full_name
            } if self.user else None
        }