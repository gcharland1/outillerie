from app.extensions import db
from models.loan import Loan, LoanStatus
from models.tool import Tool, ToolCondition, ToolPhoto
from models.user import User

# Declarative base under a plain name, for tools that load it by path (paracelsus).
Base = db.Model

__all__ = ["Base", "Loan", "LoanStatus", "Tool", "ToolCondition", "ToolPhoto", "User"]
