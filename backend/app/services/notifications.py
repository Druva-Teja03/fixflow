"""
FixFlow In-App Notifications Service.
Generates in-app notifications for:
- Student when their issue's status changes
- Staff member when an issue is assigned to them
- Reporter's supporters when the issue is resolved
Never raises an unhandled exception or breaks the request.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models import Issue, User, Notification, IssueSupporter

logger = logging.getLogger("fixflow.notifications")


def create_notification(user_id: int, message: str, db: Optional[Session] = None) -> Optional[Notification]:
    """
    Safely creates and commits an in-app notification for a user.
    Never raises an unhandled exception.
    """
    close_session = False
    session = db
    if session is None:
        session = SessionLocal()
        close_session = True

    try:
        notif = Notification(user_id=user_id, message=message, is_read=False)
        session.add(notif)
        session.commit()
        session.refresh(notif)
        logger.info(f"[NOTIFICATION] Sent to User #{user_id}: {message}")
        return notif
    except Exception as exc:
        logger.error(f"[NOTIFICATION ERROR] Failed to create notification for User #{user_id}: {exc}")
        if session:
            session.rollback()
        return None
    finally:
        if close_session and session:
            session.close()


def notify_status_change(issue: Issue, db: Optional[Session] = None) -> None:
    """
    Notifies the issue reporter of status update.
    If status is 'Resolved', also notifies all registered supporters.
    """
    try:
        current_status = issue.status.value if hasattr(issue.status, "value") else str(issue.status)
        reporter_msg = f"Your issue #{issue.issue_id} ('{issue.title}') status has been updated to '{current_status}'."
        create_notification(user_id=issue.user_id, message=reporter_msg, db=db)

        # If issue has been resolved, notify all supporters
        if current_status == "Resolved":
            supporters = []
            if db:
                supporters = db.query(IssueSupporter).filter(IssueSupporter.issue_id == issue.issue_id).all()
            else:
                with SessionLocal() as s:
                    supporters = s.query(IssueSupporter).filter(IssueSupporter.issue_id == issue.issue_id).all()

            for supp in supporters:
                if supp.user_id != issue.user_id:
                    supp_msg = f"Good news! Issue #{issue.issue_id} ('{issue.title}') that you supported has been resolved."
                    create_notification(user_id=supp.user_id, message=supp_msg, db=db)

    except Exception as exc:
        logger.error(f"[NOTIFICATION ERROR] Failed notify_status_change for Issue #{getattr(issue, 'issue_id', 'unknown')}: {exc}")


def notify_assignment(issue: Issue, staff: User, db: Optional[Session] = None) -> None:
    """
    Notifies technician when an issue is assigned to them.
    """
    try:
        loc = f"{issue.block}" + (f" / {issue.room}" if issue.room else "")
        msg = f"You have been assigned to Issue #{issue.issue_id}: '{issue.title}' at {loc}."
        create_notification(user_id=staff.user_id, message=msg, db=db)
    except Exception as exc:
        logger.error(f"[NOTIFICATION ERROR] Failed notify_assignment for Issue #{getattr(issue, 'issue_id', 'unknown')}: {exc}")
