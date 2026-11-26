"""
Benchmark Routes — AI Evaluation suites, Arena Elo ratings, and capability tests.
Demonstrates relational joins, subqueries, and analytical views (v_model_benchmark_summary).
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from db import execute_query

router = APIRouter(prefix="/api/benchmarks", tags=["Benchmarks"])


@router.get("/")
def list_benchmarks():
    """List all registered benchmark suites and human evaluation arenas."""
    return execute_query("SELECT * FROM benchmarks ORDER BY category, name")


@router.get("/summary")
def get_benchmark_summary():
    """
    Get aggregated benchmark summary across multiple evaluation vectors
    using database view v_model_benchmark_summary.
    """
    return execute_query("SELECT * FROM v_model_benchmark_summary")


@router.get("/leaderboard")
def get_leaderboard(
    benchmark_name: Optional[str] = Query(None, description="Benchmark name (e.g. MMLU, GSM8K, Arena Text)"),
    category: Optional[str] = Query(None, description="Category: general, coding, math, reasoning, creative, instruction"),
    limit: int = Query(15, ge=1, le=100),
):
    """
    Get ranked leaderboard of models for a specific benchmark or category.
    """
    if benchmark_name:
        results = execute_query("""
            SELECT mv.version_id, mv.version_name, p.name AS provider_name,
                   bs.score, b.name AS benchmark_name, b.max_score,
                   ROUND((bs.score / NULLIF(b.max_score, 0)) * 100, 2) AS percentage_score
            FROM benchmark_scores bs
            JOIN benchmarks b ON bs.benchmark_id = b.benchmark_id
            JOIN model_versions mv ON bs.version_id = mv.version_id
            JOIN model_families mf ON mv.family_id = mf.family_id
            JOIN providers p ON mf.provider_id = p.provider_id
            WHERE b.name LIKE %s
            ORDER BY bs.score DESC
            LIMIT %s
        """, (f"%{benchmark_name}%", limit))
    else:
        where = "WHERE b.category = %s" if category else ""
        params = (category, limit) if category else (limit,)
        results = execute_query(f"""
            SELECT mv.version_id, mv.version_name, p.name AS provider_name,
                   b.name AS benchmark_name, b.category, bs.score, b.max_score
            FROM benchmark_scores bs
            JOIN benchmarks b ON bs.benchmark_id = b.benchmark_id
            JOIN model_versions mv ON bs.version_id = mv.version_id
            JOIN model_families mf ON mv.family_id = mf.family_id
            JOIN providers p ON mf.provider_id = p.provider_id
            {where}
            ORDER BY bs.score DESC
            LIMIT %s
        """, params)

    return {
        "benchmark_name": benchmark_name,
        "category": category,
        "leaderboard": results,
    }


@router.get("/model/{version_id}")
def get_model_benchmarks(version_id: int):
    """Retrieve all benchmark performance records for a specific model."""
    return execute_query("""
        SELECT b.benchmark_id, b.name, b.full_name, b.category, bs.score, b.max_score,
               bs.evaluated_date, bs.source
        FROM benchmark_scores bs
        JOIN benchmarks b ON bs.benchmark_id = b.benchmark_id
        WHERE bs.version_id = %s
        ORDER BY b.category, b.name
    """, (version_id,))


@router.post("/scores")
def add_benchmark_score(payload: Dict[str, Any]):
    """Insert or update a benchmark score evaluation."""
    required = ["version_id", "benchmark_id", "score"]
    for r in required:
        if r not in payload:
            raise HTTPException(status_code=400, detail=f"Missing required parameter: {r}")

    sql = """
        INSERT INTO benchmark_scores (version_id, benchmark_id, score, evaluated_date, source)
        VALUES (%s, %s, %s, %s, %s)
    """
    params = (
        payload["version_id"],
        payload["benchmark_id"],
        payload["score"],
        payload.get("evaluated_date"),
        payload.get("source", "Standard Evaluation Run")
    )
    res = execute_query(sql, params, fetch_all=False)
    return {"message": "Benchmark score saved successfully", "result": res}
