from app.extensions import db


class AHPCriterion(db.Model):
    __tablename__ = "ahp_criteria"

    id = db.Column(db.BigInteger, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
        }