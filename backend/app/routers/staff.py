from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case

from backend.app.database import get_db
from backend.app.models import User, Issue, Assignment, IssueStatus
from backend.app.schemas import StaffTaskListItem
from backend.app.deps import require_role

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.get("/tasks", response_model=List[StaffTaskListItem])
def get_staff_tasks(
    current_user: User = Depends(require_role("staff")),
    db: Session = Depends(get_db),
):
    """
    Fetch all tasks currently assigned to the authenticated staff member.
    Ordered with active tasks first (Assigned / In Progress), followed by completed (Resolved).
    """
    # Find latest assignment ID for each issue
    subq = (
        db.query(
            Assignment.issue_id,
            func.max(Assignment.assignment_id).label("max_aid"),
        )
        .group_by(Assignment.issue_id)
        .subquery()
    )

    # Join with Assignment where staff_id matches current user
    assigned_records = (
        db.query(Assignment)
        .join(subq, Assignment.assignment_id == subq.c.max_aid)
        .filter(Assignment.staff_id == current_user.user_id)
        .all()
    )

    task_items: List[StaffTaskListItem] = []
    for a in assigned_records:
        iss = a.issue
        if not iss:
            continue

        reporter_name = iss.reporter.name if iss.reporter else "Student"
        cat_val = iss.category.value if hasattr(iss.category, "value") else str(iss.category)
        pri_val = iss.priority.value if hasattr(iss.priority, "value") else str(iss.priority)
        sta_val = iss.status.value if hasattr(iss.status, "value") else str(iss.status)

        task_items.append(
            StaffTaskListItem(
                issue_id=iss.issue_id,
                title=iss.title,
                description=iss.description,
                category=cat_val,
                block=iss.block,
                building=iss.building,
                room=iss.room,
                priority=pri_val,
                status=sta_val,
                image_url=iss.image_url,
                reporter_name=reporter_name,
                support_count=iss.support_count,
                assigned_at=a.assigned_at,
                created_at=iss.created_at,
            )
        )

    # Sort: In Progress (1), Assigned (2), Resolved (3), then by assigned_at desc
    def task_sort_key(item: StaffTaskListItem):
        rank = 3
        if item.status == "In Progress":
            rank = 1
        elif item.status == "Assigned":
            rank = 2
        return (rank, -item.assigned_at.timestamp())

    task_items.sort(key=task_sort_key)
    return task_items
