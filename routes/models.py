"""
Model Routes — CRUD operations, search, sort, and filter for AI models.

DSA Integrations:
- Trie: prefix autocomplete
- Binary Search: exact O(log n) lookup
- Binary Search Range: interval filtering
- Merge Sort & Quick Sort: custom algorithmic sorting
- HashTable: query result caching with TTL
- CircularQueue: recently viewed models buffer
- DoublyLinkedList: forward/backward model browsing history
"""
from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional, Dict, Any, List
from db import execute_query
from services.dsa_manager import dsa_manager

router = APIRouter(prefix="/api/models", tags=["Models"])


@router.get("/")
def list_models(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("name", description="Sort field: name, price, rating, context_length, release_date"),
    order: str = Query("asc", description="Sort order: asc, desc"),
    algorithm: str = Query("merge", description="Algorithm: merge (stable) or quick (fast)"),
    use_cache: bool = Query(True, description="Enable HashTable result caching"),
):
    """
    List AI models with pagination and custom in-memory DSA sorting (Merge Sort or Quick Sort).
    Results are cached in a custom separate-chaining Hash Table with TTL.
    """
    cache_key = f"models:list:{page}:{limit}:{sort_by}:{order}:{algorithm}"
    if use_cache:
        cached = dsa_manager.cache_get(cache_key)
        if cached:
            return {"source": "cache (HashTable O(1) retrieval)", "data": cached}

    # Fetch models joining across 4 tables
    models = execute_query("""
        SELECT mv.version_id, mv.version_name, mv.release_date, mv.status,
               mv.context_length, mv.max_output_tokens, mv.is_free, mv.has_free_tier,
               mv.input_modalities, mv.output_modalities,
               mv.supports_tool_use, mv.supports_reasoning,
               mf.name AS family_name, p.name AS provider_name,
               ph.input_price_per_1m_tokens, ph.output_price_per_1m_tokens,
               COALESCE((SELECT AVG(rating) FROM user_reviews WHERE version_id = mv.version_id AND is_approved = 1), 0) AS avg_rating
        FROM model_versions mv
        JOIN model_families mf ON mv.family_id = mf.family_id
        JOIN providers p ON mf.provider_id = p.provider_id
        LEFT JOIN pricing_history ph ON mv.version_id = ph.version_id
    """)

    # Apply pure-python sorting algorithm
    sorted_models = dsa_manager.sort_models(models, sort_by=sort_by, order=order, algorithm=algorithm)

    # Apply pagination
    offset = (page - 1) * limit
    paged = sorted_models[offset : offset + limit]

    result = {
        "total_models": len(sorted_models),
        "page": page,
        "limit": limit,
        "sort_by": sort_by,
        "order": order,
        "algorithm_used": "Merge Sort (Stable, O(n log n))" if algorithm == "merge" else "Quick Sort (Partitioning, O(n log n) avg)",
        "models": paged,
    }

    if use_cache:
        dsa_manager.cache_put(cache_key, result, ttl=180.0)

    return {"source": "database (joined 4 tables) + DSA sort", "data": result}


@router.get("/autocomplete")
def autocomplete(q: str = Query(..., min_length=1, description="Model name prefix")):
    """
    Autocomplete model names using a Prefix Tree (Trie).
    Complexity: O(P + K) where P is prefix length and K is matching count.
    """
    suggestions = dsa_manager.autocomplete(q)
    return {
        "prefix": q,
        "dsa_used": "Trie (Prefix Tree) — O(P + K)",
        "suggestions": suggestions,
    }


