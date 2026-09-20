from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User, UserRole, IssueCategory, IssuePriority, IssueStatus
from backend.app.schemas import MetaOptionsResponse, UserResponse
from backend.app.deps import require_role

router = APIRouter(prefix="/meta", tags=["Metadata"])


@router.get("/options", response_model=MetaOptionsResponse)
def get_meta_options():
    """
    Returns dropdown data for frontend form selection:
    Categories, Blocks, Priorities, and Statuses.
    """
    return MetaOptionsResponse(
        categories=[c.value for c in IssueCategory],
        blocks=["Block A", "Block B", "Block C", "Block D"],
        priorities=[p.value for p in IssuePriority],
        statuses=[s.value for s in IssueStatus],
    )


@router.get("/staff", response_model=List[UserResponse])
def get_staff_members(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Returns a list of maintenance/IT staff users for assignment dropdowns (Admin only).
    """
    staff_users = db.query(User).filter(User.role == UserRole.STAFF).order_by(User.name.asc()).all()
    return staff_users
