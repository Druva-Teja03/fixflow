import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, case, or_

from backend.app.database import get_db
from backend.app.models import (
    User,
    UserRole,
    Issue,
    IssueCategory,
    IssuePriority,
    IssueStatus,
    Assignment,
    StatusHistory,
)
from backend.app.schemas import (
    AdminIssueListItem,
    AdminIssueListResponse,
    AdminIssueUpdateRequest,
    AssignStaffRequest,
    IssueDetailResponse,
)
from backend.app.deps import require_role
from backend.app.services.notifications import notify_assignment, notify_status_change

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/issues", response_model=AdminIssueListResponse)
def list_admin_issues(
    status: Optional[str] = Query(None, description="Filter by issue status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    block: Optional[str] = Query(None, description="Filter by campus block"),
    priority: Optional[str] = Query(None, description="Filter by priority level"),
    q: Optional[str] = Query(None, description="Search query across title and description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("newest", description="Sort option: newest, priority, support_count"),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    List all campus issues with filtering, text search, sorting, and pagination (Admin only).
    Includes reporter details and assigned staff info.
    """
    query = db.query(Issue)

    # 1. Apply Filters
    if status:
        query = query.filter(Issue.status == status)
    if category:
        query = query.filter(Issue.category == category)
    if block:
        query = query.filter(Issue.block == block)
    if priority:
        query = query.filter(Issue.priority == priority)
    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Issue.title.ilike(search_term),
                Issue.description.ilike(search_term),
                Issue.room.ilike(search_term),
            )
        )

    # 2. Apply Sorting
    if sort_by == "priority":
        # Critical -> High -> Medium -> Low
        priority_rank = case(
            (Issue.priority == IssuePriority.CRITICAL, 1),
            (Issue.priority == IssuePriority.HIGH, 2),
            (Issue.priority == IssuePriority.MEDIUM, 3),
            (Issue.priority == IssuePriority.LOW, 4),
            else_=5,
        )
        query = query.order_by(priority_rank.asc(), desc(Issue.created_at))
    elif sort_by == "support_count":
        query = query.order_by(desc(Issue.support_count), desc(Issue.created_at))
    else:
        # Default: newest first
        query = query.order_by(desc(Issue.created_at))

    # 3. Calculate Pagination
    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    issues = query.offset(offset).limit(page_size).all()

    # 4. Map to Output Items
    items: List[AdminIssueListItem] = []
    for iss in issues:
        # Get reporter info
        reporter = iss.reporter

        # Get latest assigned staff info
        assigned_staff_id = None
        assigned_staff_name = None
        assigned_staff_team = None
        if iss.assignments:
            latest_assignment = iss.assignments[-1]
            if latest_assignment.staff:
                assigned_staff_id = latest_assignment.staff.user_id
                assigned_staff_name = latest_assignment.staff.name
                assigned_staff_team = latest_assignment.staff.team

        cat_val = iss.category.value if hasattr(iss.category, "value") else str(iss.category)
        pri_val = iss.priority.value if hasattr(iss.priority, "value") else str(iss.priority)
        sta_val = iss.status.value if hasattr(iss.status, "value") else str(iss.status)

        items.append(
            AdminIssueListItem(
                issue_id=iss.issue_id,
                user_id=iss.user_id,
                reporter_name=reporter.name if reporter else "Unknown Student",
                reporter_email=reporter.email if reporter else "",
                title=iss.title,
                description=iss.description,
                category=cat_val,
                block=iss.block,
                building=iss.building,
                room=iss.room,
                priority=pri_val,
                status=sta_val,
                image_url=iss.image_url,
                support_count=iss.support_count,
                assigned_staff_id=assigned_staff_id,
                assigned_staff_name=assigned_staff_name,
                assigned_staff_team=assigned_staff_team,
                created_at=iss.created_at,
                updated_at=iss.updated_at,
                resolved_at=iss.resolved_at,
            )
        )

    return AdminIssueListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


@router.patch("/issues/{issue_id}", response_model=AdminIssueListItem)
def update_issue_priority_category(
    issue_id: int,
    payload: AdminIssueUpdateRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Modify issue category and/or priority (Admin only).
    """
    issue = db.query(Issue).filter(Issue.issue_id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue #{issue_id} not found.",
        )

    if payload.priority is None and payload.category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of 'priority' or 'category' must be provided.",
        )

    if payload.priority is not None:
        valid_priorities = [p.value for p in IssuePriority]
        if payload.priority not in valid_priorities:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid priority '{payload.priority}'. Allowed: {valid_priorities}",
            )
        issue.priority = payload.priority

    if payload.category is not None:
        valid_categories = [c.value for c in IssueCategory]
        if payload.category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid category '{payload.category}'. Allowed: {valid_categories}",
            )
        issue.category = payload.category

    db.commit()
    db.refresh(issue)

    # Return updated item
    reporter = issue.reporter
    assigned_staff_id = None
    assigned_staff_name = None
    assigned_staff_team = None
    if issue.assignments:
        latest = issue.assignments[-1]
        if latest.staff:
            assigned_staff_id = latest.staff.user_id
            assigned_staff_name = latest.staff.name
            assigned_staff_team = latest.staff.team

    return AdminIssueListItem(
        issue_id=issue.issue_id,
        user_id=issue.user_id,
        reporter_name=reporter.name if reporter else "Unknown Student",
        reporter_email=reporter.email if reporter else "",
        title=issue.title,
        description=issue.description,
        category=issue.category.value if hasattr(issue.category, "value") else str(issue.category),
        block=issue.block,
        building=issue.building,
        room=issue.room,
        priority=issue.priority.value if hasattr(issue.priority, "value") else str(issue.priority),
        status=issue.status.value if hasattr(issue.status, "value") else str(issue.status),
        image_url=issue.image_url,
        support_count=issue.support_count,
        assigned_staff_id=assigned_staff_id,
        assigned_staff_name=assigned_staff_name,
        assigned_staff_team=assigned_staff_team,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        resolved_at=issue.resolved_at,
    )


