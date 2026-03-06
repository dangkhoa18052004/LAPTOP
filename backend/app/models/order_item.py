from app.extensions import db


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.BigInteger, primary_key=True)

    order_id = db.Column(
        db.BigInteger,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )

    laptop_id = db.Column(
        db.BigInteger,
        db.ForeignKey("laptops.id", ondelete="SET NULL"),
        nullable=True
    )

    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_purchase = db.Column(db.Numeric(15, 2), nullable=False)

    order = db.relationship("Order", backref=db.backref("items", lazy=True))
    laptop = db.relationship("Laptop")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "laptop_id": self.laptop_id,
            "quantity": self.quantity,
            "price_at_purchase": float(self.price_at_purchase) if self.price_at_purchase is not None else None,
            "laptop": self.laptop.to_dict(include_brand=True) if self.laptop else None
        }