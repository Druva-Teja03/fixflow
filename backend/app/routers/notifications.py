from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models import User, Notification
from backend.app.schemas import NotificationItem, MessageResponse
from backend.app.deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationItem])
def get_my_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch all in-app notifications for the authenticated user, newest first.
    """
    notifs = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.user_id)
        .order_by(desc(Notification.created_at))
        .all()
    )
    return notifs


@router.post("/{notification_id}/read", response_model=NotificationItem)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a single notification as read.
    Must belong to the authenticated user.
    """
    notif = (
        db.query(Notification)
        .filter(
            Notification.notification_id == notification_id,
            Notification.user_id == current_user.user_id,
        )
        .first()
    )
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification #{notification_id} not found.",
        )

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.post("/read-all", response_model=MessageResponse)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark all unread notifications for the authenticated user as read.
    """
    db.query(Notification).filter(
        Notification.user_id == current_user.user_id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()

    return MessageResponse(detail="All notifications marked as read.")
