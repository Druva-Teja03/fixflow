from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# --- Auth Schemas ---

class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr


class UserRegisterRequest(UserBase):
    password: str = Field(..., min_length=8, max_length=128, description="Minimum 8 characters")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    user_id: int
    role: str
    team: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# --- Message / Standard Response ---

class MessageResponse(BaseModel):
    detail: str


# --- Meta Schemas ---

class MetaOptionsResponse(BaseModel):
    categories: List[str]
    blocks: List[str]
    priorities: List[str]
    statuses: List[str]


# --- Status History Schemas ---

class StatusHistoryResponse(BaseModel):
    history_id: int
    old_status: Optional[str] = None
    new_status: str
    changed_by: int
    changed_by_name: Optional[str] = None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Assignment Schemas ---

class AssignmentResponse(BaseModel):
    assignment_id: int
    staff_id: int
    staff_name: str
    staff_team: Optional[str] = None
    assigned_by: int
    assigned_by_name: str
    assigned_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Comment Schemas ---

class CommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    comment_id: int
    issue_id: int
    user_id: int
    user_name: str
    user_role: str
    comment: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Issue Schemas ---

class IssueListItem(BaseModel):
    issue_id: int
    user_id: int
    title: str
    description: str
    category: str
    block: str
    building: Optional[str] = None
    room: Optional[str] = None
    priority: str
    status: str
    image_url: Optional[str] = None
    support_count: int
    assigned_staff_name: Optional[str] = None
    assigned_staff_team: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class IssueDetailResponse(BaseModel):
    issue_id: int
    user_id: int
    reporter_name: str
    reporter_email: str
    title: str
    description: str
    ai_summary: Optional[str] = None
    category: str
    block: str
    building: Optional[str] = None
    room: Optional[str] = None
    priority: str
    status: str
    image_url: Optional[str] = None
    ai_category: Optional[str] = None
    ai_priority: Optional[str] = None
    support_count: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    status_history: List[StatusHistoryResponse] = []
    assignment: Optional[AssignmentResponse] = None
    comments: List[CommentResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Phase 4: Admin & Staff Schemas ---

class AdminIssueListItem(BaseModel):
    issue_id: int
    user_id: int
    reporter_name: str
    reporter_email: str
    title: str
    description: str
    category: str
    block: str
    building: Optional[str] = None
    room: Optional[str] = None
    priority: str
    status: str
    image_url: Optional[str] = None
    support_count: int
    assigned_staff_id: Optional[int] = None
    assigned_staff_name: Optional[str] = None
    assigned_staff_team: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AdminIssueListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[AdminIssueListItem]


class AdminIssueUpdateRequest(BaseModel):
    priority: Optional[str] = None
    category: Optional[str] = None


class AssignStaffRequest(BaseModel):
    staff_id: int


class StatusUpdateRequest(BaseModel):
    status: str


class AnalyticsSummaryResponse(BaseModel):
    total: int
    open: int
    assigned: int
    in_progress: int
    resolved: int
    critical: int


class CategoryCountItem(BaseModel):
    category: str
    count: int


class BlockCountItem(BaseModel):
    block: str
    count: int


class StatusCountItem(BaseModel):
    status: str
    count: int


class TrendPointItem(BaseModel):
    date: str
    count: int


class HotspotItem(BaseModel):
    block: str
    room: str
    count: int


class HeatmapResponse(BaseModel):
    blocks: List[str]
    categories: List[str]
    matrix: dict
    max_count: int


class ResolutionTimeResponse(BaseModel):
    average_hours: float
    resolved_count: int
    fastest_hours: Optional[float] = None
    slowest_hours: Optional[float] = None


class StaffTaskListItem(BaseModel):
    issue_id: int
    title: str
    description: str
    category: str
    block: str
    building: Optional[str] = None
    room: Optional[str] = None
    priority: str
    status: str
    image_url: Optional[str] = None
    reporter_name: str
    support_count: int
    assigned_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Step A: AI & Duplicate Detection Schemas ---

class AISuggestRequest(BaseModel):
    description: str
    category: Optional[str] = None
    block: Optional[str] = None
    room: Optional[str] = None


class AISuggestResponse(BaseModel):
    category: str
    priority: str
    summary: str
    confidence: float
    source: str = "rules"


class CheckDuplicatesRequest(BaseModel):
    category: str
    block: str
    description: str
    room: Optional[str] = None


class DuplicateCandidateItem(BaseModel):
    issue_id: int
    title: str
    description: str
    category: str
    block: str
    building: Optional[str] = None
    room: Optional[str] = None
    status: str
    support_count: int
    score: float


class CheckDuplicatesResponse(BaseModel):
    has_duplicates: bool
    duplicates: List[DuplicateCandidateItem]


class SupportIssueResponse(BaseModel):
    issue_id: int
    support_count: int
    message: str


# --- In-App Notification Schemas ---

class NotificationItem(BaseModel):
    notification_id: int
    user_id: int
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    unread_count: int
    notifications: List[NotificationItem]