@router.get("/search")
def search_models(
    q: str = Query(..., min_length=1, description="Search term"),
    method: str = Query("fuzzy", description="Search algorithm: binary, linear, fuzzy, or sql"),
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
):
    """
    Search models using selected algorithmic approach:
    - binary: O(log n) exact search on sorted array
    - linear: O(n) sequential scan
    - fuzzy: Approximate string matching with character-overlap scoring
    - sql: Full SQL database LIKE query
    """
    if session_id:
        dsa_manager.add_search(session_id, q)

    if method == "binary":
        res = dsa_manager.search_model_binary(q)
        return {
            "method": "Binary Search — O(log n)",
            "query": q,
            "dsa_used": "Binary Search on sorted model index",
            "found": res is not None,
            "result": res,
        }
    elif method == "linear":
        res = dsa_manager.search_model_linear(q)
        return {
            "method": "Linear Search — O(n)",
            "query": q,
            "dsa_used": "Linear Sequential Scan",
            "found": res is not None,
            "result": res,
        }
    elif method == "fuzzy":
        matches = dsa_manager.search_models_fuzzy(q)
        return {
            "method": "Fuzzy Search — O(n × m)",
            "query": q,
            "dsa_used": "Fuzzy string matching with bi-gram similarity",
            "results_count": len(matches),
            "results": [{"model": item, "score": round(score, 3)} for item, score in matches[:25]],
        }
    else:
        results = execute_query(
            "SELECT * FROM v_model_full_details WHERE version_name LIKE %s OR family_name LIKE %s",
            (f"%{q}%", f"%{q}%")
        )
        return {
            "method": "Database View Query (v_model_full_details)",
            "query": q,
            "results_count": len(results),
            "results": results,
        }


@router.get("/top")
def get_top_models(
    k: int = Query(5, ge=1, le=50, description="Top K items to extract"),
    criteria: str = Query("rating", description="Ranking criteria: rating, price, context_length, release_date"),
):
    """
    Extract top-K models using a Binary Heap Priority Queue (MinHeap/MaxHeap).
    Complexity: O(n log k).
    """
    models = execute_query("""
        SELECT mv.version_id, mv.version_name, mv.context_length, mv.is_free,
               mv.release_date, mf.name AS family_name, p.name AS provider_name,
               ph.input_price_per_1m_tokens,
               COALESCE((SELECT AVG(rating) FROM user_reviews WHERE version_id = mv.version_id AND is_approved = 1), 0) AS avg_rating
        FROM model_versions mv
        JOIN model_families mf ON mv.family_id = mf.family_id
        JOIN providers p ON mf.provider_id = p.provider_id
        LEFT JOIN pricing_history ph ON mv.version_id = ph.version_id
    """)

    reverse = (criteria == "price")  # For price, cheaper (lower) is better
    top_items = dsa_manager.get_top_k_models(models, k, criteria=criteria, reverse=reverse)

    return {
        "k": k,
        "criteria": criteria,
        "dsa_used": f"{'Min-Heap' if reverse else 'Max-Heap'} Priority Queue — O(n log k)",
        "models": top_items,
    }


@router.get("/price-range")
def search_by_price_range(
    min_price: float = Query(0.0, ge=0.0),
    max_price: float = Query(100.0, ge=0.0),
):
    """
    Filter models in a price window using Binary Search Range.
    Complexity: O(log n + k).
    """
    results = dsa_manager.search_models_by_price_range(min_price, max_price)
    return {
        "min_price": min_price,
        "max_price": max_price,
        "dsa_used": "Binary Search Range on price-sorted array — O(log n + k)",
        "count": len(results),
        "models": results,
    }


