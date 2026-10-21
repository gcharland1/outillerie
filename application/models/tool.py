from enum import StrEnum

from sqlalchemy import func, true

from app.extensions import db


def enum_values(enum_class):
    """Store an enum's values (`needs_repair`) rather than its member names (`NEEDS_REPAIR`)"""
    return [member.value for member in enum_class]


class ToolCondition(StrEnum):
    FUNCTIONAL = "functional"
    NEEDS_REPAIR = "needs_repair"
    OUT_OF_ORDER = "out_of_order"


class Tool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text, nullable=False)
    condition = db.Column(
        db.Enum(
            ToolCondition,
            name="tool_condition",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=20,
        ),
        nullable=False,
        default=ToolCondition.FUNCTIONAL,
        server_default=ToolCondition.FUNCTIONAL.value,
    )
    # Shown to the owner only; public information goes in description.
    private_notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=true())
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    owner = db.relationship("User")
    photo = db.relationship(
        "ToolPhoto", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )


class ToolPhoto(db.Model):
    tool_id = db.Column(db.Integer, db.ForeignKey("tool.id", ondelete="CASCADE"), primary_key=True)
    content = db.Column(db.LargeBinary, nullable=False)
    content_type = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
