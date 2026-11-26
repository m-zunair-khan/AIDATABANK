"""
Compare & Recommendation Routes.

Demonstrates:
- Side-by-side matrix generation across multiple models
- Audit logging into comparison_logs table
- Stored Procedures: sp_compare_models, sp_recommend_model
"""
from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional, List
from db import execute_query, call_procedure

router = APIRouter(prefix="/api/compare", tags=["Compare & Recommend"])


@router.get("/")
def compare_models(
    ids: str = Query(..., description="Comma-separated version IDs to compare, e.g. 1,2,3"),
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
):
    """
    Side-by-side comparison matrix of 2 or more models across pricing, benchmarks,
    token limits, and capabilities. Logs audit history to comparison_logs.
    """
    try:
        version_ids = [int(x.strip()) for x in ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid format for IDs. Use comma-separated integers.")

    if not version_ids:
        raise HTTPException(status_code=400, detail="Please provide at least one model ID to inspect.")

    placeholders = ",".join(["%s"] * len(version_ids))
    models = execute_query(f"""
        SELECT mv.version_id, mv.version_name, mv.release_date, mv.status,
               mv.context_length, mv.max_output_tokens, mv.is_free, mv.has_free_tier,
               mv.input_modalities, mv.output_modalities,
               mv.supports_tool_use, mv.supports_reasoning,
               mf.name AS family_name, p.name AS provider_name,
               ph.input_price_per_1m_tokens, ph.output_price_per_1m_tokens,
               COALESCE((SELECT AVG(rating) FROM user_reviews WHERE version_id = mv.version_id AND is_approved = 1), 0) AS avg_rating,
               COALESCE((SELECT COUNT(*) FROM user_reviews WHERE version_id = mv.version_id AND is_approved = 1), 0) AS review_count
        FROM model_versions mv
        JOIN model_families mf ON mv.family_id = mf.family_id
        JOIN providers p ON mf.provider_id = p.provider_id
        LEFT JOIN pricing_history ph ON mv.version_id = ph.version_id
        WHERE mv.version_id IN ({placeholders})
    """, tuple(version_ids))

    # Benchmark scores
    benchmarks_map = {}
    for vid in version_ids:
        scores = execute_query("""
            SELECT b.name, bs.score, b.max_score
            FROM benchmark_scores bs
            JOIN benchmarks b ON bs.benchmark_id = b.benchmark_id
            WHERE bs.version_id = %s
        """, (vid,))
        benchmarks_map[str(vid)] = scores

    # Capabilities
    capabilities_map = {}
    for vid in version_ids:
        caps = execute_query("""
            SELECT c.name, mc.proficiency
            FROM model_capabilities mc
            JOIN capabilities c ON mc.capability_id = c.capability_id
            WHERE mc.version_id = %s
        """, (vid,))
        capabilities_map[str(vid)] = caps

    # Audit logging into comparison_logs
    if session_id and len(version_ids) >= 2:
        try:
            execute_query("""
                INSERT INTO comparison_logs (session_id, version_id_1, version_id_2, comparison_criteria)
                VALUES (%s, %s, %s, 'side_by_side_matrix')
            """, (session_id, version_ids[0], version_ids[1]), fetch_all=False)
        except Exception:
            pass

    return {
        "compared_models_count": len(models),
        "models": models,
        "benchmarks_by_model": benchmarks_map,
        "capabilities_by_model": capabilities_map,
    }


@router.get("/recommend")
def recommend_model(
    use_case: str = Query(..., description="Target use case, e.g. 'Coding', 'Math', 'Creative'"),
    max_budget: Optional[float] = Query(None, description="Max USD per 1M input tokens"),
    min_context: Optional[int] = Query(None, description="Minimum context window tokens"),
):
    """
    Recommend best suited models using Stored Procedure sp_recommend_model.
    """
    results = call_procedure("sp_recommend_model", (use_case, max_budget, min_context))
    recommendations = results[0] if results else []
    return {
        "use_case": use_case,
        "filters": {"max_budget": max_budget, "min_context": min_context},
        "count": len(recommendations),
        "recommendations": recommendations,
    }


@router.get("/sp-compare")
def compare_with_procedure(version_id_1: int, version_id_2: int):
    """Execute Stored Procedure sp_compare_models."""
    results = call_procedure("sp_compare_models", (version_id_1, version_id_2))
    return {
        "procedure": "sp_compare_models",
        "model_1_id": version_id_1,
        "model_2_id": version_id_2,
        "procedure_result_sets": results,
    }
