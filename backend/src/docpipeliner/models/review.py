"""Review task data models for human-in-the-loop workflow."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ReviewTaskStatus(str, Enum):
    """Status of a review task."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class ReviewTaskPriority(str, Enum):
    """Priority level for review tasks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class FieldCorrectionCreate(BaseModel):
    """Schema for creating a field correction."""

    field_name: str
    original_value: str
    corrected_value: str
    correction_reason: Optional[str] = None


class FieldCorrection(FieldCorrectionCreate):
    """Field correction model with database fields."""

    id: UUID = Field(default_factory=uuid4)
    review_task_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class ReviewTaskCreate(BaseModel):
    """Schema for creating a review task."""

    document_id: UUID
    priority: ReviewTaskPriority = ReviewTaskPriority.MEDIUM
    reason: Optional[str] = Field(
        default=None, description="Reason for requiring review (e.g., 'low_confidence')"
    )
    flagged_fields: list[str] = Field(
        default_factory=list, description="List of field names that need review"
    )


class ReviewTask(ReviewTaskCreate):
    """Review task model with database fields."""

    id: UUID = Field(default_factory=uuid4)
    status: ReviewTaskStatus = ReviewTaskStatus.PENDING
    assigned_to: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    corrections: list[FieldCorrection] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ReviewTaskResponse(BaseModel):
    """API response schema for review tasks."""

    id: UUID
    document_id: UUID
    status: ReviewTaskStatus
    priority: ReviewTaskPriority
    assigned_to: Optional[str]
    reason: Optional[str]
    flagged_fields: list[str]
    corrections_count: int = 0
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReviewSubmission(BaseModel):
    """Schema for submitting a review with corrections."""

    corrections: list[FieldCorrectionCreate] = Field(default_factory=list)
    notes: Optional[str] = None
    approve: bool = Field(..., description="Whether to approve the extraction")
