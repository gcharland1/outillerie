from sqlalchemy import func

from app.extensions import db


class ContactRequest(db.Model):
    """A request awaiting its recipient's answer; answering it deletes it (ADR 0013)"""

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    requester = db.relationship("User", foreign_keys=[requester_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])

    __table_args__ = (
        db.CheckConstraint("requester_id <> recipient_id", name="not_self"),
        # At most one request per pair of neighbours, whichever way it was sent.
        db.Index(
            "uq_contact_request_pair",
            func.least(requester_id, recipient_id),
            func.greatest(requester_id, recipient_id),
            unique=True,
        ),
    )


class ContactRelation(db.Model):
    """Two neighbours in contact, stored once with the smaller id first (ADR 0013)"""

    user_a_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    user_b_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (db.CheckConstraint("user_a_id < user_b_id", name="ordered_pair"),)

    @staticmethod
    def pair(first_id, second_id):
        """The primary key of the relation between two users, in either order"""
        return min(first_id, second_id), max(first_id, second_id)

    @classmethod
    def between(cls, first_id, second_id):
        """A new relation between two users, in either order"""
        user_a_id, user_b_id = cls.pair(first_id, second_id)
        return cls(user_a_id=user_a_id, user_b_id=user_b_id)
