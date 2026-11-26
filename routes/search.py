

































"""
Search & Session State Routes with Heavy DSA Integration.

DSA Integrations:
- Stack: Multi-stage filter undo system (push filter on search, pop on undo)
- LinkedList: Sequential search query history
- CircularQueue: Fixed-capacity (10) recently viewed models buffer
- DoublyLinkedList: Browser-style back/forward model navigation cursor
- HashTable: Instant cached search lookup
- Stored Procedure: sp_search_models
"""
from fastapi import APIRouter, Query, Header, HTTPException
from typing import Optional, Dict, Any
from db import call_procedure, execute_query
from services.dsa_manager import dsa_manager

router = APIRouter(prefix="/api/search", tags=["Search & Filters"])


@router.get("/advanced")
def advanced_search(
    q: Optional[str] = Query(None, description="Keywords or model name"),
    free_only: bool = Query(False, description="Only models with free pricing"),
    min_context: Optional[int] = Query(None, description="Minimum context length in tokens"),
    max_price: Optional[float] = Query(None, description="Maximum price per 1M tokens"),
    capability: Optional[str] = Query(None, description="Required capability"),
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
):
    """
    Advanced multi-parameter search utilizing:
    - Stored Procedure: sp_search_models
    - DSA Stack: Push filter state for undo capability
    - DSA LinkedList: Append search query to user history
    - DSA HashTable: Cache search result sets
    """
    filter_state = {
        "q": q,
        "free_only": free_only,
        "min_context": min_context,
        "max_price": max_price,
        "capability": capability,
    }

    if session_id:
        dsa_manager.push_filter(session_id, filter_state)
        dsa_manager.add_search(session_id, q or "(advanced filter browse)")

    # Check cache
    cache_key = f"adv_search:{q}:{free_only}:{min_context}:{max_price}:{capability}"
    cached = dsa_manager.cache_get(cache_key)
    if cached:
        return {
            "source": "cache (HashTable O(1))",
            "filters": filter_state,
            "count": len(cached),
            "results": cached,
            "dsa_features_invoked": ["HashTable (cache hit)", "Stack (filter pushed)", "LinkedList (search logged)"]
        }

    # Execute Stored Procedure
    results = call_procedure("sp_search_models", (
        q or "",
        free_only,
        min_context,
        max_price,
        capability
    ))
    models = results[0] if results else []

    # Cache for 2 minutes
    dsa_manager.cache_put(cache_key, models, ttl=120.0)

    # Also log to search_logs table
    if session_id:
        try:
            execute_query("""
                INSERT INTO search_logs (session_id, query_text, results_count)
                VALUES (%s, %s, %s)
            """, (session_id, q or "advanced_filter", len(models)), fetch_all=False)
        except Exception:
            pass

    return {
        "source": "Stored Procedure sp_search_models",
        "filters": filter_state,
        "count": len(models),
        "results": models,
        "dsa_features_invoked": [
            "Stack — filter state pushed onto session stack",
            "LinkedList — query appended to search history",
            "HashTable — query result cached with TTL",
            "Stored Procedure — sp_search_models executed on DB"
        ]
    }


@router.post("/filters/undo")
def undo_filter(session_id: str = Header(..., alias="X-Session-ID")):
    """
    Revert the last applied search filter.
    DSA: Stack — O(1) pop operation.
    """
    undone = dsa_manager.undo_filter(session_id)
    current = dsa_manager.get_current_filters(session_id)
    history = dsa_manager.get_filter_history(session_id)

    return {
        "undone_filter": undone,
        "active_filter": current,
        "remaining_stack_depth": len(history),
        "dsa_used": "Stack (LIFO) — O(1) pop to revert last state",
    }


@router.get("/filters/history")
def filter_history(session_id: str = Header(..., alias="X-Session-ID")):
    """
    Inspect all filter states on the Stack from top (most recent) to bottom.
    DSA: Stack traversal.
    """
    history = dsa_manager.get_filter_history(session_id)
    return {
        "stack_depth": len(history),
        "filters_top_to_bottom": history,
        "dsa_used": "Stack — top-to-bottom array snapshot",
    }


@router.get("/history")
def search_history(session_id: str = Header(..., alias="X-Session-ID")):
    """
    Retrieve user search query sequence.
    DSA: Singly Linked List — chronological sequence of searches.
    """
    searches = dsa_manager.get_searches(session_id)
    return {
        "total_searches": len(searches),
        "searches": searches,
        "dsa_used": "Singly Linked List — node-to-node traversal",
    }


@router.get("/recently-viewed")
def recently_viewed(session_id: str = Header(..., alias="X-Session-ID")):
    """
    Get the ring buffer of up to 10 recently viewed models.
    DSA: Circular Queue (Ring Buffer) — automatic rollover.
    """
    items = dsa_manager.get_recently_viewed(session_id)
    return {
        "count": len(items),
        "capacity": 10,
        "recently_viewed_models": items,
        "dsa_used": "Circular Queue — fixed ring buffer maintaining last 10 models",
    }


@router.get("/browse/current")
def browse_current(session_id: str = Header(..., alias="X-Session-ID")):
    """Inspect current model in browsing history. DSA: Doubly Linked List cursor."""
    curr = dsa_manager.browse_current(session_id)
    return {
        "current_model": curr,
        "dsa_used": "Doubly Linked List — current cursor node",
    }


@router.post("/browse/forward")
def browse_forward(session_id: str = Header(..., alias="X-Session-ID")):
    """
    Navigate forward in viewed models history.
    DSA: Doubly Linked List — cursor = cursor.next, O(1).
    """
    model = dsa_manager.browse_forward(session_id)
    return {
        "navigated_to": model,
        "has_forward": model is not None,
        "dsa_used": "Doubly Linked List — cursor.next O(1)",
    }


@router.post("/browse/backward")
def browse_backward(session_id: str = Header(..., alias="X-Session-ID")):
    """
    Navigate backward in viewed models history.
    DSA: Doubly Linked List — cursor = cursor.prev, O(1).
    """
    model = dsa_manager.browse_backward(session_id)
    return {
        "navigated_to": model,
        "has_backward": model is not None,
        "dsa_used": "Doubly Linked List — cursor.prev O(1)",
    }


@router.delete("/session")
def clear_session(session_id: str = Header(..., alias="X-Session-ID")):
    """Purge all session-bound data structures."""
    dsa_manager.cleanup_session(session_id)
    return {"message": f"All data structures cleared for session {session_id}"}
