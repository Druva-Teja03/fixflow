import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Enum as SQLEnum,
    ForeignKey,
    DateTime,
    Index,
    Boolean,
    LargeBinary,
)
from sqlalchemy.dialects.mysql import LONGBLOB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base


class UserRole(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"
    STAFF = "staff"


class IssueCategory(str, enum.Enum):
    EQUIPMENT = "Equipment"
    ELECTRICAL = "Electrical"
    PLUMBING = "Plumbing"
    CLEANING = "Cleaning"
    FURNITURE = "Furniture"
    INTERNET = "Internet"
    DOORS_WINDOWS = "Doors/Windows"
    OTHER = "Other"


class IssuePriority(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class IssueStatus(str, enum.Enum):
    OPEN = "Open"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        SQLEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=UserRole.STUDENT,
    )
    team = Column(String(50), nullable=True)  # Electrical, Plumbing, IT, Housekeeping, Carpentry
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    reported_issues = relationship("Issue", back_populates="reporter", foreign_keys="Issue.user_id")
    assignments = relationship("Assignment", back_populates="staff", foreign_keys="Assignment.staff_id")
    assigned_by_me = relationship("Assignment", back_populates="assigner", foreign_keys="Assignment.assigned_by")
    comments = relationship("Comment", back_populates="author")
    supported_issues = relationship("IssueSupporter", back_populates="user")
    status_updates = relationship("StatusHistory", back_populates="actor")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan", order_by="Notification.created_at.desc()")


class Issue(Base):
    __tablename__ = "issues"

    issue_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    ai_summary = Column(String(255), nullable=True)
    category = Column(
        SQLEnum(IssueCategory, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        index=True,
    )
    block = Column(String(50), nullable=False)
    building = Column(String(80), nullable=True)
    room = Column(String(80), nullable=True)
    priority = Column(
        SQLEnum(IssuePriority, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=IssuePriority.MEDIUM,
        index=True,
    )
    status = Column(
        SQLEnum(IssueStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=IssueStatus.OPEN,
        index=True,
    )
    image_url = Column(String(500), nullable=True)
    ai_category = Column(String(50), nullable=True)
    ai_priority = Column(String(20), nullable=True)
    support_count = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_location", "block", "room"),
    )

    # Relationships
    reporter = relationship("User", back_populates="reported_issues", foreign_keys=[user_id])
    assignments = relationship("Assignment", back_populates="issue", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="issue", cascade="all, delete-orphan", order_by="Comment.created_at.asc()")
    supporters = relationship("IssueSupporter", back_populates="issue", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="issue", cascade="all, delete-orphan", order_by="StatusHistory.changed_at.asc()")


class Assignment(Base):
    __tablename__ = "assignments"

    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = Column(Integer, ForeignKey("issues.issue_id", ondelete="CASCADE"), nullable=False)
    staff_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    assigned_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    issue = relationship("Issue", back_populates="assignments")
    staff = relationship("User", back_populates="assignments", foreign_keys=[staff_id])
    assigner = relationship("User", back_populates="assigned_by_me", foreign_keys=[assigned_by])


class Comment(Base):
    __tablename__ = "comments"

    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = Column(Integer, ForeignKey("issues.issue_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    issue = relationship("Issue", back_populates="comments")
    author = relationship("User", back_populates="comments")


class IssueSupporter(Base):
    __tablename__ = "issue_supporters"

    issue_id = Column(Integer, ForeignKey("issues.issue_id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    issue = relationship("Issue", back_populates="supporters")
    user = relationship("User", back_populates="supported_issues")


class StatusHistory(Base):
    __tablename__ = "status_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)
    issue_id = Column(Integer, ForeignKey("issues.issue_id", ondelete="CASCADE"), nullable=False)
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    changed_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    issue = relationship("Issue", back_populates="status_history")
    actor = relationship("User", back_populates="status_updates")


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")


class UploadedImage(Base):
    """Stores uploaded photo files as BLOBs for serverless/Vercel read-only filesystems."""
    __tablename__ = "uploaded_images"

    image_id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False, unique=True, index=True)
    content_type = Column(String(100), nullable=False, default="image/jpeg")
    image_data = Column(LargeBinary().with_variant(LONGBLOB, "mysql"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

