from app.extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.BigInteger, primary_key=True)

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    order_date = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)

    status = db.Column(db.String(20), default="pending")  # pending, processing, shipped, delivered, cancelled
    shipping_address = db.Column(db.Text, nullable=False)
    shipping_phone = db.Column(db.String(20), nullable=False)

    payment_method = db.Column(db.String(50), default="cod")   # cod, banking
    payment_status = db.Column(db.String(20), default="unpaid")  # unpaid, paid

    user = db.relationship("User", backref=db.backref("orders", lazy=True))

    def to_dict(self, include_items=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "total_amount": float(self.total_amount) if self.total_amount is not None else None,
            "status": self.status,
            "shipping_address": self.shipping_address,
            "shipping_phone": self.shipping_phone,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
        }

        if include_items:
            data["items"] = [item.to_dict() for item in getattr(self, "items", [])]

        return data