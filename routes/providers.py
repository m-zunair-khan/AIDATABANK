"""
Provider Routes — AI Vendor and Laboratory entity management.
Demonstrates relational joins, stored procedures (sp_provider_report), and view aggregation.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from db import execute_query, call_procedure

router = APIRouter(prefix="/api/providers", tags=["Providers"])


@router.get("/")
def list_providers():
    """List all AI vendors and their global model statistics from v_provider_statistics view."""
    return execute_query("SELECT * FROM v_provider_statistics")


@router.get("/{provider_id}")
def get_provider(provider_id: int):
    """Fetch provider profile and all belonging model families."""
    provider = execute_query(
        "SELECT * FROM providers WHERE provider_id = %s",
        (provider_id,), fetch_one=True
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    families = execute_query("""
        SELECT mf.*, COUNT(mv.version_id) AS total_versions
        FROM model_families mf
        LEFT JOIN model_versions mv ON mf.family_id = mv.family_id
        WHERE mf.provider_id = %s
        GROUP BY mf.family_id
    """, (provider_id,))

    return {"provider": provider, "model_families": families}


@router.get("/{provider_id}/report")
def provider_report(provider_id: int):
    """
    Generate an in-depth enterprise report for a provider using Stored Procedure sp_provider_report.
    """
    provider = execute_query(
        "SELECT name FROM providers WHERE provider_id = %s",
        (provider_id,), fetch_one=True
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    results = call_procedure("sp_provider_report", (provider["name"],))
    return {
        "provider": provider["name"],
        "statistics_summary": results[0] if len(results) > 0 else [],
        "models_catalog": results[1] if len(results) > 1 else [],
    }


@router.post("/")
def create_provider(payload: Dict[str, Any]):
    """Register a new AI provider."""
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Provider name is required")

    res = execute_query("""
        INSERT INTO providers (name, headquarters_country, founded_year, website, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        name,
        payload.get("headquarters_country"),
        payload.get("founded_year"),
        payload.get("website"),
        payload.get("description", "")
    ), fetch_all=False)

    return {"message": "Provider created", "provider_id": res.get("last_id")}


@router.put("/{provider_id}")
def update_provider(provider_id: int, payload: Dict[str, Any]):
    """Update provider details."""
    updates, params = [], []
    for field in ["name", "headquarters_country", "founded_year", "website", "description"]:
        if field in payload:
            updates.append(f"{field} = %s")
            params.append(payload[field])

    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    params.append(provider_id)
    execute_query(
        f"UPDATE providers SET {', '.join(updates)} WHERE provider_id = %s",
        tuple(params), fetch_all=False
    )
    return {"message": "Provider updated successfully"}


@router.delete("/{provider_id}")
def delete_provider(provider_id: int):
    """Delete provider and cascade deletion to all model families and versions."""
    res = execute_query("DELETE FROM providers WHERE provider_id = %s", (provider_id,), fetch_all=False)
    return {"message": "Provider deleted", "affected_rows": res.get("affected_rows")}
