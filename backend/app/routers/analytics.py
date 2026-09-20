from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models import Issue, IssueCategory, IssueStatus, IssuePriority, User
from backend.app.schemas import (
    AnalyticsSummaryResponse,
    CategoryCountItem,
    BlockCountItem,
    StatusCountItem,
    TrendPointItem,
    HotspotItem,
    HeatmapResponse,
    ResolutionTimeResponse,
)
from backend.app.deps import require_role

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Returns high-level statistics for Admin Dashboard metric cards:
    Total, Open, Assigned, In Progress, Resolved, and Critical counts.
    """
    total = db.query(func.count(Issue.issue_id)).scalar() or 0
    open_count = db.query(func.count(Issue.issue_id)).filter(Issue.status == IssueStatus.OPEN).scalar() or 0
    assigned_count = db.query(func.count(Issue.issue_id)).filter(Issue.status == IssueStatus.ASSIGNED).scalar() or 0
    in_prog_count = db.query(func.count(Issue.issue_id)).filter(Issue.status == IssueStatus.IN_PROGRESS).scalar() or 0
    resolved_count = db.query(func.count(Issue.issue_id)).filter(Issue.status == IssueStatus.RESOLVED).scalar() or 0
    critical_count = db.query(func.count(Issue.issue_id)).filter(Issue.priority == IssuePriority.CRITICAL).scalar() or 0

    return AnalyticsSummaryResponse(
        total=total,
        open=open_count,
        assigned=assigned_count,
        in_progress=in_prog_count,
        resolved=resolved_count,
        critical=critical_count,
    )


@router.get("/by-category", response_model=List[CategoryCountItem])
def get_issues_by_category(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Returns count of issues grouped by category, sorted descending.
    """
    rows = (
        db.query(Issue.category, func.count(Issue.issue_id))
        .group_by(Issue.category)
        .order_by(func.count(Issue.issue_id).desc())
        .all()
    )
    return [
        CategoryCountItem(
            category=r[0].value if hasattr(r[0], "value") else str(r[0]),
            count=r[1],
        )
        for r in rows
    ]


@router.get("/by-block", response_model=List[BlockCountItem])
def get_issues_by_block(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Returns count of issues grouped by campus block, sorted descending.
    """
    rows = (
        db.query(Issue.block, func.count(Issue.issue_id))
        .group_by(Issue.block)
        .order_by(func.count(Issue.issue_id).desc())
        .all()
    )
    return [
        BlockCountItem(
            block=str(r[0]),
            count=r[1],
        )
        for r in rows
    ]


@router.get("/by-status", response_model=List[StatusCountItem])
def get_issues_by_status(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Returns count of issues grouped by lifecycle status.
    """
    rows = (
        db.query(Issue.status, func.count(Issue.issue_id))
        .group_by(Issue.status)
        .all()
    )
    # Ensure ordered representation: Open, Assigned, In Progress, Resolved
    order_map = {"Open": 1, "Assigned": 2, "In Progress": 3, "Resolved": 4}
    items = [
        StatusCountItem(
            status=r[0].value if hasattr(r[0], "value") else str(r[0]),
            count=r[1],
        )
        for r in rows
    ]
    items.sort(key=lambda x: order_map.get(x.status, 99))
    return items


@router.get("/trend", response_model=List[TrendPointItem])
def get_issues_trend(
    days: int = Query(30, ge=1, le=365, description="Number of past days to include in trend"),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Returns daily issue creation counts over the past N days.
    Fills days with 0 counts to produce a smooth, contiguous timeline.
    """
    start_date = (datetime.now() - timedelta(days=days - 1)).date()
    
    rows = (
        db.query(func.date(Issue.created_at), func.count(Issue.issue_id))
        .filter(func.date(Issue.created_at) >= start_date)
        .group_by(func.date(Issue.created_at))
        .all()
    )
    
    # Map DB results by string date (YYYY-MM-DD)
    db_counts = {}
    for r in rows:
        d_val = r[0]
        date_str = d_val.strftime("%Y-%m-%d") if hasattr(d_val, "strftime") else str(d_val)
        db_counts[date_str] = r[1]

    # Generate contiguous points for every day
    timeline: List[TrendPointItem] = []
    current = start_date
    end_date = datetime.now().date()
    while current <= end_date:
        d_str = current.strftime("%Y-%m-%d")
        timeline.append(TrendPointItem(date=d_str, count=db_counts.get(d_str, 0)))
        current += timedelta(days=1)

    return timeline


@router.get("/hotspots", response_model=List[HotspotItem])
def get_issue_hotspots(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Returns top recurring location hotspots (Block + Room combinations with most reports).
    """
    rows = (
        db.query(Issue.block, Issue.room, func.count(Issue.issue_id))
        .filter(Issue.room.isnot(None), Issue.room != "")
        .group_by(Issue.block, Issue.room)
        .order_by(func.count(Issue.issue_id).desc())
        .limit(limit)
        .all()
    )
    return [
        HotspotItem(
            block=str(r[0]),
            room=str(r[1]),
            count=r[2],
        )
        for r in rows
    ]


@router.get("/heatmap", response_model=HeatmapResponse)
def get_issue_heatmap(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Returns matrix of Block × Category counts for heatmap visualization.
    """
    # Distinct blocks present or standard list
    db_blocks = [r[0] for r in db.query(Issue.block).distinct().order_by(Issue.block).all() if r[0]]
    blocks = db_blocks if db_blocks else ["Block A", "Block B", "Block C", "Block D"]
    
    # All canonical categories
    categories = [c.value for c in IssueCategory]

    # Query counts for combinations
    rows = (
        db.query(Issue.block, Issue.category, func.count(Issue.issue_id))
        .group_by(Issue.block, Issue.category)
        .all()
    )

    # Initialize empty grid
    matrix = {b: {c: 0 for c in categories} for b in blocks}
    max_count = 0

    for b, c, cnt in rows:
        cat_str = c.value if hasattr(c, "value") else str(c)
        if b in matrix and cat_str in matrix[b]:
            matrix[b][cat_str] = cnt
            if cnt > max_count:
                max_count = cnt

    return HeatmapResponse(
        blocks=blocks,
        categories=categories,
        matrix=matrix,
        max_count=max_count,
    )


@router.get("/resolution-time", response_model=ResolutionTimeResponse)
def get_resolution_time(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Calculates average, fastest, and slowest resolution turnaround in hours
    for all resolved issues with non-null resolved_at timestamps.
    """
    resolved_issues = (
        db.query(Issue)
        .filter(Issue.status == IssueStatus.RESOLVED, Issue.resolved_at.isnot(None))
        .all()
    )

    if not resolved_issues:
        return ResolutionTimeResponse(
            average_hours=0.0,
            resolved_count=0,
            fastest_hours=None,
            slowest_hours=None,
        )

    hours_list = [
        max(0.1, round((iss.resolved_at - iss.created_at).total_seconds() / 3600.0, 1))
        for iss in resolved_issues
        if iss.resolved_at and iss.created_at
    ]

    if not hours_list:
        return ResolutionTimeResponse(
            average_hours=0.0,
            resolved_count=0,
            fastest_hours=None,
            slowest_hours=None,
        )

    avg_hrs = round(sum(hours_list) / len(hours_list), 1)
    fastest = min(hours_list)
    slowest = max(hours_list)

    return ResolutionTimeResponse(
        average_hours=avg_hrs,
        resolved_count=len(hours_list),
        fastest_hours=fastest,
        slowest_hours=slowest,
    )
