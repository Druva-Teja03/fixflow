from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models import (
    User,
    UserRole,
    Issue,
    IssueCategory,
    IssuePriority,
    IssueStatus,
    StatusHistory,
    Assignment,
    Comment,
    IssueSupporter,
)
from backend.app.schemas import (
    IssueListItem,
    IssueDetailResponse,
    StatusHistoryResponse,
    AssignmentResponse,
    CommentCreate,
    CommentResponse,
    MessageResponse,
    StatusUpdateRequest,
    CheckDuplicatesRequest,
    CheckDuplicatesResponse,
    DuplicateCandidateItem,
    SupportIssueResponse,
)
from backend.app.deps import get_current_user, require_role
from backend.app.services.storage import save_uploaded_file
from backend.app.services.notifications import notify_status_change
from backend.app.services.duplicates import find_duplicate_candidates

router = APIRouter(prefix="/issues", tags=["Issues"])


@router.post("", response_model=IssueListItem, status_code=status.HTTP_201_CREATED)
async def create_issue(
    title: str = Form(..., min_length=3, max_length=150),
    description: str = Form(..., min_length=5),
    category: str = Form(...),
    block: str = Form(...),
    building: Optional[str] = Form(None),
    room: Optional[str] = Form(None),
    priority: str = Form("Medium"),
    image: Optional[UploadFile] = File(None),
    ai_category: Optional[str] = Form(None),
    ai_priority: Optional[str] = Form(None),
    ai_summary: Optional[str] = Form(None),
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    Submit a new campus infrastructure issue report (Students only).
    Handles optional image upload, initializes status to Open,
    and records the first status_history audit entry.
    """
    # Validate category enum
    allowed_categories = [c.value for c in IssueCategory]
    if category not in allowed_categories:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid category '{category}'. Allowed: {allowed_categories}",
        )

    # Validate priority enum
    allowed_priorities = [p.value for p in IssuePriority]
    if priority not in allowed_priorities:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid priority '{priority}'. Allowed: {allowed_priorities}",
        )

    # Save uploaded image if provided
    image_url = await save_uploaded_file(image)

    # Create new Issue instance
    new_issue = Issue(
        user_id=current_user.user_id,
        title=title.strip(),
        description=description.strip(),
        ai_summary=ai_summary.strip() if ai_summary else None,
        category=category,
        block=block.strip(),
        building=building.strip() if building else None,
        room=room.strip() if room else None,
        priority=priority,
        status=IssueStatus.OPEN,
        image_url=image_url,
        ai_category=ai_category.strip() if ai_category else None,
        ai_priority=ai_priority.strip() if ai_priority else None,
        support_count=1,
    )
    db.add(new_issue)
    db.flush()  # Allocates issue_id

    # Record the initial status_history row
    initial_history = StatusHistory(
        issue_id=new_issue.issue_id,
        old_status=None,
        new_status="Open",
        changed_by=current_user.user_id,
    )
    db.add(initial_history)
    db.commit()
    db.refresh(new_issue)

    return new_issue


@router.post("/check-duplicates", response_model=CheckDuplicatesResponse)
def check_duplicates_endpoint(
    payload: CheckDuplicatesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Detect potential duplicate issues in the same block/room submitted in the last 30 days.
    Uses hybrid Jaccard token overlap + SequenceMatcher string distance.
    """
    candidates = find_duplicate_candidates(
        db=db,
        category=payload.category,
        block=payload.block,
        description=payload.description,
        room=payload.room,
        threshold=0.55,
        limit=3,
    )

    items = [
        DuplicateCandidateItem(
            issue_id=c["issue_id"],
            title=c["title"],
            description=c["description"],
            category=c["category"],
            block=c["block"],
            building=c.get("building"),
            room=c.get("room"),
            status=c["status"],
            support_count=c["support_count"],
            score=c["score"],
        )
        for c in candidates
    ]

    return CheckDuplicatesResponse(
        has_duplicates=len(items) > 0,
        duplicates=items,
    )


@router.get("/mine", response_model=List[IssueListItem])
def get_my_issues(
    status: Optional[str] = Query(None, description="Optional status filter"),
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    Fetch all issues reported by the authenticated student,
    ordered newest first, with optional status filter and assigned staff info.
    """
    query = db.query(Issue).filter(Issue.user_id == current_user.user_id)

    if status:
        query = query.filter(Issue.status == status)

    issues = query.order_by(desc(Issue.created_at)).all()
    results: List[IssueListItem] = []
    for iss in issues:
        staff_name = None
        staff_team = None
        if iss.assignments:
            latest = iss.assignments[-1]
            if latest.staff:
                staff_name = latest.staff.name
                staff_team = latest.staff.team

        cat_val = iss.category.value if hasattr(iss.category, "value") else str(iss.category)
        pri_val = iss.priority.value if hasattr(iss.priority, "value") else str(iss.priority)
        sta_val = iss.status.value if hasattr(iss.status, "value") else str(iss.status)

        results.append(
            IssueListItem(
                issue_id=iss.issue_id,
                user_id=iss.user_id,
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
                assigned_staff_name=staff_name,
                assigned_staff_team=staff_team,
                created_at=iss.created_at,
                updated_at=iss.updated_at,
                resolved_at=iss.resolved_at,
            )
        )
    return results


@router.get("/{issue_id}", response_model=IssueDetailResponse)
def get_issue_detail(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve full details for an issue including timeline, assignment, and comments.
    Students can ONLY view their own reported issues (returns 403 otherwise).
    Admin and Staff can view any issue.
    """
    issue = db.query(Issue).filter(Issue.issue_id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue #{issue_id} not found.",
        )

    # Access control: students may only view their own issues
    user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role == "student" and issue.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot view issues reported by another student.",
        )

    # Build status history timeline
    timeline: List[StatusHistoryResponse] = []
    for h in issue.status_history:
        changed_by_user = db.query(User).filter(User.user_id == h.changed_by).first()
        timeline.append(
            StatusHistoryResponse(
                history_id=h.history_id,
                old_status=h.old_status,
                new_status=h.new_status,
                changed_by=h.changed_by,
                changed_by_name=changed_by_user.name if changed_by_user else "System",
                changed_at=h.changed_at,
            )
        )

    # Build assignment info
    assignment_resp: Optional[AssignmentResponse] = None
    if issue.assignments:
        latest_assignment = issue.assignments[-1]
        staff_user = db.query(User).filter(User.user_id == latest_assignment.staff_id).first()
        assigner_user = db.query(User).filter(User.user_id == latest_assignment.assigned_by).first()
        if staff_user:
            assignment_resp = AssignmentResponse(
                assignment_id=latest_assignment.assignment_id,
                staff_id=staff_user.user_id,
                staff_name=staff_user.name,
                staff_team=staff_user.team,
                assigned_by=latest_assignment.assigned_by,
                assigned_by_name=assigner_user.name if assigner_user else "Admin",
                assigned_at=latest_assignment.assigned_at,
            )

    # Build comments
    comments_resp: List[CommentResponse] = []
    for c in issue.comments:
        author = db.query(User).filter(User.user_id == c.user_id).first()
        author_role = author.role.value if (author and hasattr(author.role, "value")) else "user"
        comments_resp.append(
            CommentResponse(
                comment_id=c.comment_id,
                issue_id=c.issue_id,
                user_id=c.user_id,
                user_name=author.name if author else "User",
                user_role=author_role,
                comment=c.comment,
                created_at=c.created_at,
            )
        )

    reporter = db.query(User).filter(User.user_id == issue.user_id).first()

    return IssueDetailResponse(
        issue_id=issue.issue_id,
        user_id=issue.user_id,
        reporter_name=reporter.name if reporter else "Student",
        reporter_email=reporter.email if reporter else "",
        title=issue.title,
        description=issue.description,
        ai_summary=issue.ai_summary,
        category=issue.category.value if hasattr(issue.category, "value") else str(issue.category),
        block=issue.block,
        building=issue.building,
        room=issue.room,
        priority=issue.priority.value if hasattr(issue.priority, "value") else str(issue.priority),
        status=issue.status.value if hasattr(issue.status, "value") else str(issue.status),
        image_url=issue.image_url,
        ai_category=issue.ai_category,
        ai_priority=issue.ai_priority,
        support_count=issue.support_count,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        resolved_at=issue.resolved_at,
        status_history=timeline,
        assignment=assignment_resp,
        comments=comments_resp,
    )


@router.post("/{issue_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    issue_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a comment to an issue.
    Allowed for the issue reporter (student), assigned staff, and admins.
    """
    issue = db.query(Issue).filter(Issue.issue_id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue #{issue_id} not found.",
        )

    user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role == "student" and issue.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to comment on another student's issue.",
        )

    new_comment = Comment(
        issue_id=issue_id,
        user_id=current_user.user_id,
        comment=payload.comment.strip(),
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return CommentResponse(
        comment_id=new_comment.comment_id,
        issue_id=new_comment.issue_id,
        user_id=new_comment.user_id,
        user_name=current_user.name,
        user_role=user_role,
        comment=new_comment.comment,
        created_at=new_comment.created_at,
    )


@router.get("/{issue_id}/comments", response_model=List[CommentResponse])
def get_comments(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch all comments for an issue.
    """
    issue = db.query(Issue).filter(Issue.issue_id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue #{issue_id} not found.",
        )

    user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role == "student" and issue.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot view comments on another student's issue.",
        )

    comments = (
        db.query(Comment)
        .filter(Comment.issue_id == issue_id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    results = []
    for c in comments:
        author = db.query(User).filter(User.user_id == c.user_id).first()
        author_role = author.role.value if (author and hasattr(author.role, "value")) else "user"
        results.append(
            CommentResponse(
                comment_id=c.comment_id,
                issue_id=c.issue_id,
                user_id=c.user_id,
                user_name=author.name if author else "User",
                user_role=author_role,
                comment=c.comment,
                created_at=c.created_at,
            )
        )

    return results


@router.patch("/{issue_id}/status", response_model=IssueDetailResponse)
def update_issue_status(
    issue_id: int,
    payload: StatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the lifecycle status of an issue (Section 5 strict rules).
    Allowed for:
    - Admin (can advance one step, jump directly to Resolved, or reopen Resolved -> Open).
    - Assigned Staff member (can advance Assigned -> In Progress -> Resolved).
    Rejects invalid transitions and unauthorized roles with appropriate HTTP codes.
    """
    issue = db.query(Issue).filter(Issue.issue_id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue #{issue_id} not found.",
        )

    user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)

    # 1. Role Authorization Check
    if user_role == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Students are not authorized to change issue status.",
        )

    if user_role == "staff":
        # Check if staff is currently assigned to this issue
        latest_assignment = issue.assignments[-1] if issue.assignments else None
        if not latest_assignment or latest_assignment.staff_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Only the assigned staff member or an administrator can update this issue's status.",
            )
    elif user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Not authorized to update issue status.",
        )

    # 2. Status Validation
    allowed_statuses = [s.value for s in IssueStatus]
    if payload.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Allowed statuses: {allowed_statuses}",
        )

    curr_status = issue.status.value if hasattr(issue.status, "value") else str(issue.status)
    new_status = payload.status

    if curr_status == new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Issue is already in '{curr_status}' status.",
        )

    # 3. Transition Rules Matrix (Section 5: Open -> Assigned -> In Progress -> Resolved)
    if curr_status == "Resolved":
        if new_status == "Open":
            if user_role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Only administrators can reopen resolved issues.",
                )
            valid_transitions = ["Open"]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from 'Resolved' to '{new_status}'. A resolved issue may only be reopened to 'Open' by an administrator.",
            )
    elif curr_status == "Open":
        valid_transitions = ["Assigned", "Resolved"] if user_role == "admin" else []
    elif curr_status == "Assigned":
        valid_transitions = ["In Progress", "Resolved"]
    elif curr_status == "In Progress":
        valid_transitions = ["Resolved"]
    else:
        valid_transitions = []

    if new_status not in valid_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from '{curr_status}' to '{new_status}'. Allowed: {valid_transitions or 'None'}",
        )

    # 4. Apply status update
    old_status = curr_status
    issue.status = new_status

    if new_status == "Resolved":
        issue.resolved_at = datetime.now()
    elif old_status == "Resolved" and new_status == "Open":
        issue.resolved_at = None

    # 5. Record status history
    history = StatusHistory(
        issue_id=issue.issue_id,
        old_status=old_status,
        new_status=new_status,
        changed_by=current_user.user_id,
    )
    db.add(history)
    db.commit()
    db.refresh(issue)

    # 6. Trigger notification
    notify_status_change(issue, db=db)

    # Return full updated issue details
    return get_issue_detail(issue_id=issue.issue_id, current_user=current_user, db=db)


@router.post("/{issue_id}/support", response_model=SupportIssueResponse)
def support_issue(
    issue_id: int,
    current_user: User = Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    """
    Support an existing open issue.
    - User must be a student
    - Cannot support your own issue
    - Cannot support a resolved issue
    - Can only support once per issue
    Increments support_count and records entry in issue_supporters table.
    """
    issue = db.query(Issue).filter(Issue.issue_id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue #{issue_id} not found.",
        )

    # Cannot support own issue
    if issue.user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot support your own reported issue.",
        )

    # Cannot support resolved issue
    status_str = issue.status.value if hasattr(issue.status, "value") else str(issue.status)
    if status_str == "Resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot support an issue that has already been resolved.",
        )

    # Check if user already supported this issue
    existing = (
        db.query(IssueSupporter)
        .filter(IssueSupporter.issue_id == issue_id, IssueSupporter.user_id == current_user.user_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already supported this issue.",
        )

    # Add supporter and increment support_count
    supporter = IssueSupporter(issue_id=issue_id, user_id=current_user.user_id)
    db.add(supporter)
    issue.support_count += 1
    db.commit()
    db.refresh(issue)

    return SupportIssueResponse(
        issue_id=issue.issue_id,
        support_count=issue.support_count,
        message="Issue supported successfully.",
    )

