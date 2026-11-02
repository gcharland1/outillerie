import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, StatementError

from app.extensions import db
from models import Loan, LoanStatus, Tool, User
from tests.factories import a_day, make_loan, make_tool, make_user


@pytest.fixture
def owner_id(mock_app, user):
    with mock_app.app_context():
        return User.query.filter_by(username=user).one().id


@pytest.fixture
def borrower_id(mock_app):
    with mock_app.app_context():
        borrower = make_user("bob", "bob@example.com")
        db.session.add(borrower)
        db.session.commit()
        return borrower.id


@pytest.fixture
def tool_id(mock_app, owner_id):
    with mock_app.app_context():
        return make_tool(owner_id).id


def test_loan_is_stored_and_lent_by_the_tool_owner(mock_app, tool_id, borrower_id, owner_id):
    with mock_app.app_context():
        loan_id = make_loan(tool_id, borrower_id, a_day(3), a_day(5)).id
        db.session.expire_all()
        loan = db.session.get(Loan, loan_id)
        assert (loan.tool_id, loan.borrower_id, loan.start_date, loan.end_date) == (
            tool_id,
            borrower_id,
            a_day(3),
            a_day(5),
        )
        assert loan.lender.id == owner_id


@pytest.mark.parametrize("missing", ["tool", "borrower"])
def test_loan_of_unknown_tool_or_borrower_is_refused(mock_app, tool_id, borrower_id, missing):
    ids = {"tool": tool_id, "borrower": borrower_id, missing: 999_999}
    with mock_app.app_context():
        with pytest.raises(IntegrityError):
            make_loan(ids["tool"], ids["borrower"], a_day(3), a_day(5))
        db.session.rollback()
        assert Loan.query.count() == 0


def test_one_day_loan_is_stored(mock_app, tool_id, borrower_id):
    with mock_app.app_context():
        make_loan(tool_id, borrower_id, a_day(3), a_day(3))
        assert Loan.query.count() == 1


def test_loan_ending_before_it_starts_is_refused(mock_app, tool_id, borrower_id):
    with mock_app.app_context(), pytest.raises(IntegrityError, match="ck_loan_end_after_start"):
        make_loan(tool_id, borrower_id, a_day(5), a_day(3))


def test_loan_status_defaults_to_requested(mock_app, tool_id, borrower_id):
    with mock_app.app_context():
        assert make_loan(tool_id, borrower_id, a_day(3), a_day(5)).status is LoanStatus.REQUESTED
        db.session.execute(
            text(
                "INSERT INTO loan (tool_id, borrower_id, start_date, end_date) "
                "VALUES (:tool, :borrower, '2026-11-10', '2026-11-12')"
            ),
            {"tool": tool_id, "borrower": borrower_id},
        )
        assert (
            db.session.execute(
                text("SELECT status FROM loan WHERE start_date = '2026-11-10'")
            ).scalar_one()
            == "requested"
        )


def test_unknown_status_is_refused_by_the_orm(mock_app, tool_id, borrower_id):
    with mock_app.app_context(), pytest.raises(StatementError):
        make_loan(tool_id, borrower_id, a_day(3), a_day(5), status="in_progress")


def test_unknown_status_is_refused_by_the_database(mock_app, tool_id, borrower_id):
    with mock_app.app_context(), pytest.raises(IntegrityError, match="ck_loan_loan_status"):
        db.session.execute(
            text(
                "INSERT INTO loan (tool_id, borrower_id, start_date, end_date, status) "
                "VALUES (:tool, :borrower, '2026-11-03', '2026-11-05', 'in_progress')"
            ),
            {"tool": tool_id, "borrower": borrower_id},
        )


def test_overlapping_committed_loans_are_refused(mock_app, tool_id, borrower_id):
    with mock_app.app_context():
        make_loan(tool_id, borrower_id, a_day(3), a_day(5), LoanStatus.ACCEPTED)
        with pytest.raises(IntegrityError, match="excl_loan_tool_dates"):
            make_loan(tool_id, borrower_id, a_day(5), a_day(7), LoanStatus.ACCEPTED)


def test_consecutive_committed_loans_are_stored(mock_app, tool_id, borrower_id):
    with mock_app.app_context():
        make_loan(tool_id, borrower_id, a_day(3), a_day(5), LoanStatus.LENT)
        make_loan(tool_id, borrower_id, a_day(6), a_day(8), LoanStatus.ACCEPTED)
        assert Loan.query.count() == 2


def test_requests_may_overlap(mock_app, tool_id, borrower_id):
    with mock_app.app_context():
        make_loan(tool_id, borrower_id, a_day(3), a_day(5), LoanStatus.ACCEPTED)
        make_loan(tool_id, borrower_id, a_day(4), a_day(6), LoanStatus.REQUESTED)
        make_loan(tool_id, borrower_id, a_day(4), a_day(6), LoanStatus.REQUESTED)
        assert Loan.query.count() == 3


def test_accepting_an_overlapping_request_is_refused(mock_app, tool_id, borrower_id):
    with mock_app.app_context():
        make_loan(tool_id, borrower_id, a_day(3), a_day(5), LoanStatus.ACCEPTED)
        request = make_loan(tool_id, borrower_id, a_day(4), a_day(6), LoanStatus.REQUESTED)
        request.status = LoanStatus.ACCEPTED
        with pytest.raises(IntegrityError, match="excl_loan_tool_dates"):
            db.session.commit()


def test_returned_loan_frees_its_dates(mock_app, tool_id, borrower_id):
    with mock_app.app_context():
        make_loan(tool_id, borrower_id, a_day(3), a_day(5), LoanStatus.RETURNED)
        make_loan(tool_id, borrower_id, a_day(3), a_day(5), LoanStatus.ACCEPTED)
        assert Loan.query.count() == 2


def test_committed_loans_of_different_tools_may_share_dates(
    mock_app, tool_id, borrower_id, owner_id
):
    with mock_app.app_context():
        other_tool_id = make_tool(owner_id, name="Scie").id
        make_loan(tool_id, borrower_id, a_day(3), a_day(5), LoanStatus.ACCEPTED)
        make_loan(other_tool_id, borrower_id, a_day(3), a_day(5), LoanStatus.ACCEPTED)
        assert Loan.query.count() == 2


def test_lent_tool_cannot_be_deleted(mock_app, tool_id, borrower_id):
    with mock_app.app_context():
        make_loan(tool_id, borrower_id, a_day(3), a_day(5), LoanStatus.RETURNED)
        db.session.expunge_all()
        db.session.delete(db.session.get(Tool, tool_id))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert db.session.get(Tool, tool_id) is not None
        assert Loan.query.count() == 1