@router.get("/{version_id}")
def get_model_detail(
    version_id: int,
    session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Fetch comprehensive model specifications joined across 7 tables:
    - Core model info & family & provider
    - Pricing history
    - Capabilities & proficiencies
    - Benchmark evaluations
    - Tag mappings
    - Use-case recommendations
    - User review statistics
    Updates session's CircularQueue (recently viewed) and DoublyLinkedList (browse cursor).
    """
    model = execute_query("""
        SELECT mv.*, mf.name AS family_name, mf.is_open_source, mf.github_url,
               p.name AS provider_name, p.headquarters_country, p.website AS provider_website
        FROM model_versions mv
        JOIN model_families mf ON mv.family_id = mf.family_id
        JOIN providers p ON mf.provider_id = p.provider_id
        WHERE mv.version_id = %s
    """, (version_id,), fetch_one=True)

    if not model:
        raise HTTPException(status_code=404, detail="Model version not found")

    # Pricing history
    pricing = execute_query(
        "SELECT * FROM pricing_history WHERE version_id = %s ORDER BY effective_date DESC",
        (version_id,)
    )

    # Capabilities
    capabilities = execute_query("""
        SELECT c.name, c.category, mc.proficiency, c.description
        FROM model_capabilities mc
        JOIN capabilities c ON mc.capability_id = c.capability_id
        WHERE mc.version_id = %s
    """, (version_id,))

    # Benchmark scores
    benchmarks = execute_query("""
        SELECT b.name, b.full_name, b.category, bs.score, b.max_score, bs.evaluated_date, bs.source
        FROM benchmark_scores bs
        JOIN benchmarks b ON bs.benchmark_id = b.benchmark_id
        WHERE bs.version_id = %s
        ORDER BY b.category, b.name
    """, (version_id,))

    # Tags
    tags = execute_query("""
        SELECT t.name, t.color
        FROM model_tags mt
        JOIN tags t ON mt.tag_id = t.tag_id
        WHERE mt.version_id = %s
    """, (version_id,))

    # Use cases
    use_cases = execute_query("""
        SELECT uc.name, uc.category, muc.suitability_score, muc.notes
        FROM model_use_cases muc
        JOIN use_cases uc ON muc.use_case_id = uc.use_case_id
        WHERE muc.version_id = %s
        ORDER BY muc.suitability_score DESC
    """, (version_id,))

    # Reviews summary
    rev_summary = execute_query("""
        SELECT COUNT(*) AS total_reviews, AVG(rating) AS average_rating
        FROM user_reviews
        WHERE version_id = %s AND is_approved = 1
    """, (version_id,), fetch_one=True)

    # DSA Session state tracking
    if session_id:
        view_summary = {
            "version_id": version_id,
            "version_name": model.get("version_name"),
            "provider_name": model.get("provider_name"),
        }
        dsa_manager.add_recent_view(session_id, view_summary)
        dsa_manager.add_to_browse_history(session_id, view_summary)

    return {
        "model": model,
        "pricing_history": pricing,
        "capabilities": capabilities,
        "benchmarks": benchmarks,
        "tags": tags,
        "use_cases": use_cases,
        "reviews_summary": rev_summary,
    }


@router.post("/")
def create_model_version(payload: Dict[str, Any]):
    """Insert a new model version (DBMS ACID insert)."""
    required = ["family_id", "version_name"]
    for r in required:
        if r not in payload:
            raise HTTPException(status_code=400, detail=f"Missing required field: {r}")

    sql = """
        INSERT INTO model_versions (
            family_id, version_name, external_id, release_date, status,
            context_length, max_output_tokens, input_modalities, output_modalities,
            is_free, has_free_tier, supports_tool_use, supports_reasoning, description
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        payload["family_id"],
        payload["version_name"],
        payload.get("external_id"),
        payload.get("release_date"),
        payload.get("status", "active"),
        payload.get("context_length"),
        payload.get("max_output_tokens"),
        payload.get("input_modalities", "text"),
        payload.get("output_modalities", "text"),
        1 if payload.get("is_free") else 0,
        1 if payload.get("has_free_tier") else 0,
        1 if payload.get("supports_tool_use") else 0,
        1 if payload.get("supports_reasoning") else 0,
        payload.get("description", "")
    )
    res = execute_query(sql, params, fetch_all=False)
    # Clear cache
    dsa_manager.cache_clear()
    return {"message": "Model version registered successfully", "version_id": res.get("last_id")}


@router.delete("/{version_id}")
def delete_model_version(version_id: int):
    """Delete a model version (cascades to junction tables via foreign keys)."""
    res = execute_query("DELETE FROM model_versions WHERE version_id = %s", (version_id,), fetch_all=False)
    dsa_manager.cache_clear()
    return {"message": "Model deleted", "affected_rows": res.get("affected_rows")}