@router.post("/issues/{issue_id}/assign", response_model=AdminIssueListItem)
def assign_issue_to_staff(
    issue_id: int,
    payload: AssignStaffRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Assign an issue to a maintenance staff member (Admin only).
    Creates an assignments row, updates status to 'Assigned',
    records status history, and invokes notification logger.
    """
    issue = db.query(Issue).filter(Issue.issue_id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue #{issue_id} not found.",
        )

    # Validate staff user
    staff = db.query(User).filter(User.user_id == payload.staff_id).first()
    if not staff or staff.role != UserRole.STAFF:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The specified user does not exist or does not hold the 'staff' role.",
        )

    # Create assignment record
    new_assignment = Assignment(
        issue_id=issue.issue_id,
        staff_id=staff.user_id,
        assigned_by=current_user.user_id,
    )
    db.add(new_assignment)

    # Move issue status to Assigned
    old_status = issue.status.value if hasattr(issue.status, "value") else str(issue.status)
    issue.status = IssueStatus.ASSIGNED

    # Record status history
    history = StatusHistory(
        issue_id=issue.issue_id,
        old_status=old_status,
        new_status="Assigned",
        changed_by=current_user.user_id,
    )
    db.add(history)

    db.commit()
    db.refresh(issue)

    # Trigger notifications
    notify_assignment(issue, staff, db=db)
    notify_status_change(issue, db=db)

    reporter = issue.reporter
    return AdminIssueListItem(
        issue_id=issue.issue_id,
        user_id=issue.user_id,
        reporter_name=reporter.name if reporter else "Unknown Student",
        reporter_email=reporter.email if reporter else "",
        title=issue.title,
        description=issue.description,
        category=issue.category.value if hasattr(issue.category, "value") else str(issue.category),
        block=issue.block,
        building=issue.building,
        room=issue.room,
        priority=issue.priority.value if hasattr(issue.priority, "value") else str(issue.priority),
        status=issue.status.value if hasattr(issue.status, "value") else str(issue.status),
        image_url=issue.image_url,
        support_count=issue.support_count,
        assigned_staff_id=staff.user_id,
        assigned_staff_name=staff.name,
        assigned_staff_team=staff.team,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        resolved_at=issue.resolved_at,
    )
