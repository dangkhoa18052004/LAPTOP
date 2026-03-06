from app.extensions import db


class LaptopImportLog(db.Model):
    __tablename__ = "laptop_import_logs"

    id = db.Column(db.BigInteger, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    imported_by = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    total_rows = db.Column(db.Integer, default=0)
    success_rows = db.Column(db.Integer, default=0)
    failed_rows = db.Column(db.Integer, default=0)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    user = db.relationship("User", backref=db.backref("import_logs", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "file_name": self.file_name,
            "imported_by": self.imported_by,
            "imported_by_user": self.user.to_dict() if self.user else None,
            "total_rows": self.total_rows,
            "success_rows": self.success_rows,
            "failed_rows": self.failed_rows,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }