"""
NEXUS AI — Data Access Layer (data.py)
======================================
Unified, cached data access interface for NEXUS AI Streamlit platform.
Exclusively encapsulates calls to BackendService (MySQL relational engine)
and dsa_manager (pure-Python data structures & algorithms).

Required API contract:
- get_models(filters, sort, currency)
- get_model(id, currency)
- get_benchmarks(ids, suite_id, currency)
- get_incidents(filters)
- get_leaderboard(metric, filters, currency)
- compare_models(ids, currency, est_input_m, est_output_m)
- convert_price(value, currency)
"""

from typing import List, Dict, Any, Tuple, Optional
import time
import numpy as np
import pandas as pd
import streamlit as st
from services import BackendService, dsa_manager
from ui.styles import CURRENCIES, format_country, format_context


# -----------------------------------------------------------------------------
# CURRENCY CONVERSION & FORMATTING
# -----------------------------------------------------------------------------

def get_currency_info(currency: str = "USD ($)") -> Dict[str, Any]:
    """Returns currency metadata (symbol, exchange rate, ISO code, display name)."""
    return CURRENCIES.get(currency, CURRENCIES["USD ($)"])


def convert_price(value: Optional[float], currency: str = "USD ($)") -> Optional[float]:
    """
    Converts a USD price value into the selected target currency as a raw numeric float.
    Never returns formatted strings.
    """
    if value is None:
        return None
    info = get_currency_info(currency)
    return round(float(value) * info["rate"], 4)


def format_price_display(value_conv: Optional[float], currency: str = "USD ($)", decimals: int = 2) -> str:
    """Formats an already-converted price into a display string for cards and summaries."""
    if value_conv is None or value_conv == 0:
        return "Free"
    info = get_currency_info(currency)
    return f"{info['symbol']}{value_conv:.{decimals}f}"


# -----------------------------------------------------------------------------
# PLATFORM KPIS & SYSTEM STATUS
# -----------------------------------------------------------------------------

def get_kpis(currency: str = "USD ($)") -> Dict[str, Any]:
    """Retrieves live platform-wide KPIs with currency-converted average price."""
    raw_kpis = BackendService.get_kpi_metrics()
    info = get_currency_info(currency)
    avg_usd = float(raw_kpis.get('avg_input_price', 1.58))
    converted_avg = avg_usd * info["rate"]
    max_ctx = int(raw_kpis.get('max_context', 2000000))

    return {
        "total_models": int(raw_kpis.get('total_models', 100)),
        "active_models": int(raw_kpis.get('active_models', 100)),
        "total_providers": int(raw_kpis.get('total_providers', 9)),
        "avg_input_price_usd": avg_usd,
        "avg_input_price_converted": converted_avg,
        "avg_input_price_str": f"{info['symbol']}{converted_avg:.2f}",
        "max_context": max_ctx,
        "max_context_str": format_context(max_ctx),
        "total_benchmarks": int(raw_kpis.get('total_benchmarks', 1000)),
        "currency_symbol": info["symbol"]
    }


def get_filter_options() -> Tuple[List[str], List[str], List[str]]:
    """Returns sorted provider names, countries, and available enterprise use cases."""
    providers, countries = BackendService.get_providers_and_countries()
    use_cases = BackendService.get_all_use_cases()
    return providers, countries, use_cases


# -----------------------------------------------------------------------------
# 1. MODELS DIRECTORY: get_models
# -----------------------------------------------------------------------------

def get_models(
    filters: Optional[Dict[str, Any]] = None,
    sort: str = "Cost: Low to High",
    currency: str = "USD ($)",
    algorithm: str = "merge"
) -> List[Dict[str, Any]]:
    """
    Retrieves, filters, and sorts foundation models.
    Returns dictionaries with raw numeric fields for dataframe column_config formatting.
    """
    filters = filters or {}
    raw_models = BackendService.get_all_models_for_catalog()
    curr_info = get_currency_info(currency)
    rate = curr_info["rate"]

    q = (filters.get("q") or "").strip().lower()
    sel_providers = filters.get("providers") or []
    sel_countries = filters.get("countries") or []
    min_ctx = int(filters.get("min_ctx") or 0)
    raw_budget = filters.get("max_budget")
    if raw_budget is not None and float(raw_budget) > 0:
        max_budget_usd = float(raw_budget) / rate if rate > 0 else 999999.0
    else:
        max_budget_usd = 999999.0

    capabilities = filters.get("capabilities") or []
    free_only = bool(filters.get("free", False) or "Free" in capabilities)
    tool_only = bool(filters.get("tools", False) or "Tool Calling" in capabilities)
    reasoning_only = bool(filters.get("reasoning", False) or "Reasoning" in capabilities)
    vision_only = bool(filters.get("vision", False) or "Vision" in capabilities)

    filtered = []
    for m in raw_models:
        v_name = (m.get("version_name") or "").lower()
        f_name = (m.get("family_name") or "").lower()
        p_name = (m.get("provider_name") or "").lower()

        # Multi-term, punctuation-resilient search
        if q:
            full_haystack = f"{v_name} {f_name} {p_name}"
            norm_haystack = full_haystack.replace("-", " ").replace(".", " ").replace("_", " ").replace("/", " ")
            norm_q = q.replace("-", " ").replace(".", " ").replace("_", " ").replace("/", " ")

            q_words = norm_q.split()
            direct_match = q in full_haystack or norm_q in norm_haystack
            token_match = bool(q_words and all(w in norm_haystack for w in q_words))

            if not (direct_match or token_match):
                continue

            # Prefix matches ranked first (priority 0), then contains (priority 1-3)
            words = norm_haystack.split()
            if v_name.startswith(q) or any(w.startswith(norm_q) for w in words):
                search_rank = 0
            elif p_name.startswith(q):
                search_rank = 1
            elif q in v_name:
                search_rank = 2
            else:
                search_rank = 3
            m["_search_rank"] = search_rank
        else:
            m["_search_rank"] = 0

        if sel_providers and m["provider_name"] not in sel_providers:
            continue

        if sel_countries and m.get("headquarters_country") not in sel_countries:
            continue

        in_price_usd = float(m.get("input_price_per_1m_tokens") or 0.0)
        is_free = bool(m.get("is_free")) or in_price_usd == 0.0

        if free_only and not is_free:
            continue

        if not free_only and in_price_usd > max_budget_usd:
            continue

        ctx_len = int(m.get("context_length") or 0)
        if min_ctx > 0 and ctx_len < min_ctx:
            continue

        if tool_only and not bool(m.get("supports_tool_use")):
            continue

        if reasoning_only and not bool(m.get("supports_reasoning")):
            continue

        if vision_only and "image" not in (m.get("input_modalities") or "").lower():
            continue

        filtered.append(m)

    # In-memory sorting via DSA (Merge Sort / Quick Sort)
    sort_map = {
        "Cost: Low to High": ("price", "asc"),
        "Cost: High to Low": ("price", "desc"),
        "Input: Low to High": ("price", "asc"),
        "Input: High to Low": ("price", "desc"),
        "Context Window": ("context_length", "desc"),
        "Context: High to Low": ("context_length", "desc"),
        "Context: Low to High": ("context_length", "asc"),
        "Model Rating": ("avg_rating", "desc"),
        "Rating: High to Low": ("avg_rating", "desc"),
        "Rating: Low to High": ("avg_rating", "asc"),
        "Output: Low to High": ("output_price", "asc"),
        "Output: High to Low": ("output_price", "desc"),
        "Release Date": ("release_date", "desc"),
        "Model Name": ("name", "asc"),
        "Model Name: A to Z": ("name", "asc"),
        "Model Name: Z to A": ("name", "desc"),
        "AI Lab: A to Z": ("lab", "asc"),
        "AI Lab: Z to A": ("lab", "desc"),
    }
    field, direction = sort_map.get(sort, ("price", "asc"))
    algo = algorithm if algorithm in ("merge", "quick") else "merge"
    sorted_models = dsa_manager.sort_models(filtered, sort_by=field, order=direction, algorithm=algo)

    # If query is active and sort is default or by name, prioritize search prefix matches
    if q and sort in ("Cost: Low to High", "Model Name"):
        sorted_models.sort(key=lambda x: x.get("_search_rank", 0))

    # Format into normalized rows with raw numeric types
    result = []
    for m in sorted_models:
        in_usd = float(m.get('input_price_per_1m_tokens') or 0.0)
        out_usd = float(m.get('output_price_per_1m_tokens') or 0.0)
        in_conv = round(in_usd * rate, 3)
        out_conv = round(out_usd * rate, 3)
        rating_val = float(m['avg_rating']) if m.get('avg_rating') is not None else None
        ctx = int(m.get("context_length") or 0)

        caps = []
        if m.get("supports_tool_use"):
            caps.append("Tools")
        if m.get("supports_reasoning"):
            caps.append("Reasoning")
        if "image" in (m.get("input_modalities") or "").lower():
            caps.append("Vision")
        caps_str = " · ".join(caps) if caps else "—"

        c_code = format_country(m.get("headquarters_country"))

        result.append({
            "version_id": m["version_id"],
            "Model": m["version_name"],
            "Lab": f"{m['provider_name']} ({c_code})",
            "Context": ctx,
            "Input / 1M": in_conv,
            "Output / 1M": out_conv,
            "Rating": rating_val,
            "Capabilities": caps_str,
            "is_free": bool(m.get("is_free") or in_usd == 0.0),
            "provider_name": m["provider_name"],
            "headquarters_country": m.get("headquarters_country"),
            "family_name": m.get("family_name", ""),
            "max_output_tokens": int(m.get("max_output_tokens") or 0),
            "input_modalities": m.get("input_modalities", "text"),
            "release_date": str(m.get("release_date", ""))[:10],
            "description": m.get("description", ""),
            "input_price_usd": in_usd,
            "output_price_usd": out_usd,
            "supports_tool_use": bool(m.get("supports_tool_use")),
            "supports_reasoning": bool(m.get("supports_reasoning")),
        })

    return result


