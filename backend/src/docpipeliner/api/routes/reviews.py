"""Review task API endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from docpipeliner.api.dependencies import ApiKey, SupabaseDB
from docpipeliner.models.review import (
    ReviewSubmission,
    ReviewTaskResponse,
    ReviewTaskStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("", response_model=list[ReviewTaskResponse])
async def list_review_tasks(
    status_filter: Optional[ReviewTaskStatus] = None,
    limit: int = 100,
    offset: int = 0,
    api_key: str = ApiKey,
    supabase_client: SupabaseDB = None,
):
    """List review tasks with optional filters.

    Args:
        status_filter: Filter by task status
        limit: Maximum number of results
        offset: Offset for pagination
        api_key: API key for authentication
        supabase_client: Supabase database client

    Returns:
        List of review tasks
    """
    try:
        tasks = await supabase_client.get_review_tasks(
            status=status_filter,
            limit=limit,
            offset=offset,
        )

        return [
            ReviewTaskResponse(
                id=task.id,
                document_id=task.document_id,
                status=task.status,
                priority=task.priority,
                assigned_to=task.assigned_to,
                reason=task.reason,
                flagged_fields=task.flagged_fields,
                corrections_count=len(task.corrections),
                created_at=task.created_at,
                updated_at=task.updated_at,
                completed_at=task.completed_at,
            )
            for task in tasks
        ]

    except Exception as e:
        logger.error(f"Failed to list review tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list review tasks: {str(e)}",
        )


@router.get("/{task_id}", response_model=ReviewTaskResponse)
async def get_review_task(
    task_id: UUID,
    api_key: str = ApiKey,
    supabase_client: SupabaseDB = None,
):
    """Get review task details.

    Args:
        task_id: Review task UUID
        api_key: API key for authentication
        supabase_client: Supabase database client

    Returns:
        Review task details
    """
    # TODO: Implement get single review task
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented yet",
    )


@router.post("/{task_id}/corrections")
async def submit_corrections(
    task_id: UUID,
    submission: ReviewSubmission,
    api_key: str = ApiKey,
    supabase_client: SupabaseDB = None,
):
    """Submit corrections for a review task.

    Args:
        task_id: Review task UUID
        submission: Correction submission data
        api_key: API key for authentication
        supabase_client: Supabase database client

    Returns:
        Updated review task
    """
    # TODO: Implement correction submission
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented yet",
    )


@router.post("/{task_id}/approve")
async def approve_extraction(
    task_id: UUID,
    api_key: str = ApiKey,
    supabase_client: SupabaseDB = None,
):
    """Approve extraction results.

    Args:
        task_id: Review task UUID
        api_key: API key for authentication
        supabase_client: Supabase database client

    Returns:
        Updated review task
    """
    # TODO: Implement approval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented yet",
    )


@router.post("/{task_id}/reject")
async def reject_extraction(
    task_id: UUID,
    api_key: str = ApiKey,
    supabase_client: SupabaseDB = None,
):
    """Reject extraction and request reprocessing.

    Args:
        task_id: Review task UUID
        api_key: API key for authentication
        supabase_client: Supabase database client

    Returns:
        Updated review task
    """
    # TODO: Implement rejection
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented yet",
    )
