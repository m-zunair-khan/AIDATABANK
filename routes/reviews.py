"""
Review & Error Report Routes.

DSA Integration:
- Queue (FIFO): Moderation queue where newly submitted reviews wait for admin approval
- Demonstrates triggers: trg_review_rating_check, trg_error_resolve_timestamp
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from db import execute_query
from services.dsa_manager import dsa_manager

router = APIRouter(prefix="/api/reviews", tags=["Reviews & Error Reports"])


@router.get("/model/{version_id}")
def get_model_reviews(version_id: int, approved_only: bool = Query(True)):
    """Fetch user reviews for a model."""
    where = "AND is_approved = 1" if approved_only else ""
    return execute_query(
        f"""SELECT review_id, version_id, reviewer_name, rating, title, review_text,
                   is_verified, is_approved, created_at
            FROM user_reviews
            WHERE version_id = %s {where}
            ORDER BY created_at DESC""",
        (version_id,)
    )


@router.post("/")
def submit_review(payload: Dict[str, Any]):
    """
    Submit a user review.
    1. Persists into user_reviews table with is_approved=0.
    2. Enqueues review metadata into in-memory FIFO moderation Queue (DSA).
    """
    required = ["version_id", "reviewer_name", "rating"]
    for r in required:
        if r not in payload:
            raise HTTPException(status_code=400, detail=f"Missing required field: {r}")

    rating = int(payload["rating"])
    if not (1 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    res = execute_query("""
        INSERT INTO user_reviews (version_id, reviewer_name, rating, title, review_text, is_approved)
        VALUES (%s, %s, %s, %s, %s, 0)
    """, (
        payload["version_id"],
        payload["reviewer_name"],
        rating,
        payload.get("title", ""),
        payload.get("review_text", "")
    ), fetch_all=False)

    review_id = res.get("last_id")

    # Enqueue into DSA Queue
    dsa_manager.submit_review_for_moderation({
        "review_id": review_id,
        "version_id": payload["version_id"],
        "reviewer_name": payload["reviewer_name"],
        "rating": rating,
        "title": payload.get("title", ""),
    })

    return {
        "message": "Review submitted and placed in FIFO moderation queue",
        "review_id": review_id,
        "queue_position": dsa_manager.pending_reviews_count(),
        "dsa_used": "Queue (FIFO) — O(1) enqueue",
    }


@router.get("/moderation/next")
def get_next_for_moderation():
    """
    Dequeue the oldest pending review from the moderation Queue.
    DSA: Queue — O(1) dequeue operation.
    """
    review = dsa_manager.get_next_review_to_moderate()
    if not review:
        return {
            "message": "Moderation queue is empty",
            "dsa_used": "Queue (FIFO) — is_empty() check",
        }
    return {
        "review_to_moderate": review,
        "remaining_in_queue": dsa_manager.pending_reviews_count(),
        "dsa_used": "Queue (FIFO) — O(1) dequeue",
    }


@router.get("/moderation/peek")
def peek_moderation_queue():
    """
    Inspect the next review at the front of the queue without removing it.
    DSA: Queue — O(1) peek operation.
    """
    item = dsa_manager.peek_next_review()
    return {
        "next_in_queue": item,
        "total_pending": dsa_manager.pending_reviews_count(),
        "dsa_used": "Queue (FIFO) — O(1) peek",
    }


@router.put("/moderation/{review_id}/approve")
def approve_review(review_id: int):
    """Approve review in the database."""
    execute_query("UPDATE user_reviews SET is_approved = 1 WHERE review_id = %s", (review_id,), fetch_all=False)
    return {"message": f"Review {review_id} approved"}


@router.put("/moderation/{review_id}/reject")
def reject_review(review_id: int):
    """Reject and delete review from the database."""
    execute_query("DELETE FROM user_reviews WHERE review_id = %s", (review_id,), fetch_all=False)
    return {"message": f"Review {review_id} rejected and removed"}


# ---- Error Reports ----

@router.get("/errors/model/{version_id}")
def get_model_errors(version_id: int, status: Optional[str] = Query(None)):
    """Fetch reported issues/hallucinations for a model."""
    where = "AND status = %s" if status else ""
    params = (version_id, status) if status else (version_id,)
    return execute_query(
        f"SELECT * FROM error_reports WHERE version_id = %s {where} ORDER BY created_at DESC",
        params
    )


@router.post("/errors")
def submit_error_report(payload: Dict[str, Any]):
    """Report an error, refusal, or hallucination for a model."""
    required = ["version_id", "error_type", "description"]
    for r in required:
        if r not in payload:
            raise HTTPException(status_code=400, detail=f"Missing required parameter: {r}")

    res = execute_query("""
        INSERT INTO error_reports (version_id, reporter_name, error_type, severity, description, steps_to_reproduce, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'open')
    """, (
        payload["version_id"],
        payload.get("reporter_name", "Anonymous"),
        payload["error_type"],
        payload.get("severity", "medium"),
        payload["description"],
        payload.get("steps_to_reproduce", "")
    ), fetch_all=False)

    return {"message": "Error report filed", "report_id": res.get("last_id")}


@router.put("/errors/{report_id}/status")
def update_error_status(report_id: int, status: str = Query(..., description="Status: open, investigating, confirmed, resolved, wont_fix")):
    """
    Update error report status.
    Trigger trg_error_resolve_timestamp automatically populates resolved_at timestamp when marked resolved.
    """
    execute_query(
        "UPDATE error_reports SET status = %s WHERE report_id = %s",
        (status, report_id), fetch_all=False
    )
    return {"message": f"Error report {report_id} updated to status '{status}'"}