def autocomplete_suggestions(prefix: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Retrieves fast Trie prefix autocomplete suggestions."""
    if not prefix or not prefix.strip():
        return []
    return dsa_manager.autocomplete(prefix.strip(), limit=limit)


def push_filter_state(session_id: str, state: Dict[str, Any]) -> None:
    """Pushes a filter snapshot onto the session filter Stack DSA."""
    dsa_manager.push_filter(session_id, state)


def undo_filter_state(session_id: str) -> Optional[Dict[str, Any]]:
    """Pops and returns the previous filter snapshot from the session Stack DSA."""
    return dsa_manager.undo_filter(session_id)


# -----------------------------------------------------------------------------
# 2. COMPARE MODELS: compare_models
# -----------------------------------------------------------------------------

def compare_models(
    model_ids: List[int],
    currency: str = "USD ($)",
    est_input_m: float = 10.0,
    est_output_m: float = 2.0
) -> Dict[str, Any]:
    """
    Compares 2 to 4 models side-by-side.
    Returns:
    - models_data: list of dicts for each model
    - spec_rows: list of dicts with each spec, values per model, and advantage/winner
    - monthly_costs: spend simulation for each model in active currency
    - winners: dict identifying cheapest, largest context, best rated
    - benchmark_chart_rows: normalized horizontal grouped bar chart rows
    """
    if not model_ids:
        model_ids = [1, 2]
    # Restrict to maximum 4 models per spec
    model_ids = model_ids[:4]

    curr_info = get_currency_info(currency)
    rate = curr_info["rate"]
    sym = curr_info["symbol"]

    models_data = []
    for vid in model_ids:
        m = BackendService.get_model_deep_profile(vid)
        if not m:
            continue
        in_usd = float(m.get("input_price_per_1m_tokens") or 0.0)
        out_usd = float(m.get("output_price_per_1m_tokens") or 0.0)
        in_conv = round(in_usd * rate, 3)
        out_conv = round(out_usd * rate, 3)
        ctx = int(m.get("context_length") or 0)
        max_out = int(m.get("max_output_tokens") or 0)
        rate_val = float(m.get("avg_rating") or 0.0)

        # Monthly spend simulation
        monthly_cost = (est_input_m * in_conv) + (est_output_m * out_conv)

        models_data.append({
            "version_id": vid,
            "version_name": m.get("version_name", f"Model {vid}"),
            "provider_name": m.get("provider_name", "Unknown"),
            "headquarters_country": format_country(m.get("headquarters_country")),
            "input_price_usd": in_usd,
            "output_price_usd": out_usd,
            "input_price_conv": in_conv,
            "output_price_conv": out_conv,
            "context_length": ctx,
            "max_output_tokens": max_out,
            "avg_rating": rate_val,
            "supports_tool_use": bool(m.get("supports_tool_use")),
            "supports_reasoning": bool(m.get("supports_reasoning")),
            "monthly_cost": monthly_cost
        })

    if not models_data:
        return {}

    # Identify winners
    cheapest = min(models_data, key=lambda x: x["monthly_cost"])
    largest_ctx = max(models_data, key=lambda x: x["context_length"])
    best_rated = max(models_data, key=lambda x: x["avg_rating"])

    winners = {
        "cheapest": cheapest["version_name"],
        "cheapest_cost": cheapest["monthly_cost"],
        "largest_ctx": largest_ctx["version_name"],
        "largest_ctx_val": largest_ctx["context_length"],
        "best_rated": best_rated["version_name"],
        "best_rated_val": best_rated["avg_rating"],
    }

    # Best values for highlighting
    min_in = min(m["input_price_conv"] for m in models_data)
    min_out = min(m["output_price_conv"] for m in models_data)
    max_c = max(m["context_length"] for m in models_data)
    max_o = max(m["max_output_tokens"] for m in models_data)
    max_r = max(m["avg_rating"] for m in models_data)

    # Build side-by-side spec rows
    spec_rows = []

    def make_row(spec_name, getter_fn, best_val=None, is_min=False):
        row = {"Specification": spec_name}
        vals = [getter_fn(m) for m in models_data]
        for m, v in zip(models_data, vals):
            row[m["version_name"]] = v
        # Determine advantage
        if best_val is not None:
            best_models = [m["version_name"] for m in models_data if getter_fn(m) == best_val]
            row["Best"] = ", ".join(best_models) if len(best_models) < len(models_data) else "Tie"
        else:
            row["Best"] = "—"
        return row

    spec_rows.append(make_row("Provider / Lab", lambda m: f"{m['provider_name']} ({m['headquarters_country']})"))
    spec_rows.append(make_row(f"Input Price / 1M ({sym})", lambda m: f"{sym}{m['input_price_conv']:.3f}", best_val=f"{sym}{min_in:.3f}"))
    spec_rows.append(make_row(f"Output Price / 1M ({sym})", lambda m: f"{sym}{m['output_price_conv']:.3f}", best_val=f"{sym}{min_out:.3f}"))
    spec_rows.append(make_row("Context Window", lambda m: f"{format_context(m['context_length'])} Tokens", best_val=f"{format_context(max_c)} Tokens"))
    spec_rows.append(make_row("Max Output Tokens", lambda m: f"{format_context(m['max_output_tokens'])} Tokens", best_val=f"{format_context(max_o)} Tokens"))
    spec_rows.append(make_row("Tool Calling", lambda m: "Supported" if m['supports_tool_use'] else "No"))
    spec_rows.append(make_row("Step Reasoning (CoT)", lambda m: "Supported" if m['supports_reasoning'] else "No"))
    spec_rows.append(make_row("Rating", lambda m: f"★ {m['avg_rating']:.2f}" if m['avg_rating'] > 0 else "Unrated", best_val=f"★ {max_r:.2f}"))

    # Benchmark comparisons for horizontal grouped bar chart
    all_scores = {}
    for m in models_data:
        m_benchs = BackendService.get_model_benchmarks(m["version_id"]) or []
        all_scores[m["version_name"]] = {b.get("benchmark_name") or b.get("benchmark", "Unknown"): b for b in m_benchs}

    all_benchmark_names = sorted(list({bname for sdict in all_scores.values() for bname in sdict}))

    chart_rows = []
    for bname in all_benchmark_names:
        for idx, m in enumerate(models_data):
            info = all_scores.get(m["version_name"], {}).get(bname, {})
            max_s = float(info.get("max_score") or 100.0)
            raw_s = float(info.get("score") or 0.0)
            pct = round((raw_s / max_s) * 100.0, 1) if max_s > 0 else 0.0
            disp_s = f"{raw_s:.1f} Elo" if "Elo" in bname else f"{raw_s:.1f}%"
            chart_rows.append({
                "Benchmark": bname,
                "Model": m["version_name"],
                "Score_Pct": pct,
                "Raw_Score": raw_s,
                "Display_Score": disp_s,
                "Model_Index": idx
            })

    return {
        "models_data": models_data,
        "spec_rows": spec_rows,
        "winners": winners,
        "benchmark_chart_rows": chart_rows,
        "currency_symbol": sym
    }


# -----------------------------------------------------------------------------
# 3. PERFORMANCE LEADERBOARDS: get_leaderboard & get_benchmarks
# -----------------------------------------------------------------------------

def get_benchmark_suites() -> List[Dict[str, Any]]:
    """Returns all verified benchmark suites."""
    return BackendService.get_all_benchmark_suites()


def get_benchmarks(
    model_ids: Optional[List[int]] = None,
    suite_id: Optional[int] = None,
    currency: str = "USD ($)"
) -> Any:
    """Retrieves benchmark scores for specified models or suite."""
    if suite_id is not None:
        return BackendService.get_leaderboard_for_suite(suite_id)
    if model_ids:
        res = {}
        for mid in model_ids:
            res[mid] = BackendService.get_model_benchmarks(mid)
        return res
    return BackendService.get_all_benchmark_suites()


def get_leaderboard(
    metric: str = "score",
    filters: Optional[Dict[str, Any]] = None,
    currency: str = "USD ($)"
) -> List[Dict[str, Any]]:
    """
    Returns ranked leaderboard data for:
    - metric="score": Benchmark suite evaluation scores (normalized % scaled to TOP score)
    - metric="cost": Ingestion price leaderboard (lowest first)
    - metric="context": Context capacity leaderboard (highest first)
    - metric="rating": Developer satisfaction leaderboard (highest first)
    """
    filters = filters or {}
    curr_info = get_currency_info(currency)
    rate = curr_info["rate"]

    rows = []

    if metric == "score":
        suite_id = int(filters.get("suite_id") or 1)
        lab_filter = filters.get("labs") or []
        reasoning_only = bool(filters.get("reasoning_only", False))

        board_records = BackendService.get_leaderboard_for_suite(suite_id)
        if not board_records:
            return []

        # Find top score for scaling (best = 100%)
        valid_scores = [float(r.get("score") or 0.0) for r in board_records]
        top_score = max(valid_scores) if valid_scores else 100.0
        if top_score <= 0:
            top_score = 100.0

        rank = 1
        for r in board_records:
            if lab_filter and r["provider_name"] not in lab_filter:
                continue
            if reasoning_only and not bool(r.get("supports_reasoning")):
                continue

            sc = float(r.get("score") or 0.0)
            in_p_usd = r.get("price_per_1m") if r.get("price_per_1m") is not None else r.get("input_price_per_1m_tokens")
            in_p_conv = round(float(in_p_usd) * rate, 3) if in_p_usd is not None else 0.0

            # Scale to top score (best = 100%)
            rel_score = round(min(100.0, (sc / top_score) * 100.0), 1)

            # Rank label with special medal styling identifier
            rank_label = f"#{rank}"
            if rank == 1:
                rank_style = "gold"
            elif rank in (2, 3):
                rank_style = "silver"
            else:
                rank_style = "plain"

            rows.append({
                "Rank": rank_label,
                "Rank_Style": rank_style,
                "Model": r["version_name"],
                "Lab": r["provider_name"],
                "Score": sc,
                "Relative Score": rel_score,
                "Price": in_p_conv,
                "version_id": r["version_id"]
            })
            rank += 1

    elif metric == "cost":
        cat_models = BackendService.get_all_models_for_catalog()
        sorted_models = sorted(cat_models, key=lambda x: (x.get("input_price_per_1m_tokens") or 999.0))[:25]
        for i, m in enumerate(sorted_models):
            in_usd = float(m.get("input_price_per_1m_tokens") or 0.0)
            out_usd = float(m.get("output_price_per_1m_tokens") or 0.0)
            rank_style = "gold" if i == 0 else ("silver" if i in (1, 2) else "plain")
            rows.append({
                "Rank": f"#{i+1}",
                "Rank_Style": rank_style,
                "Model": m["version_name"],
                "Lab": m["provider_name"],
                "Input / 1M": round(in_usd * rate, 3),
                "Output / 1M": round(out_usd * rate, 3),
                "Context": int(m.get("context_length") or 0),
                "version_id": m["version_id"]
            })

    elif metric == "context":
        cat_models = BackendService.get_all_models_for_catalog()
        sorted_models = sorted(cat_models, key=lambda x: (x.get("context_length") or 0), reverse=True)[:25]
        for i, m in enumerate(sorted_models):
            in_usd = float(m.get("input_price_per_1m_tokens") or 0.0)
            rank_style = "gold" if i == 0 else ("silver" if i in (1, 2) else "plain")
            rows.append({
                "Rank": f"#{i+1}",
                "Rank_Style": rank_style,
                "Model": m["version_name"],
                "Lab": m["provider_name"],
                "Context Window": int(m.get("context_length") or 0),
                "Max Output": int(m.get("max_output_tokens") or 0),
                "Input / 1M": round(in_usd * rate, 3),
                "version_id": m["version_id"]
            })

    elif metric == "rating":
        cat_models = BackendService.get_all_models_for_catalog()
        sorted_models = sorted(cat_models, key=lambda x: (x.get("avg_rating") or 0.0), reverse=True)[:25]
        for i, m in enumerate(sorted_models):
            in_usd = float(m.get("input_price_per_1m_tokens") or 0.0)
            rank_style = "gold" if i == 0 else ("silver" if i in (1, 2) else "plain")
            rows.append({
                "Rank": f"#{i+1}",
                "Rank_Style": rank_style,
                "Model": m["version_name"],
                "Lab": m["provider_name"],
                "Rating": round(float(m.get("avg_rating") or 0.0), 2),
                "Input / 1M": round(in_usd * rate, 3),
                "Context": int(m.get("context_length") or 0),
                "version_id": m["version_id"]
            })

    return rows


# -----------------------------------------------------------------------------
# 4. DEEP MODEL PROFILE: get_model
# -----------------------------------------------------------------------------

def get_model_selection_list() -> List[Dict[str, Any]]:
    """Returns dropdown options for selecting models."""
    return BackendService.get_model_selection_list()


def get_model(model_id: int, currency: str = "USD ($)") -> Optional[Dict[str, Any]]:
    """
    Fetches full specifications, capabilities, pricing history, benchmarks,
    reviews, and operational incidents for a single model.
    All prices converted into the selected currency.
    """
    profile = BackendService.get_model_deep_profile(model_id)
    if not profile:
        return None

    curr_info = get_currency_info(currency)
    rate = curr_info["rate"]

    caps = BackendService.get_model_capabilities(model_id)
    pricing_raw = BackendService.get_model_pricing_history(model_id)
    benchmarks = BackendService.get_model_benchmarks(model_id)
    use_cases = BackendService.get_model_use_cases(model_id)
    reviews = BackendService.get_model_reviews(model_id)
    incidents = BackendService.get_model_incidents(model_id)
    api_gateway = BackendService.get_model_api_gateway(model_id)

    pricing_history = []
    for r in pricing_raw:
        in_usd = r.get("input_price_per_1m_tokens")
        out_usd = r.get("output_price_per_1m_tokens")
        pricing_history.append({
            "Effective Date": str(r.get("effective_date", ""))[:10],
            "Input / 1M": round(float(in_usd) * rate, 4) if in_usd is not None else 0.0,
            "Output / 1M": round(float(out_usd) * rate, 4) if out_usd is not None else 0.0,
            "Input (USD Base)": round(float(in_usd), 4) if in_usd is not None else 0.0,
            "Output (USD Base)": round(float(out_usd), 4) if out_usd is not None else 0.0,
        })

    in_price_usd = float(profile.get("input_price_per_1m_tokens") or 0.0)
    in_price_conv = round(in_price_usd * rate, 3)

    return {
        "profile": profile,
        "input_price_converted": in_price_conv,
        "currency_symbol": curr_info["symbol"],
        "capabilities": caps,
        "pricing_history": pricing_history,
        "benchmarks": benchmarks,
        "use_cases": use_cases,
        "reviews": reviews,
        "incidents": incidents,
        "api_gateway": api_gateway
    }


def add_recent_view(session_id: str, version_id: int, version_name: str) -> None:
    """Enqueues model to Circular Queue DSA for recent browsing tracking."""
    dsa_manager.add_recent_view(session_id, {"version_id": version_id, "version_name": version_name})


def get_recent_views(session_id: str) -> List[Dict[str, Any]]:
    """Retrieves recent models from Circular Queue DSA."""
    return dsa_manager.get_recently_viewed(session_id)


# -----------------------------------------------------------------------------
# 5. SMART COST & TASK MATCHER: get_recommendations
# -----------------------------------------------------------------------------

def get_recommendations(
    use_case: str,
    budget_cap: float,
    min_context: int,
    currency: str = "USD ($)"
) -> List[Dict[str, Any]]:
    """
    Executes constraint-based matching using stored procedure sp_recommend_model.
    Converts budget cap from active currency to USD, executes query, and converts output prices.
    Identifies the best-value recommendation.
    """
    curr_info = get_currency_info(currency)
    rate = curr_info["rate"]
    budget_cap_usd = budget_cap / rate if rate > 0 else budget_cap

    raw_matches = BackendService.get_model_recommendations(use_case, budget_cap_usd, min_context)
    results = []

    for m in raw_matches:
        in_val = m.get("input_price_per_1m_tokens") or m.get("input_price") or 0.0
        out_val = m.get("output_price_per_1m_tokens") or m.get("output_price") or 0.0
        suitability = float(m.get("suitability_score") or 0.0)
        in_conv = round(float(in_val) * rate, 3)
        out_conv = round(float(out_val) * rate, 3)

        results.append({
            "version_id": m.get("version_id"),
            "Model": m.get("version_name"),
            "Provider": m.get("provider_name"),
            "Input / 1M": in_conv,
            "Output / 1M": out_conv,
            "Context": int(m.get('context_length') or 0),
            "Suitability Score": suitability,
        })

    # Sort candidates by suitability score DESC, then cost ASC
    results.sort(key=lambda x: (-x["Suitability Score"], x["Input / 1M"]))

    # Tag top recommendation as "Best Value"
    if results:
        results[0]["is_best_value"] = True

    return results


# -----------------------------------------------------------------------------
# 6. AUDIT & INCIDENTS: get_incidents & get_reviews
# -----------------------------------------------------------------------------

def get_incidents(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Fetches recent incident and error reports across all models.
    Supports filtering by severity and model.
    Note: Status is omitted per specification.
    """
    filters = filters or {}
    raw = BackendService.get_all_recent_incidents(limit=int(filters.get("limit") or 100))

    sel_severity = (filters.get("severity") or "").lower()
    sel_model = (filters.get("model") or "").lower()

    records = []
    for inc in raw:
        sev = (inc.get("severity") or "medium").lower()
        v_name = (inc.get("version_name") or "").lower()

        if sel_severity and sev != sel_severity:
            continue
        if sel_model and sel_model not in v_name:
            continue

        records.append({
            "report_id": inc.get("report_id"),
            "Severity": sev.upper(),
            "Model": inc.get("version_name", ""),
            "Failure Mode": inc.get("error_type", "hallucination").title(),
            "Description": inc.get("description", ""),
            "Time": str(inc.get("created_at", ""))[:19]
        })
    return records


def get_reviews(model_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Fetches approved community developer reviews."""
    if model_id:
        raw = BackendService.get_model_reviews(model_id)
    else:
        raw = BackendService.get_all_community_reviews()

    records = []
    for rev in raw:
        records.append({
            "review_id": rev.get("review_id"),
            "Model": rev.get("version_name", ""),
            "Rating": int(rev.get("rating", 5)),
            "Reviewer": rev.get("reviewer_name", "Anonymous"),
            "Title": rev.get("title", ""),
            "Observations": rev.get("review_text", ""),
            "Date": str(rev.get("created_at", ""))[:10]
        })
    return records


def submit_review(version_id: int, reviewer_name: str, rating: int, title: str, review_text: str) -> bool:
    """Submits a user review to the database and moderation queue."""
    success = BackendService.submit_user_review(version_id, reviewer_name, rating, title, review_text)
    if success:
        dsa_manager.submit_review_for_moderation({
            "version_id": version_id,
            "reviewer_name": reviewer_name,
            "rating": rating,
            "title": title
        })
    return success


def log_incident(version_id: int, reporter_name: str, error_type: str, severity: str, description: str) -> bool:
    """Logs an incident or failure report."""
    return BackendService.log_incident_report(version_id, reporter_name, error_type, severity, description)


# -----------------------------------------------------------------------------
# 7. ENTERPRISE ANALYTICS: get_analytics_report & get_schema_counts
# -----------------------------------------------------------------------------

REPORTS_REGISTRY = {
    "Top 20 Cost-Effective Models": {
        "desc": "Models offering the lowest API token ingestion cost per 1M tokens in active currency.",
        "query": """
            SELECT mv.version_name, p.name AS provider_name, p.headquarters_country,
                   ph.input_price_per_1m_tokens, ph.output_price_per_1m_tokens,
                   mv.context_length, mv.supports_tool_use, mv.supports_reasoning
            FROM model_versions mv
            JOIN model_families mf ON mv.family_id = mf.family_id
            JOIN providers p ON mf.provider_id = p.provider_id
            JOIN pricing_history ph ON mv.version_id = ph.version_id
            WHERE ph.input_price_per_1m_tokens IS NOT NULL
            ORDER BY ph.input_price_per_1m_tokens ASC
            LIMIT 20
        """,
        "chart_type": "bar_cost"
    },
    "Chatbot Arena Elo Champions": {
        "desc": "Frontier models ranked by crowdsourced blind human pairwise preference.",
        "query": """
            SELECT mv.version_name, p.name AS provider_name, p.headquarters_country,
                   bs.score AS elo_rating, mv.context_length, ph.input_price_per_1m_tokens
            FROM benchmark_scores bs
            JOIN benchmarks b ON bs.benchmark_id = b.benchmark_id
            JOIN model_versions mv ON bs.version_id = mv.version_id
            JOIN model_families mf ON mv.family_id = mf.family_id
            JOIN providers p ON mf.provider_id = p.provider_id
            LEFT JOIN pricing_history ph ON mv.version_id = ph.version_id
            WHERE b.name = 'Chatbot Arena Elo'
            ORDER BY bs.score DESC
            LIMIT 20
        """,
        "chart_type": "bar_elo"
    },
    "SWE-bench Verified Leaders": {
        "desc": "Models ranked on real-world GitHub bug resolution and software engineering tasks.",
        "query": """
            SELECT mv.version_name, p.name AS provider_name, p.headquarters_country,
                   bs.score AS swe_bench_verified_pct, ph.input_price_per_1m_tokens, mv.context_length
            FROM benchmark_scores bs
            JOIN benchmarks b ON bs.benchmark_id = b.benchmark_id
            JOIN model_versions mv ON bs.version_id = mv.version_id
            JOIN model_families mf ON mv.family_id = mf.family_id
            JOIN providers p ON mf.provider_id = p.provider_id
            LEFT JOIN pricing_history ph ON mv.version_id = ph.version_id
            WHERE b.name = 'SWE-bench Verified'
            ORDER BY bs.score DESC
            LIMIT 20
        """,
        "chart_type": "bar_swe"
    },
    "Extreme Context Window Leaders": {
        "desc": "Models with maximum context capacity for document ingestion and long-horizon tasks.",
        "query": """
            SELECT mv.version_name, p.name AS provider_name, p.headquarters_country,
                   mv.context_length, mv.max_output_tokens, ph.input_price_per_1m_tokens
            FROM model_versions mv
            JOIN model_families mf ON mv.family_id = mf.family_id
            JOIN providers p ON mf.provider_id = p.provider_id
            LEFT JOIN pricing_history ph ON mv.version_id = ph.version_id
            WHERE mv.context_length >= 100000
            ORDER BY mv.context_length DESC
            LIMIT 20
        """,
        "chart_type": "bar_ctx"
    }
}


def get_analytics_report(report_name: str, currency: str = "USD ($)") -> Tuple[List[Dict[str, Any]], float, str]:
    """Executes pre-configured query, converts pricing fields to active currency, and returns rows, latency, chart type."""
    meta = REPORTS_REGISTRY.get(report_name)
    if not meta:
        return [], 0.0, ""

    curr_info = get_currency_info(currency)
    rate = curr_info["rate"]

    t0 = time.perf_counter()
    raw = BackendService.execute_analytical_report(meta["query"])
    latency_ms = (time.perf_counter() - t0) * 1000.0

    processed = []
    for row in raw:
        r_dict = dict(row)
        if "input_price_per_1m_tokens" in r_dict and r_dict["input_price_per_1m_tokens"] is not None:
            r_dict["input_price_converted"] = round(float(r_dict["input_price_per_1m_tokens"]) * rate, 3)
        if "output_price_per_1m_tokens" in r_dict and r_dict["output_price_per_1m_tokens"] is not None:
            r_dict["output_price_converted"] = round(float(r_dict["output_price_per_1m_tokens"]) * rate, 3)
        processed.append(r_dict)

    return processed, latency_ms, meta.get("chart_type", "")


def get_schema_counts() -> Dict[str, int]:
    """Retrieves record counts across all 17 database tables."""
    tables_list = [
        "providers", "model_families", "model_versions", "pricing_history",
        "capabilities", "model_capabilities", "benchmarks", "benchmark_scores",
        "use_cases", "model_use_cases", "tags", "model_tags",
        "user_reviews", "error_reports", "comparison_logs", "search_logs", "api_endpoints"
    ]
    return BackendService.get_table_counts(tables_list)


# -----------------------------------------------------------------------------
# BENCHMARK SUITE MATRIX & PROFILE COMPACT RANKS
# -----------------------------------------------------------------------------

def get_model_benchmark_ranks(version_id: int) -> List[Dict[str, Any]]:
    """
    Returns benchmark scores for a single model along with its relative rank
    (e.g. '#4 of 100') among all evaluated models in each suite.
    """
    benchmarks = BackendService.get_model_benchmarks(version_id) or []
    results = []
    for b in benchmarks:
        b_id = b.get("benchmark_id")
        b_name = b.get("benchmark_name") or b.get("benchmark", "Unknown")
        sc = float(b.get("score") or 0.0)
        max_s = float(b.get("max_score") or 100.0)
        pct = round((sc / max_s) * 100.0, 1) if max_s > 0 else 0.0

        rank_str = "#1 of 100"
        rank_num = 1
        total_eval = 100
        if b_id:
            suite_board = BackendService.get_leaderboard_for_suite(b_id) or []
            total_eval = max(len(suite_board), 1)
            for idx, item in enumerate(suite_board):
                if item.get("version_id") == version_id:
                    rank_num = idx + 1
                    break
            rank_str = f"#{rank_num} of {total_eval}"

        disp_score = f"{sc:.1f} Elo" if "Elo" in b_name else f"{sc:.1f}%"
        results.append({
            "suite_id": b_id,
            "suite_name": b_name,
            "category": b.get("category", "General"),
            "score": sc,
            "display_score": disp_score,
            "max_score": max_s,
            "pct_score": pct,
            "rank": rank_num,
            "total": total_eval,
            "rank_str": rank_str
        })
    return results


def get_all_benchmarks_matrix(
    filters: Optional[Dict[str, Any]] = None,
    currency: str = "USD ($)"
) -> List[Dict[str, Any]]:
    """
    Generates a dense cross-comparison matrix of all models across all benchmark suites.
    Columns include Model, Lab, each benchmark suite score, average score, and input price.
    """
    filters = filters or {}
    labs_filter = filters.get("labs") or []
    reasoning_only = bool(filters.get("reasoning_only", False))
    curr_info = get_currency_info(currency)
    rate = curr_info["rate"]

    all_models = BackendService.get_all_models_for_catalog() or []
    suites = BackendService.get_all_benchmark_suites() or []
    priority_order = [
        "Chatbot Arena Elo",
        "SWE-bench Verified",
        "MMLU",
        "GPQA Diamond",
        "GSM8K",
        "HumanEval",
        "MATH",
        "AIME 2024",
        "ARC-AGI",
        "LiveCodeBench"
    ]
    suites_sorted = sorted(suites, key=lambda s: priority_order.index(s["name"]) if s["name"] in priority_order else 99)
    suite_names = [s["name"] for s in suites_sorted]

    # Pre-cache leaderboard scores for fast lookup
    suite_scores_map = {}
    for s in suites:
        s_board = BackendService.get_leaderboard_for_suite(s["benchmark_id"]) or []
        suite_scores_map[s["name"]] = {row["version_id"]: float(row.get("score") or 0.0) for row in s_board}

    matrix_rows = []
    for m in all_models:
        if labs_filter and m["provider_name"] not in labs_filter:
            continue
        if reasoning_only and not bool(m.get("supports_reasoning")):
            continue

        vid = m["version_id"]
        in_usd = float(m.get("input_price_per_1m_tokens") or 0.0)
        in_conv = round(in_usd * rate, 3)

        total_sc = 0.0
        count_sc = 0
        score_entries = {}
        for sname in suite_names:
            sc = suite_scores_map.get(sname, {}).get(vid, None)
            score_entries[sname] = round(sc, 1) if sc is not None else None
            if sc is not None:
                total_sc += sc
                count_sc += 1

        avg_score = round(total_sc / count_sc, 1) if count_sc > 0 else 0.0

        row = {
            "version_id": vid,
            "Model": m["version_name"],
            "Lab": m["provider_name"],
            "Average Score": avg_score,
            "Input / 1M": in_conv,
            "Rating": float(m.get("avg_rating") or 0.0),
        }
        row.update(score_entries)
        matrix_rows.append(row)

    # Default sort by Average Score descending
    matrix_rows.sort(key=lambda x: x["Average Score"], reverse=True)
    return matrix_rows


# -----------------------------------------------------------------------------
# ENTERPRISE ANALYTICS & ADVANCED REPORT BUILDER
# -----------------------------------------------------------------------------

ANALYTICS_REPORTS = {
    "Cost Overview": "Token pricing analysis, median rates, and cost spread across all models",
    "Cost vs Performance": "Scatter analysis of ingestion price vs benchmark accuracy",
    "Lab Market Share": "Foundation model catalog concentration by AI laboratory",
    "Context Window Distribution": "Context window tiers and memory capacity spread",
    "Capability Coverage": "Adoption rates of tool use, step reasoning, and vision",
    "Price Tier Breakdown": "Categorization of models into Free, Budget, Mid, and Premium tiers",
    "Rating Distribution": "Developer satisfaction and community rating metrics",
    "Incident Trends": "Production failure mode and severity analysis",
    "Model Risk Score": "Operational risk index based on incident density and validation",
    "Country/Region Breakdown": "Geographic dispersion of frontier AI model providers",
}


def get_analytics(
    report_type: str,
    filters: Optional[Dict[str, Any]] = None,
    currency: str = "USD ($)"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]], Dict[str, Any]]:
    """
    Executes dynamic analytics across the catalog and telemetry tables.
    Returns:
    - rows: list of dicts for charting and data display
    - kpis: list of 4 metric summary dicts: {"label": ..., "val": ..., "desc": ...}
    - chart_meta: configuration for altair rendering
    """
    filters = filters or {}
    labs_filter = filters.get("labs") or []
    models_filter = filters.get("models") or []
    group_by = filters.get("group_by", "lab").lower()
    curr_info = get_currency_info(currency)
    rate = curr_info["rate"]
    sym = curr_info["symbol"]

    raw_models = BackendService.get_all_models_for_catalog() or []
    if labs_filter:
        raw_models = [m for m in raw_models if m["provider_name"] in labs_filter]
    if models_filter:
        raw_models = [m for m in raw_models if m["version_name"] in models_filter or m["version_id"] in models_filter]

    rows = []
    kpis = []
    chart_meta = {}

    # 1. Cost Overview
    if report_type == "Cost Overview":
        prices = [float(m.get("input_price_per_1m_tokens") or 0.0) * rate for m in raw_models]
        out_prices = [float(m.get("output_price_per_1m_tokens") or 0.0) * rate for m in raw_models]
        avg_in = np.mean(prices) if prices else 0.0
        med_in = float(np.median(prices)) if prices else 0.0
        min_p = min(prices) if prices else 0.0
        max_p = max(prices) if prices else 0.0

        kpis = [
            {"label": "Avg Input Price", "val": f"{sym}{avg_in:.3f}", "desc": f"Per 1M tokens in {currency}"},
            {"label": "Median Ingestion", "val": f"{sym}{med_in:.3f}", "desc": "50th percentile market baseline"},
            {"label": "Lowest Available", "val": f"{sym}{min_p:.3f}", "desc": "Most cost-effective model"},
            {"label": "Highest Frontier", "val": f"{sym}{max_p:.3f}", "desc": "Flagship reasoning peak price"},
        ]
        for m in sorted(raw_models, key=lambda x: float(x.get("input_price_per_1m_tokens") or 0.0))[:25]:
            rows.append({
                "Model": m["version_name"],
                "Lab": m["provider_name"],
                f"Input / 1M ({sym})": round(float(m.get("input_price_per_1m_tokens") or 0.0) * rate, 3),
                f"Output / 1M ({sym})": round(float(m.get("output_price_per_1m_tokens") or 0.0) * rate, 3),
                "Context": int(m.get("context_length") or 0),
            })
        chart_meta = {"type": "bar", "x": f"Input / 1M ({sym})", "y": "Model", "title": f"Input Price per 1M Tokens ({sym})"}

    # 2. Cost vs Performance
    elif report_type == "Cost vs Performance":
        all_benchmarks = BackendService.get_leaderboard_for_suite(1) or []
        bench_map = {b["version_id"]: float(b.get("score") or 0.0) for b in all_benchmarks}

        scored_models = []
        for m in raw_models:
            vid = m["version_id"]
            p_conv = round(float(m.get("input_price_per_1m_tokens") or 0.0) * rate, 3)
            sc = bench_map.get(vid, round(float(m.get("avg_rating") or 3.5) * 16.0, 1))
            scored_models.append({
                "Model": m["version_name"],
                "Lab": m["provider_name"],
                f"Price ({sym}/1M)": p_conv,
                "Performance Score": sc,
                "Context": int(m.get("context_length") or 0)
            })

        rows = scored_models
        scores = [r["Performance Score"] for r in rows]
        med_score = float(np.median(scores)) if scores else 0.0
        efficiency_champ = max(rows, key=lambda x: (x["Performance Score"] / max(x[f"Price ({sym}/1M)"], 0.01))) if rows else None
        champ_name = efficiency_champ["Model"] if efficiency_champ else "None"

        kpis = [
            {"label": "Value Leader", "val": champ_name, "desc": "Highest performance per currency unit"},
            {"label": "Median Score", "val": f"{med_score:.1f}%", "desc": "Benchmark score across cohort"},
            {"label": "Models Analyzed", "val": str(len(rows)), "desc": "Paired price-performance data points"},
            {"label": "Frontier Spread", "val": f"{max(scores)-min(scores):.1f}%" if scores else "0", "desc": "Gap between peak & base model"},
        ]
        chart_meta = {"type": "scatter", "x": f"Price ({sym}/1M)", "y": "Performance Score", "color": "Lab", "title": "Cost vs Benchmark Score"}

    # 3. Lab Market Share
    elif report_type == "Lab Market Share":
        lab_counts = {}
        for m in raw_models:
            lab = m["provider_name"]
            lab_counts[lab] = lab_counts.get(lab, 0) + 1

        for lab, cnt in sorted(lab_counts.items(), key=lambda x: x[1], reverse=True):
            pct = round((cnt / len(raw_models)) * 100.0, 1) if raw_models else 0.0
            rows.append({
                "Lab": lab,
                "Models Count": cnt,
                "Market Share (%)": pct
            })

        top_lab = rows[0]["Lab"] if rows else "None"
        top_share = rows[0]["Market Share (%)"] if rows else 0.0
        kpis = [
            {"label": "Dominant Vendor", "val": top_lab, "desc": f"{top_share}% of total catalog models"},
            {"label": "Active Labs", "val": str(len(rows)), "desc": "Frontier AI research organizations"},
            {"label": "Total Models", "val": str(len(raw_models)), "desc": "Indexed foundation versions"},
            {"label": "Avg Models / Lab", "val": f"{len(raw_models)/max(len(rows),1):.1f}", "desc": "Portfolio breadth per vendor"},
        ]
        chart_meta = {"type": "bar", "x": "Models Count", "y": "Lab", "title": "Models Count by Laboratory"}

    # 4. Context Window Distribution
    elif report_type == "Context Window Distribution":
        buckets = {
            "Standard (<=32k)": 0,
            "Expanded (33k - 128k)": 0,
            "High Capacity (129k - 256k)": 0,
            "Mega Context (257k - 1M)": 0,
            "Ultra Context (1M+)": 0
        }
        for m in raw_models:
            ctx = int(m.get("context_length") or 0)
            if ctx <= 32000:
                buckets["Standard (<=32k)"] += 1
            elif ctx <= 128000:
                buckets["Expanded (33k - 128k)"] += 1
            elif ctx <= 256000:
                buckets["High Capacity (129k - 256k)"] += 1
            elif ctx <= 1000000:
                buckets["Mega Context (257k - 1M)"] += 1
            else:
                buckets["Ultra Context (1M+)"] += 1

        for b_name, count in buckets.items():
            pct = round((count / max(len(raw_models), 1)) * 100.0, 1)
            rows.append({"Context Tier": b_name, "Model Count": count, "Share (%)": pct})

        ultra_count = buckets["Ultra Context (1M+)"] + buckets["Mega Context (257k - 1M)"]
        kpis = [
            {"label": "1M+ Capable", "val": str(ultra_count), "desc": "Models processing book-scale prompts"},
            {"label": "128k+ Adoption", "val": f"{round((len(raw_models)-buckets['Standard (<=32k)'])/max(len(raw_models),1)*100,1)}%", "desc": "Long context as industry baseline"},
            {"label": "Max Window", "val": "2,000k", "desc": "Largest verified memory buffer"},
            {"label": "Standard Tier", "val": str(buckets["Standard (<=32k)"]), "desc": "Models <= 32k tokens"},
        ]
        chart_meta = {"type": "bar", "x": "Model Count", "y": "Context Tier", "title": "Models by Context Memory Window"}

    # 5. Capability Coverage
    elif report_type == "Capability Coverage":
        tools_cnt = sum(1 for m in raw_models if bool(m.get("supports_tool_use")))
        reason_cnt = sum(1 for m in raw_models if bool(m.get("supports_reasoning")))
        vision_cnt = sum(1 for m in raw_models if "image" in (m.get("input_modalities") or "").lower())
        free_cnt = sum(1 for m in raw_models if bool(m.get("is_free")) or float(m.get("input_price_per_1m_tokens") or 0) == 0)

        n = max(len(raw_models), 1)
        rows = [
            {"Capability": "Tool Calling / Agentic", "Supported Models": tools_cnt, "Coverage (%)": round(tools_cnt/n*100, 1)},
            {"Capability": "Step Reasoning (CoT)", "Supported Models": reason_cnt, "Coverage (%)": round(reason_cnt/n*100, 1)},
            {"Capability": "Vision / Multimodal", "Supported Models": vision_cnt, "Coverage (%)": round(vision_cnt/n*100, 1)},
            {"Capability": "Free / Open Tier", "Supported Models": free_cnt, "Coverage (%)": round(free_cnt/n*100, 1)},
        ]
        kpis = [
            {"label": "Tool Calling Adoption", "val": f"{round(tools_cnt/n*100, 1)}%", "desc": "API function invocation support"},
            {"label": "Reasoning Models", "val": f"{round(reason_cnt/n*100, 1)}%", "desc": "Chain-of-thought architecture"},
            {"label": "Vision Native", "val": f"{round(vision_cnt/n*100, 1)}%", "desc": "Multimodal ingestion support"},
            {"label": "Zero-Cost Access", "val": f"{round(free_cnt/n*100, 1)}%", "desc": "Free research or dev tier"},
        ]
        chart_meta = {"type": "bar", "x": "Coverage (%)", "y": "Capability", "title": "Capability Market Penetration"}

    # 6. Price Tier Breakdown
    elif report_type == "Price Tier Breakdown":
        tiers = {"Free ($0)": 0, "Budget (<$1/1M)": 0, "Mid-Tier ($1-$5/1M)": 0, "Flagship (>$5/1M)": 0}
        for m in raw_models:
            p = float(m.get("input_price_per_1m_tokens") or 0.0)
            if p == 0:
                tiers["Free ($0)"] += 1
            elif p < 1.0:
                tiers["Budget (<$1/1M)"] += 1
            elif p <= 5.0:
                tiers["Mid-Tier ($1-$5/1M)"] += 1
            else:
                tiers["Flagship (>$5/1M)"] += 1

        n = max(len(raw_models), 1)
        for t_name, count in tiers.items():
            rows.append({"Price Tier": t_name, "Model Count": count, "Share (%)": round(count/n*100, 1)})

        kpis = [
            {"label": "Budget (<$1/1M)", "val": f"{round(tiers['Budget (<$1/1M)']/n*100, 1)}%", "desc": "High-volume commodity models"},
            {"label": "Flagship (>$5)", "val": str(tiers["Flagship (>$5/1M)"]), "desc": "Frontier enterprise tier"},
            {"label": "Mid-Tier ($1-$5)", "val": str(tiers["Mid-Tier ($1-$5/1M)"]), "desc": "Balanced cost-intelligence ratio"},
            {"label": "Free Tier Models", "val": str(tiers["Free ($0)"]), "desc": "Zero token fee models"},
        ]
        chart_meta = {"type": "bar", "x": "Model Count", "y": "Price Tier", "title": "Catalog Distribution by Price Tier"}

    # 7. Rating Distribution
    elif report_type == "Rating Distribution":
        rating_buckets = {"★ 4.5 – 5.0 (Exceptional)": 0, "★ 4.0 – 4.4 (Strong)": 0, "★ 3.5 – 3.9 (Moderate)": 0, "★ < 3.5 (Developing)": 0, "Unrated": 0}
        ratings = []
        for m in raw_models:
            r = m.get("avg_rating")
            if r is None or float(r) == 0.0:
                rating_buckets["Unrated"] += 1
            else:
                rf = float(r)
                ratings.append(rf)
                if rf >= 4.5:
                    rating_buckets["★ 4.5 – 5.0 (Exceptional)"] += 1
                elif rf >= 4.0:
                    rating_buckets["★ 4.0 – 4.4 (Strong)"] += 1
                elif rf >= 3.5:
                    rating_buckets["★ 3.5 – 3.9 (Moderate)"] += 1
                else:
                    rating_buckets["★ < 3.5 (Developing)"] += 1

        n = max(len(raw_models), 1)
        for b_name, count in rating_buckets.items():
            rows.append({"Rating Tier": b_name, "Model Count": count, "Share (%)": round(count/n*100, 1)})

        avg_r = np.mean(ratings) if ratings else 0.0
        kpis = [
            {"label": "Platform Avg Rating", "val": f"★ {avg_r:.2f}", "desc": "Developer satisfaction benchmark"},
            {"label": "Exceptional Tier", "val": str(rating_buckets["★ 4.5 – 5.0 (Exceptional)"]), "desc": "Models rated 4.5+ stars"},
            {"label": "Rated Proportion", "val": f"{round(len(ratings)/n*100,1)}%", "desc": "Audited with production feedback"},
            {"label": "Unrated Models", "val": str(rating_buckets["Unrated"]), "desc": "Awaiting initial developer audits"},
        ]
        chart_meta = {"type": "bar", "x": "Model Count", "y": "Rating Tier", "title": "Developer Rating Distribution"}

    # 8. Incident Trends
    elif report_type == "Incident Trends":
        incidents = BackendService.get_all_recent_incidents(limit=200) or []
        sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        type_counts = {}
        for inc in incidents:
            sev = (inc.get("severity") or "medium").lower()
            if sev in sev_counts:
                sev_counts[sev] += 1
            et = (inc.get("error_type") or "hallucination").title()
            type_counts[et] = type_counts.get(et, 0) + 1

        for et, cnt in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            rows.append({"Failure Mode": et, "Incident Count": cnt})

        total_inc = len(incidents)
        crit_pct = round(((sev_counts["critical"] + sev_counts["high"]) / max(total_inc, 1)) * 100.0, 1)
        top_err = rows[0]["Failure Mode"] if rows else "None"
        kpis = [
            {"label": "Logged Incidents", "val": str(total_inc), "desc": "Audited production failure reports"},
            {"label": "High/Critical Share", "val": f"{crit_pct}%", "desc": "Severe anomalies or breaches"},
            {"label": "Top Failure Mode", "val": top_err, "desc": "Most prevalent production flaw"},
            {"label": "Low/Medium Incidents", "val": str(sev_counts["low"] + sev_counts["medium"]), "desc": "Minor cosmetic/refusal defects"},
        ]
        chart_meta = {"type": "bar", "x": "Incident Count", "y": "Failure Mode", "title": "Incidents by Failure Mode"}

    # 9. Model Risk Score
    elif report_type == "Model Risk Score":
        incidents = BackendService.get_all_recent_incidents(limit=200) or []
        inc_counts = {}
        for inc in incidents:
            vid = inc.get("version_id")
            if vid:
                inc_counts[vid] = inc_counts.get(vid, 0) + 1

        for m in raw_models:
            vid = m["version_id"]
            inc_cnt = inc_counts.get(vid, 0)
            rating = float(m.get("avg_rating") or 4.0)
            risk = round(min(10.0, max(0.5, (inc_cnt * 1.8) + (5.0 - rating) * 1.2)), 1)
            risk_tier = "High" if risk >= 6.0 else ("Medium" if risk >= 3.0 else "Low")
            rows.append({
                "Model": m["version_name"],
                "Lab": m["provider_name"],
                "Risk Score": risk,
                "Risk Tier": risk_tier,
                "Incidents Logged": inc_cnt,
                "Rating": rating
            })

        rows.sort(key=lambda x: x["Risk Score"], reverse=True)
        avg_risk = np.mean([r["Risk Score"] for r in rows]) if rows else 0.0
        low_risk_cnt = sum(1 for r in rows if r["Risk Tier"] == "Low")
        kpis = [
            {"label": "Avg Risk Score", "val": f"{avg_risk:.1f}/10", "desc": "Catalog operational risk baseline"},
            {"label": "Low Risk Certified", "val": f"{round(low_risk_cnt/max(len(rows),1)*100,1)}%", "desc": "Safe for enterprise deployment"},
            {"label": "High Risk Models", "val": str(sum(1 for r in rows if r["Risk Tier"] == "High")), "desc": "Models requiring sandboxing"},
            {"label": "Zero Incident Rate", "val": f"{round(sum(1 for r in rows if r['Incidents Logged']==0)/max(len(rows),1)*100,1)}%", "desc": "Clean operational track record"},
        ]
        chart_meta = {"type": "bar", "x": "Risk Score", "y": "Model", "title": "Model Risk Score Index"}

    # 10. Country/Region Breakdown
    elif report_type == "Country/Region Breakdown":
        c_counts = {}
        for m in raw_models:
            c = format_country(m.get("headquarters_country"))
            c_counts[c] = c_counts.get(c, 0) + 1

        for c, count in sorted(c_counts.items(), key=lambda x: x[1], reverse=True):
            pct = round((count / max(len(raw_models), 1)) * 100.0, 1)
            rows.append({"Country / Region": c, "Models": count, "Share (%)": pct})

        kpis = [
            {"label": "Leading Region", "val": rows[0]["Country / Region"] if rows else "US", "desc": "Highest catalog model density"},
            {"label": "Jurisdictions", "val": str(len(rows)), "desc": "Sovereign AI development nations"},
            {"label": "Top Region Share", "val": f"{rows[0]['Share (%)']}%" if rows else "0%", "desc": "Concentration in dominant hub"},
            {"label": "Global Diversity", "val": "High", "desc": "Multi-region fallback capability"},
        ]
        chart_meta = {"type": "bar", "x": "Models", "y": "Country / Region", "title": "Models by Host Jurisdiction"}

    return rows, kpis, chart_meta
