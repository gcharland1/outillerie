from enum import StrEnum

from sqlalchemy import func, literal_column, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint

from app.extensions import db
from models.tool import enum_values


class LoanStatus(StrEnum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    REFUSED = "refused"
    CANCELED = "canceled"
    LENT = "lent"
    RETURNED = "returned"


class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey("tool.id"), nullable=False, index=True)
    borrower_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(
        db.Enum(
            LoanStatus,
            name="loan_status",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=20,
        ),
        nullable=False,
        default=LoanStatus.REQUESTED,
        server_default=LoanStatus.REQUESTED.value,
    )
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    tool = db.relationship("Tool")
    borrower = db.relationship("User")

    __table_args__ = (
        db.CheckConstraint("end_date >= start_date", name="end_after_start"),
        # Committed loans of a tool never share a day, even under concurrent writes.
        ExcludeConstraint(
            ("tool_id", "="),
            (literal_column("daterange(start_date, end_date, '[]')"), "&&"),
            name="excl_loan_tool_dates",
            using="gist",
            where=text("status IN ('accepted', 'lent')"),
        ),
    )

    @property
    def lender(self):
        """The lender is whoever owns the tool"""
        return self.tool.owner
