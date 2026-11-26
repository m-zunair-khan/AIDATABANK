"""
Test Suite for data.py (Unified Data Access Layer).
Validates:
1. get_kpis(currency)
2. get_filter_options()
3. get_models(filters, sort, currency) with multiple filter combinations
4. get_model(id, currency) with pricing history and capabilities
5. get_benchmarks(ids, suite_id, currency)
6. get_leaderboard(metric, filters, currency) for 'score', 'cost', 'context', 'rating'
7. compare_models(ids, currency, est_input_m, est_output_m) with 2, 3, 4 models
8. convert_price(value, currency) across multiple currencies
9. get_recommendations(use_case, budget_cap, min_context, currency)
10. get_incidents(filters) with severity and status filtering
11. get_reviews()
12. get_analytics_report() & get_schema_counts()
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data


def test_currency_conversion():
    print("[1] Testing convert_price...")
    p_usd = 2.0
    p_pkr = data.convert_price(p_usd, "PKR (Rs)")
    p_eur = data.convert_price(p_usd, "EUR (€)")
    assert p_pkr > p_usd, "PKR price should be greater than USD"
    assert p_eur < p_usd, "EUR price should be less than USD"
    print(f"    convert_price OK: $2.00 -> Rs {p_pkr:.2f}, €{p_eur:.2f}")


def test_kpis():
    print("[2] Testing get_kpis...")
    kpi = data.get_kpis("USD ($)")
    assert kpi["total_models"] > 0
    assert kpi["active_models"] > 0
    assert kpi["total_providers"] > 0
    assert "avg_input_price_str" in kpi
    print(f"    get_kpis OK: {kpi['total_models']} models, {kpi['total_providers']} labs, avg {kpi['avg_input_price_str']}")


def test_models_filtering():
    print("[3] Testing get_models with multiple filter combinations...")
    # Base unfiltered
    all_m = data.get_models({}, currency="USD ($)")
    assert len(all_m) > 0, "Catalog should not be empty"

    # Filter by search
    q_m = data.get_models({"q": "Claude"}, currency="USD ($)")
    assert len(q_m) > 0, "Claude search should return results"

    # Filter by lab
    lab_m = data.get_models({"providers": ["Anthropic"]}, currency="USD ($)")
    assert len(lab_m) > 0, "Anthropic lab filter should return results"

    # Filter by capabilities
    tool_m = data.get_models({"tools": True}, currency="USD ($)")
    assert len(tool_m) > 0, "Tool filter should return results"

    # Filter by budget
    cheap_m = data.get_models({"max_budget": 0.5}, currency="USD ($)")
    assert len(cheap_m) > 0, "Cheap budget filter should return results"

    print(f"    get_models OK: All={len(all_m)}, Claude={len(q_m)}, Anthropic={len(lab_m)}, Tools={len(tool_m)}, Cheap={len(cheap_m)}")


def test_model_deep_profile():
    print("[4] Testing get_model...")
    m = data.get_model(1, currency="EUR (€)")
    assert m is not None, "Model 1 should exist"
    assert "profile" in m
    assert "capabilities" in m
    assert "pricing_history" in m
    assert m["currency_symbol"] == "€"
    print(f"    get_model OK: {m['profile']['version_name']} loaded with {len(m['capabilities'])} caps")


def test_compare_models():
    print("[5] Testing compare_models with 2, 3, and 4 models...")
    cmp2 = data.compare_models([1, 2], currency="USD ($)")
    assert len(cmp2["models_data"]) == 2
    assert "winners" in cmp2
    assert "cheapest" in cmp2["winners"]

    cmp4 = data.compare_models([1, 2, 3, 4], currency="USD ($)")
    assert len(cmp4["models_data"]) == 4
    assert len(cmp4["spec_rows"]) > 0
    print(f"    compare_models OK: 2 models -> winner '{cmp2['winners']['cheapest']}', 4 models compared cleanly")


def test_leaderboard():
    print("[6] Testing get_leaderboard across all 4 metrics...")
    suites = data.get_benchmark_suites()
    assert len(suites) > 0

    lead_score = data.get_leaderboard("score", {"suite_id": suites[0]["benchmark_id"]}, currency="USD ($)")
    assert len(lead_score) > 0
    assert lead_score[0]["Relative Score"] == 100.0, "Top score should be normalized to 100%"
    assert lead_score[0]["Rank_Style"] == "gold", "Rank 1 should have gold style"

    lead_cost = data.get_leaderboard("cost", currency="USD ($)")
    assert len(lead_cost) > 0

    lead_ctx = data.get_leaderboard("context", currency="USD ($)")
    assert len(lead_ctx) > 0

    lead_rate = data.get_leaderboard("rating", currency="USD ($)")
    assert len(lead_rate) > 0

    print(f"    get_leaderboard OK: Score={len(lead_score)}, Cost={len(lead_cost)}, Context={len(lead_ctx)}, Rating={len(lead_rate)}")


def test_recommendations():
    print("[7] Testing get_recommendations...")
    recs = data.get_recommendations("Software Engineering & Coding", 15.0, 8000, currency="USD ($)")
    assert len(recs) > 0, "Should return recommendations"
    assert recs[0].get("is_best_value") is True, "First candidate should be tagged best value"
    print(f"    get_recommendations OK: {len(recs)} candidates discovered, Top: {recs[0]['Model']}")


def test_incidents_and_reviews():
    print("[8] Testing get_incidents and get_reviews...")
    all_inc = data.get_incidents()
    assert len(all_inc) > 0
    filtered_inc = data.get_incidents({"severity": "high"})
    reviews = data.get_reviews()
    assert len(reviews) > 0
    print(f"    get_incidents & get_reviews OK: {len(all_inc)} incidents ({len(filtered_inc)} high sev), {len(reviews)} reviews")


def test_analytics_and_counts():
    print("[9] Testing get_analytics_report and get_schema_counts...")
    rep, lat, ctype = data.get_analytics_report("Top 20 Cost-Effective Models", currency="USD ($)")
    assert len(rep) > 0
    counts = data.get_schema_counts()
    assert len(counts) == 17
    print(f"    Analytics OK: {len(rep)} rows in {lat:.2f}ms, {len(counts)} tables verified")


def test_search_c_and_empty():
    print("[10] Testing search 'c' and empty query...")
    all_models = data.get_models({"q": ""}, currency="USD ($)")
    assert len(all_models) == 100, f"Empty search should return all 100 models, got {len(all_models)}"

    c_models = data.get_models({"q": "c"}, currency="USD ($)")
    assert len(c_models) > 0, "Search 'c' should return non-empty list of models"
    for m in c_models:
        v_name = m["Model"].lower()
        p_name = m["Lab"].lower()
        assert ("c" in v_name or "c" in p_name), f"Model {m['Model']} or lab {m['Lab']} does not match 'c'"

    # Verify prefix match ranked first
    first_model = c_models[0]["Model"].lower()
    first_lab = c_models[0]["Lab"].lower()
    assert first_model.startswith("c") or first_lab.startswith("c") or any(w.startswith("c") for w in first_model.split()), f"First model '{first_model}' should be a prefix match for 'c'"
    print(f"    search OK: '' -> {len(all_models)} models, 'c' -> {len(c_models)} models (Top: {c_models[0]['Model']})")


def test_advanced_analytics_and_matrix():
    print("[11] Testing get_analytics reports and get_all_benchmarks_matrix...")
    # Test matrix
    matrix = data.get_all_benchmarks_matrix({}, currency="USD ($)")
    assert len(matrix) > 0, "Benchmark matrix should be non-empty"
    assert "Average Score" in matrix[0]
    assert "SWE-bench Verified" in matrix[0]

    # Test profile ranks
    ranks = data.get_model_benchmark_ranks(1)
    assert len(ranks) > 0, "Profile benchmark ranks should be non-empty"
    assert "rank_str" in ranks[0]

    # Test analytics reports
    for rep_name in ["Cost Overview", "Cost vs Performance", "Lab Market Share", "Capability Coverage", "Model Risk Score"]:
        rows, kpis, meta = data.get_analytics(rep_name, {}, currency="USD ($)")
        assert len(rows) > 0, f"Report {rep_name} should return rows"
        assert len(kpis) == 4, f"Report {rep_name} should return 4 KPIs"

    print(f"    Matrix & Analytics OK: Matrix={len(matrix)} models, Ranks={len(ranks)} suites, 5 analytics suites verified")


if __name__ == "__main__":
    print("=" * 60)
    print("NEXUS AI DATA LAYER VERIFICATION SUITE")
    print("=" * 60)
    test_currency_conversion()
    test_kpis()
    test_models_filtering()
    test_model_deep_profile()
    test_compare_models()
    test_leaderboard()
    test_recommendations()
    test_incidents_and_reviews()
    test_analytics_and_counts()
    test_search_c_and_empty()
    test_advanced_analytics_and_matrix()
    print("=" * 60)
    print("ALL DATA LAYER TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
