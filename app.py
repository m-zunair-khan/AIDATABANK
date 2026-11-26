"""
NEXUS AI — Frontier Model Intelligence & Enterprise Registry
============================================================
Commercial-grade AI intelligence platform and model analytics engine.
Unified with pure-Python DSA algorithms and backed by a 17-table relational schema.
Design System: Ink + Acid Lime (Flat, Sharp, Responsive).
Data Access: Exclusively through data.py layer.
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import time

# Centralized Data Layer & Styling
import data
from ui.styles import (
    apply_theme, apply_altair_dark_theme,
    format_country, format_context,
    CURRENCIES, CHART_PALETTE
)


def render_html(html_str: str):
    """Safely renders HTML in Streamlit."""
    if hasattr(st, "html"):
        st.html(html_str)
    else:
        clean_lines = [line.strip() for line in html_str.strip().splitlines() if line.strip()]
        cleaned_html = "".join(clean_lines)
        st.markdown(cleaned_html, unsafe_allow_html=True)


# --- Page Configuration ---
st.set_page_config(
    page_title="NEXUS AI — Model Registry",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply cohesive Ink + Acid Lime design system
apply_theme()


# ==============================================================================
# SHARED SESSION STATE INITIALIZATION (Fixed Keys)
# ==============================================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = f"nexus-{int(time.time())}"

if "currency" not in st.session_state:
    st.session_state.currency = "USD ($)"

if "selected_models" not in st.session_state:
    st.session_state.selected_models = 1

if "compare_list" not in st.session_state:
    st.session_state.compare_list = [1, 2]

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "Table"

if "active_preset" not in st.session_state:
    st.session_state.active_preset = "All"

if "dismissed_help" not in st.session_state:
    st.session_state.dismissed_help = {}

if "matcher_results" not in st.session_state:
    st.session_state.matcher_results = None

if "search_counter" not in st.session_state:
    st.session_state.search_counter = 0

if "filter_counter" not in st.session_state:
    st.session_state.filter_counter = 0

if "dsa_sort_algorithm" not in st.session_state:
    st.session_state.dsa_sort_algorithm = "merge"

if "saved_analytics_presets" not in st.session_state:
    st.session_state.saved_analytics_presets = {}

DEFAULT_FILTERS = {
    "q": "",
    "providers": [],
    "countries": [],
    "capabilities": [],
    "max_budget": 0,
    "min_ctx": 0,
    "sort_by": "Cost: Low to High",
}

if "active_filters" not in st.session_state:
    st.session_state.active_filters = dict(DEFAULT_FILTERS)

curr_info = data.get_currency_info(st.session_state.currency)


# ==============================================================================
# GLOBAL UI COMPONENTS (Header, Stat Cards, Sidebar)
# ==============================================================================

def render_header(page_key: str, page_title: str, page_desc: str, help_title: str = "", help_desc: str = ""):
    """Renders page header, currency selector, and dismissible contextual help."""
    col_left, col_curr = st.columns([5, 1.4])
    with col_left:
        render_html("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <span style="color: #C8F169; font-size: 1.25rem; font-weight: 800;">◆</span>
            <span style="color: #EDEFE9; font-size: 1.2rem; font-weight: 700; letter-spacing: -0.02em;">NEXUS AI</span>
            <span class="nexus-badge badge-neutral" style="font-size: 0.68rem; padding: 2px 7px; border-radius: 4px;">Enterprise</span>
        </div>
        """)
        st.markdown(f'<div class="nexus-page-title">{page_title}</div><div class="nexus-page-desc">{page_desc}</div>', unsafe_allow_html=True)
    with col_curr:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        curr_keys = list(CURRENCIES.keys())
        curr_idx = curr_keys.index(st.session_state.currency) if st.session_state.currency in curr_keys else 0
        selected_curr = st.selectbox(
            "Billing Currency",
            curr_keys,
            index=curr_idx,
            help="Select your operational billing currency. Converted across all tables and cost simulations.",
            key=f"curr_sel_{page_key}"
        )
        if selected_curr != st.session_state.currency:
            st.session_state.currency = selected_curr
            st.rerun()

    # Dismissible "How to use" guidance card on first visit
    if help_title and not st.session_state.dismissed_help.get(page_key, False):
        h_col, b_col = st.columns([11, 1])
        with h_col:
            render_html(f"""
            <div class="nexus-help-box">
                <div>
                    <div class="nexus-help-title">{help_title}</div>
                    <div class="nexus-help-desc">{help_desc}</div>
                </div>
            </div>
            """)
        with b_col:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("✕", key=f"dismiss_btn_{page_key}", help="Dismiss this guide"):
                st.session_state.dismissed_help[page_key] = True
                st.rerun()


def render_stat_cards():
    """Renders one row of equal-height flat stat cards with secondary-gray info tooltips."""
    kpi_data = data.get_kpis(st.session_state.currency)
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    cards = [
        ("Models", str(kpi_data['total_models']), "Total foundation models indexed in the catalog."),
        ("Active", str(kpi_data['active_models']), "Models currently deployed and operational in production."),
        ("Labs", str(kpi_data['total_providers']), "Distinct AI research laboratories and frontier vendors."),
        ("Avg Input", kpi_data['avg_input_price_str'], f"Average token ingestion cost per 1M tokens in {st.session_state.currency}."),
        ("Max Context", kpi_data['max_context_str'], "Largest verified context window capacity (2M tokens)."),
        ("Benchmarks", f"{kpi_data['total_benchmarks']:,}", "Verified quantitative benchmark evaluation results.")
    ]
    cols = [k1, k2, k3, k4, k5, k6]
    for idx, (col, (label, val, tooltip)) in enumerate(zip(cols, cards)):
        with col:
            pos_cls = "nexus-card-pos-first" if idx == 0 else ("nexus-card-pos-last" if idx == len(cards) - 1 else "nexus-card-pos-mid")
            render_html(f"""
            <div class="nexus-kpi-card {pos_cls}">
                <div class="nexus-kpi-label-row">
                    <span class="nexus-kpi-label">{label}</span>
                    <span class="nexus-card-info-badge">ⓘ</span>
                </div>
                <div class="nexus-kpi-val">{val}</div>
                <div class="nexus-card-tooltip">
                    <div class="nexus-tooltip-hdr">CATALOG METRIC</div>
                    <div class="nexus-tooltip-title">{label}: <span style="color:#C8F169;">{val}</span></div>
                    <div class="nexus-tooltip-body">{tooltip}</div>
                </div>
            </div>
            """)
    st.write("")


def render_recent_history_sidebar():
    """Renders Recently Viewed Models from Circular Queue DSA in the sidebar."""
    recent_items = data.get_recent_views(st.session_state.session_id)
    if recent_items:
        with st.sidebar:
            st.markdown("<div style='font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #A3A89C; margin-bottom: 8px;'>RECENT HISTORY (CIRCULAR QUEUE)</div>", unsafe_allow_html=True)
            seen_vids = set()
            unique_recent = []
            for item in recent_items:
                vid = item.get("version_id") if isinstance(item, dict) else item
                if vid and vid not in seen_vids:
                    seen_vids.add(vid)
                    unique_recent.append(item)
            for idx, item in enumerate(unique_recent):
                vid = item.get("version_id")
                vname = item.get("version_name", "Model")
                if st.button(f"▸ {vname}", key=f"hist_btn_{vid}_{idx}", help=f"Jump to {vname} profile", use_container_width=True):
                    st.session_state.selected_models = vid
                    st.switch_page(nav_pages["profile"])


# ==============================================================================
# WORKSPACE 1: MODEL DIRECTORY (OpenRouter-style)
# ==============================================================================
def page_directory():
    render_header(
        "directory",
        "Frontier Model Directory",
        "Dense, sortable catalog of frontier models with verified pricing, context sizes, and operational capabilities.",
        help_title="Model Directory Workspace",
        help_desc="Filter models by lab, budget, context, or capabilities. Select rows to compare or inspect deep technical profiles."
    )
    render_stat_cards()
    render_recent_history_sidebar()

    provider_options, country_options, _ = data.get_filter_options()

    # Search Bar (Trie DSA & Substring Matching)
    s_col1, s_col2 = st.columns([5, 1.2])
    with s_col1:
        current_q = st.session_state.active_filters.get("q", "")
        q_val = st.text_input(
            "Search Catalog",
            value=current_q,
            placeholder="Search by name, provider, or architecture (e.g. Claude 3.5, GPT-4, Llama 3, Gemini, Command)...",
            label_visibility="collapsed",
            help="Instant search matching across model name, laboratory, and model family.",
            key=f"dir_search_box_{st.session_state.filter_counter}"
        )
        if q_val != current_q:
            st.session_state.active_filters["q"] = q_val
            st.rerun()

    with s_col2:
        has_active_filters = (
            bool(st.session_state.active_filters.get("q")) or
            bool(st.session_state.active_filters.get("providers")) or
            bool(st.session_state.active_filters.get("capabilities")) or
            st.session_state.active_filters.get("min_ctx", 0) > 0 or
            st.session_state.active_preset != "All" or
            st.session_state.active_filters.get("sort_by") not in ("Cost: Low to High", "Input: Low to High")
        )
        if has_active_filters:
            btn_lbl = "Clear Search" if (st.session_state.active_filters.get("q") and not bool(st.session_state.active_filters.get("providers")) and not bool(st.session_state.active_filters.get("capabilities")) and st.session_state.active_filters.get("min_ctx", 0) == 0) else "Reset All"
            if st.button(btn_lbl, key=f"dir_clear_search_btn_{st.session_state.filter_counter}", help="Clear search and reset all active filters", use_container_width=True):
                st.session_state.active_filters = dict(DEFAULT_FILTERS)
                st.session_state.active_preset = "All"
                st.session_state.search_counter += 1
                st.session_state.filter_counter += 1
                st.rerun()

    # Trie Autocomplete Clickable Pills
    cur_q = st.session_state.active_filters.get("q", "").strip()
    if cur_q:
        auto_suggs = data.autocomplete_suggestions(cur_q, limit=5)
        if auto_suggs:
            st.markdown("<small style='color: #A3A89C; font-weight: 500;'>Trie Autocomplete (Click to fill): </small>", unsafe_allow_html=True)
            sugg_cols = st.columns(min(len(auto_suggs), 5))
            for idx, s in enumerate(auto_suggs[:5]):
                with sugg_cols[idx]:
                    s_name = s.get("name", "")
                    if st.button(s_name, key=f"sugg_pill_{idx}_{st.session_state.filter_counter}", use_container_width=True):
                        st.session_state.active_filters["q"] = s_name
                        st.session_state.search_counter += 1
                        st.session_state.filter_counter += 1
                        st.rerun()
            st.write("")

    # Presets Row (Cheapest, Largest context, Best rated, Tool calling, Reasoning)
    p_cols = st.columns([1, 1.2, 1.3, 1.2, 1.2, 1.2, 2.5])
    with p_cols[0]:
        all_active = "active" if st.session_state.active_preset == "All" else ""
        if st.button("All", key="preset_all", use_container_width=True, type="primary" if all_active else "secondary"):
            st.session_state.active_preset = "All"
            st.session_state.active_filters = dict(DEFAULT_FILTERS)
            st.session_state.search_counter += 1
            st.session_state.filter_counter += 1
            st.rerun()
    with p_cols[1]:
        cheap_active = "active" if st.session_state.active_preset == "Cheapest" else ""
        if st.button("Cheapest", key="preset_cheap", use_container_width=True, type="primary" if cheap_active else "secondary"):
            st.session_state.active_preset = "Cheapest"
            st.session_state.active_filters["sort_by"] = "Cost: Low to High"
            st.session_state.active_filters["max_budget"] = float(round(1.0 * curr_info["rate"], 1))
            st.session_state.filter_counter += 1
            st.rerun()
    with p_cols[2]:
        ctx_active = "active" if st.session_state.active_preset == "Largest context" else ""
        if st.button("Largest context", key="preset_ctx", use_container_width=True, type="primary" if ctx_active else "secondary"):
            st.session_state.active_preset = "Largest context"
            st.session_state.active_filters["sort_by"] = "Context: High to Low"
            st.session_state.active_filters["min_ctx"] = 128000
            st.session_state.filter_counter += 1
            st.rerun()
    with p_cols[3]:
        rate_active = "active" if st.session_state.active_preset == "Best rated" else ""
        if st.button("Best rated", key="preset_rate", use_container_width=True, type="primary" if rate_active else "secondary"):
            st.session_state.active_preset = "Best rated"
            st.session_state.active_filters["sort_by"] = "Rating: High to Low"
            st.session_state.filter_counter += 1
            st.rerun()
    with p_cols[4]:
        tool_active = "active" if st.session_state.active_preset == "Tool calling" else ""
        if st.button("Tool calling", key="preset_tool", use_container_width=True, type="primary" if tool_active else "secondary"):
            st.session_state.active_preset = "Tool calling"
            st.session_state.active_filters["capabilities"] = ["Tool Calling"]
            st.session_state.filter_counter += 1
            st.rerun()
    with p_cols[5]:
        cot_active = "active" if st.session_state.active_preset == "Reasoning" else ""
        if st.button("Reasoning", key="preset_cot", use_container_width=True, type="primary" if cot_active else "secondary"):
            st.session_state.active_preset = "Reasoning"
            st.session_state.active_filters["capabilities"] = ["Reasoning"]
            st.session_state.filter_counter += 1
            st.rerun()

    # Visible Filter Row (NO EXPANDER per spec)
    f1, f2, f3, f4, f5 = st.columns([2.5, 2.2, 2.6, 2.0, 2.2])
    with f1:
        sel_labs = st.multiselect(
            "AI Lab / Vendor",
            provider_options,
            default=st.session_state.active_filters.get("providers", []),
            placeholder="All Labs",
            help="Filter by AI foundation model research organization.",
            key=f"dir_filter_labs_{st.session_state.filter_counter}"
        )
    with f2:
        cap_opts = ["Tool Calling", "Reasoning", "Vision", "Free"]
        sel_caps = st.multiselect(
            "Capabilities",
            cap_opts,
            default=st.session_state.active_filters.get("capabilities", []),
            placeholder="All Capabilities",
            help="Filter models supporting tool use, step reasoning (CoT), vision, or free tiers.",
            key=f"dir_filter_caps_{st.session_state.filter_counter}"
        )
    with f3:
        max_slider_val = float(round(25.0 * curr_info["rate"], 1))
        cur_b = float(st.session_state.active_filters.get("max_budget") or 0)
        # If 0 or >= max_slider_val, slider sits at max_slider_val (Any Price / No filter)
        cur_pos = max_slider_val if (cur_b <= 0 or cur_b >= max_slider_val) else min(cur_b, max_slider_val)
        slider_label = f"Max Price ({curr_info['symbol']}/1M) · Any" if cur_pos >= max_slider_val else f"Max Price ({curr_info['symbol']}/1M)"
        step_val = 0.5 if curr_info["rate"] <= 2.0 else round(0.5 * curr_info["rate"], 1)
        max_price = st.slider(
            slider_label,
            0.0, max_slider_val, cur_pos, step_val,
            help=f"Maximum token ingestion price per 1M tokens in {st.session_state.currency}. Set to maximum for Any Price (no filter).",
            key=f"dir_filter_price_slider_{st.session_state.filter_counter}"
        )
    with f4:
        ctx_opts = [0, 8000, 32000, 128000, 200000, 1000000]
        cur_ctx = st.session_state.active_filters.get("min_ctx", 0)
        ctx_idx = ctx_opts.index(cur_ctx) if cur_ctx in ctx_opts else 0
        min_context = st.selectbox(
            "Min Context",
            ctx_opts,
            index=ctx_idx,
            format_func=lambda x: "All Sizes" if x == 0 else f"{format_context(x)} Tokens",
            help="Minimum memory window context required for prompt tokens.",
            key=f"dir_filter_ctx_sel_{st.session_state.filter_counter}"
        )
    with f5:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        v_c1, v_c2, v_c3 = st.columns([1, 1, 1.2])
        with v_c1:
            if st.button("Table", key="btn_view_table", use_container_width=True, type="primary" if st.session_state.view_mode == "Table" else "secondary"):
                st.session_state.view_mode = "Table"
                st.rerun()
        with v_c2:
            if st.button("Cards", key="btn_view_cards", use_container_width=True, type="primary" if st.session_state.view_mode == "Cards" else "secondary"):
                st.session_state.view_mode = "Cards"
                st.rerun()
        with v_c3:
            if st.button("Reset", key=f"dir_reset_filters_btn_{st.session_state.filter_counter}", help="Reset all filters to defaults", use_container_width=True):
                st.session_state.active_filters = dict(DEFAULT_FILTERS)
                st.session_state.active_preset = "All"
                st.session_state.search_counter += 1
                st.session_state.filter_counter += 1
                st.toast("Filters reset to defaults.")
                st.rerun()

    # Sync filter state (0 means Any Price / uncapped)
    effective_budget = 0 if max_price >= max_slider_val else max_price
    updated_filters = {
        "q": st.session_state.active_filters.get("q", ""),
        "providers": sel_labs,
        "capabilities": sel_caps,
        "max_budget": effective_budget,
        "min_ctx": min_context,
        "sort_by": st.session_state.active_filters.get("sort_by", "Cost: Low to High"),
    }
    if updated_filters != st.session_state.active_filters:
        data.push_filter_state(st.session_state.session_id, dict(st.session_state.active_filters))
        st.session_state.active_filters = updated_filters

    # Fetch models through Data Layer with chosen DSA algorithm
    catalog_models = data.get_models(
        filters=st.session_state.active_filters,
        sort=st.session_state.active_filters.get("sort_by", "Cost: Low to High"),
        currency=st.session_state.currency,
        algorithm=st.session_state.get("dsa_sort_algorithm", "merge")
    )

    total_models = data.get_kpis(st.session_state.currency)["total_models"]

    # Result count & Action bar
    rc1, rc2, rc3 = st.columns([3, 1.8, 2.4])
    with rc1:
        st.markdown(f"<span style='color: #A3A89C; font-size: 0.88rem; font-weight: 500;'>Showing <strong style='color: #EDEFE9;'>{len(catalog_models)}</strong> of <strong style='color: #EDEFE9;'>{total_models}</strong> models</span>", unsafe_allow_html=True)
    with rc2:
        if st.button("Undo Filter (Stack)", key="dir_undo_btn", help="Undo last filter change using Stack DSA", use_container_width=True):
            popped = data.undo_filter_state(st.session_state.session_id)
            if popped:
                st.session_state.active_filters = popped
                st.session_state.search_counter += 1
                st.session_state.filter_counter += 1
                st.toast("Restored previous filter state from Stack.")
                st.rerun()
            else:
                st.toast("No previous filter states stored in Stack.")
    with rc3:
        if st.session_state.view_mode == "Table":
            dir_t_mode = st.radio(
                "View as:",
                ["Visual Table", "Data Grid (Select)"],
                horizontal=True,
                index=0 if st.session_state.get("dir_table_style_radio") != "Data Grid (Select)" else 1,
                key="dir_table_style_radio",
                label_visibility="collapsed"
            )
        else:
            dir_t_mode = "Cards"

    # Empty State with working Reset
    if not catalog_models:
        cur_q_str = st.session_state.active_filters.get("q", "").strip()
        empty_title = f'No models match "{cur_q_str}"' if cur_q_str else "No models match these filters"
        btn_label = "Clear search" if cur_q_str else "Reset Filters"
        render_html(f"""
        <div style="background: #131512; border: 1px solid #242722; border-radius: 8px; padding: 24px; text-align: center; margin-top: 14px;">
            <div style="font-size: 1.1rem; font-weight: 600; color: #EDEFE9; margin-bottom: 6px;">{empty_title}</div>
            <div style="font-size: 0.86rem; color: #A3A89C; margin-bottom: 14px;">Try loosening your budget cap, lowering context requirements, or clearing your search prefix.</div>
        </div>
        """)
        if st.button(btn_label, key=f"empty_reset_btn_{st.session_state.filter_counter}", type="primary"):
            st.session_state.active_filters = dict(DEFAULT_FILTERS)
            st.session_state.active_preset = "All"
            st.session_state.search_counter += 1
            st.session_state.filter_counter += 1
            st.rerun()
        return

    sym = curr_info["symbol"]

    # --------------------------------------------------------------------------
    # VIEW MODE A: TABLE VIEW (OpenRouter-style)
    # --------------------------------------------------------------------------
    if st.session_state.view_mode == "Table":
        df_models = pd.DataFrame(catalog_models)

        if dir_t_mode == "Visual Table" or dir_t_mode == "Visual SaaS Table":
            # DIRECT COLUMN DSA SORT CONTROLS
            cur_s = st.session_state.active_filters.get("sort_by", "Cost: Low to High")
            algo_badge = st.session_state.get("dsa_sort_algorithm", "merge").upper()

            st.markdown(
                f"<div style='display:flex; justify-content:space-between; align-items:center; margin-top:10px; margin-bottom:6px;'>"
                f"<span style='font-size:0.75rem; font-weight:700; color:#C8F169; letter-spacing:0.06em; text-transform:uppercase;'>"
                f"⚡ Direct Column DSA Sorting · Active: <strong style='color:#EDEFE9;'>{cur_s}</strong>"
                f"</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            col_sort_row = st.columns([1.5, 1.5, 1.6, 1.6, 1.5, 1.4, 2.0])
            with col_sort_row[0]:
                is_active = cur_s in ("Context: High to Low", "Context Window")
                if st.button("Context ⬇ Top", key="btn_col_ctx_desc", help="Sort Context Window: Top to Low (Merge Sort)", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.active_filters["sort_by"] = "Context: High to Low"
                    st.session_state.filter_counter += 1
                    st.rerun()
            with col_sort_row[1]:
                is_active = cur_s == "Context: Low to High"
                if st.button("Context ⬆ Low", key="btn_col_ctx_asc", help="Sort Context Window: Low to High", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.active_filters["sort_by"] = "Context: Low to High"
                    st.session_state.filter_counter += 1
                    st.rerun()
            with col_sort_row[2]:
                is_active = cur_s in ("Cost: Low to High", "Input: Low to High")
                if st.button("Input ⬆ Cheap", key="btn_col_in_asc", help="Sort Input Price: Low to High (Cheapest)", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.active_filters["sort_by"] = "Cost: Low to High"
                    st.session_state.filter_counter += 1
                    st.rerun()
            with col_sort_row[3]:
                is_active = cur_s in ("Cost: High to Low", "Input: High to Low")
                if st.button("Input ⬇ Top", key="btn_col_in_desc", help="Sort Input Price: High to Low (Top to Low)", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.active_filters["sort_by"] = "Cost: High to Low"
                    st.session_state.filter_counter += 1
                    st.rerun()
            with col_sort_row[4]:
                is_active = cur_s in ("Rating: High to Low", "Model Rating")
                if st.button("Rating ⬇ Best", key="btn_col_rate_desc", help="Sort Rating: High to Low (Best Rated)", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.active_filters["sort_by"] = "Rating: High to Low"
                    st.session_state.filter_counter += 1
                    st.rerun()
            with col_sort_row[5]:
                is_active = cur_s in ("Model Name: A to Z", "Model Name")
                if st.button("Model A-Z", key="btn_col_name_asc", help="Sort Model Name: Alphabetical A-Z", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.active_filters["sort_by"] = "Model Name: A to Z"
                    st.session_state.filter_counter += 1
                    st.rerun()
            with col_sort_row[6]:
                algo_choice = st.selectbox(
                    "DSA Algorithm",
                    ["Merge Sort (Stable)", "Quick Sort (Fast)"],
                    index=0 if st.session_state.get("dsa_sort_algorithm", "merge") == "merge" else 1,
                    key=f"dsa_algo_sel_{st.session_state.filter_counter}",
                    label_visibility="collapsed",
                    help="Switch between Python Merge Sort and Quick Sort DSA implementations"
                )
                picked_algo = "merge" if "Merge" in algo_choice else "quick"
                if picked_algo != st.session_state.get("dsa_sort_algorithm"):
                    st.session_state.dsa_sort_algorithm = picked_algo
                    st.rerun()

            # Dynamic column header sort indicators
            def _th_hdr(title: str, asc_name: str, desc_name: str = None, is_num: bool = False):
                arrow = ""
                is_active_col = False
                if cur_s == asc_name or (asc_name == "Cost: Low to High" and cur_s in ("Cost: Low to High", "Input: Low to High")):
                    arrow = " ▲"
                    is_active_col = True
                elif desc_name and (cur_s == desc_name or (desc_name == "Context: High to Low" and cur_s in ("Context: High to Low", "Context Window")) or (desc_name == "Rating: High to Low" and cur_s in ("Rating: High to Low", "Model Rating")) or (desc_name == "Cost: High to Low" and cur_s in ("Cost: High to Low", "Input: High to Low"))):
                    arrow = " ▼"
                    is_active_col = True
                th_cls = ' class="num"' if is_num else ""
                th_color = ' style="color: #C8F169; font-weight: 700;"' if is_active_col else ""
                return f'<th{th_cls}{th_color}>{title}{arrow}</th>'

            th_model_html = _th_hdr("Model", "Model Name: A to Z", "Model Name: Z to A")
            th_lab_html = _th_hdr("Lab", "AI Lab: A to Z", "AI Lab: Z to A")
            th_ctx_html = _th_hdr("Context", "Context: Low to High", "Context: High to Low", is_num=True)
            th_in_html = _th_hdr("Input / 1M", "Cost: Low to High", "Cost: High to Low", is_num=True)
            th_out_html = _th_hdr("Output / 1M", "Output: Low to High", "Output: High to Low", is_num=True)
            th_rate_html = _th_hdr("Rating", "Rating: Low to High", "Rating: High to Low", is_num=True)

            # High-polish HTML SaaS table (No boring spreadsheet feel)
            table_rows_html = ""
            for idx, m in enumerate(catalog_models):
                in_p = f"{sym}{m['Input / 1M']:.3f}" if m['Input / 1M'] > 0 else "Free"
                out_p = f"{sym}{m['Output / 1M']:.3f}" if m['Output / 1M'] > 0 else "Free"
                rate_str = f"★ {m['Rating']:.2f}" if (m.get('Rating') and m['Rating'] > 0) else '<span style="color: #6B6E66;">—</span>'
                caps_html = "".join([f'<span class="nexus-badge badge-neutral" style="margin-right: 4px;">{c.strip()}</span>' for c in m['Capabilities'].split("·") if c.strip() and c.strip() != "—"]) or '<span style="color: #6B6E66;">General</span>'
                family_sub = f"<div style='font-size: 0.76rem; color: #6B6E66;'>{m.get('family_name', '')}</div>" if m.get('family_name') else ""

                table_rows_html += f"""
                <tr>
                    <td style="width: 50px; color: #6B6E66; font-family: var(--font-mono); font-size: 0.78rem;">#{idx+1}</td>
                    <td>
                        <div style="font-weight: 600; color: #EDEFE9;">{m['Model']}</div>
                        {family_sub}
                    </td>
                    <td><span class="nexus-badge badge-neutral">{m['Lab']}</span></td>
                    <td class="num" style="color: #A3A89C;">{format_context(m['Context'])}</td>
                    <td class="num" style="color: #C8F169; font-weight: 700;">{in_p}</td>
                    <td class="num" style="color: #EDEFE9;">{out_p}</td>
                    <td class="num" style="color: #F5B94A;">{rate_str}</td>
                    <td>{caps_html}</td>
                </tr>
                """

            render_html(f"""
            <div class="nexus-table-container">
                <table class="nexus-table">
                    <thead>
                        <tr>
                            <th style="width: 50px;">#</th>
                            {th_model_html}
                            {th_lab_html}
                            {th_ctx_html}
                            {th_in_html}
                            {th_out_html}
                            {th_rate_html}
                            <th>Capabilities</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows_html}
                    </tbody>
                </table>
            </div>
            """)

            # Quick Action bar directly below SaaS table
            q_col1, q_col2, q_col3 = st.columns([3, 1.3, 1.3])
            with q_col1:
                model_names = [m["Model"] for m in catalog_models]
                sel_quick_name = st.selectbox("Quick Select Model to Audit or Compare:", model_names, key="dir_quick_select_box", label_visibility="collapsed")
                sel_m_item = next((m for m in catalog_models if m["Model"] == sel_quick_name), catalog_models[0])
            with q_col2:
                if st.button("Deep Profile →", key="dir_quick_prof_btn", type="primary", use_container_width=True):
                    st.session_state.selected_models = sel_m_item["version_id"]
                    st.switch_page(nav_pages["profile"])
            with q_col3:
                if st.button("+ Add to Compare", key="dir_quick_cmp_btn", use_container_width=True):
                    if sel_m_item["version_id"] not in st.session_state.compare_list:
                        st.session_state.compare_list = ([sel_m_item["version_id"]] + st.session_state.compare_list)[:4]
                        st.toast(f"Added {sel_m_item['Model']} to comparison list.")
                    else:
                        st.toast("Model is already in comparison list.")

        else:
            # Enhanced Interactive Data Grid with clean formatting and no raw numbers
            df_visible = df_models[["Model", "Lab", "Context", "Input / 1M", "Output / 1M", "Rating", "Capabilities"]].copy()
            df_visible["Context"] = df_models["Context"].apply(format_context)
            df_visible["Rating"] = df_models["Rating"].apply(lambda r: f"★ {r:.2f}" if (pd.notnull(r) and r > 0) else "—")
            df_visible["Capabilities"] = df_models["Capabilities"].replace("—", "General")

            event = st.dataframe(
                df_visible,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="multi-row",
                height=540,
                column_config={
                    "Model": st.column_config.TextColumn("Model", width="medium", help="Foundation model release version name."),
                    "Lab": st.column_config.TextColumn("Lab", width="medium", help="AI research provider and ISO country code."),
                    "Context": st.column_config.TextColumn("Context", width="small", help="Total context window capacity in tokens."),
                    "Input / 1M": st.column_config.NumberColumn(f"Input / 1M ({sym})", format=f"{sym}%.3f", help=f"Ingestion price per 1M prompt tokens in {st.session_state.currency}."),
                    "Output / 1M": st.column_config.NumberColumn(f"Output / 1M ({sym})", format=f"{sym}%.3f", help=f"Generation price per 1M completion tokens in {st.session_state.currency}."),
                    "Rating": st.column_config.TextColumn("Rating", width="small", help="Developer satisfaction rating score (1-5)."),
                    "Capabilities": st.column_config.TextColumn("Capabilities", width="medium", help="Verified operational capabilities (Tools, Reasoning, Vision)."),
                }
            )

            selected_indices = event.selection.rows if hasattr(event, "selection") and event.selection else []

            # Action Bar (Single or Multi-row selection)
            if len(selected_indices) == 1:
                sel_idx = selected_indices[0]
                sel_vid = int(df_models.iloc[sel_idx]["version_id"])
                sel_name = str(df_models.iloc[sel_idx]["Model"])
                b1, b2, b3 = st.columns([3, 1.2, 1.2])
                with b1:
                    st.markdown(f"<span style='color: #A3A89C;'>Selected: <strong style='color: #EDEFE9;'>{sel_name}</strong></span>", unsafe_allow_html=True)
                with b2:
                    if st.button("Deep Profile →", key="act_deep_prof", type="primary", use_container_width=True):
                        st.session_state.selected_models = sel_vid
                        st.switch_page(nav_pages["profile"])
                with b3:
                    if st.button("Add to Compare", key="act_add_cmp", use_container_width=True):
                        if sel_vid not in st.session_state.compare_list:
                            st.session_state.compare_list = ([sel_vid] + st.session_state.compare_list)[:4]
                            st.toast(f"Added {sel_name} to comparison list.")
                        else:
                            st.toast("Model is already in comparison list.")
            elif len(selected_indices) >= 2:
                selected_vids = [int(df_models.iloc[idx]["version_id"]) for idx in selected_indices]
                b1, b2 = st.columns([4, 1.8])
                with b1:
                    st.markdown(f"<span style='color: #C8F169; font-weight: 600;'>{len(selected_indices)} models selected in catalog</span>", unsafe_allow_html=True)
                with b2:
                    if st.button(f"Compare ({len(selected_indices)}) Models →", key="act_multi_cmp", type="primary", use_container_width=True):
                        st.session_state.compare_list = selected_vids[:4]
                        st.switch_page(nav_pages["compare"])

    # --------------------------------------------------------------------------
    # VIEW MODE B: CARDS VIEW
    # --------------------------------------------------------------------------
    else:
        card_cols = st.columns(3)
        for idx, m in enumerate(catalog_models):
            col_target = card_cols[idx % 3]
            with col_target:
                in_p = f"{sym}{m['Input / 1M']:.3f}" if m['Input / 1M'] > 0 else "Free"
                out_p = f"{sym}{m['Output / 1M']:.3f}" if m['Output / 1M'] > 0 else "Free"
                rate_str = f"★ {m['Rating']:.2f}" if m['Rating'] else "Unrated"
                family = m.get('family_name') or m['provider_name']
                max_out = format_context(m.get('max_output_tokens', 0))
                modalities = m.get('input_modalities', 'text').title()

                render_html(f"""
                <div class="nexus-model-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                        <div>
                            <div style="font-weight: 700; color: #EDEFE9; font-size: 1.0rem; letter-spacing: -0.01em;">{m['Model']}</div>
                            <div style="font-size: 0.78rem; color: #A3A89C; margin-top: 1px;">{m['Lab']} · <span style="color: #6B6E66;">{family}</span></div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-family: var(--font-mono); font-weight: 700; color: #C8F169; font-size: 0.96rem;">{in_p}</div>
                            <div style="font-size: 0.70rem; color: #6B6E66; font-family: var(--font-mono);">In / 1M</div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #A3A89C; border-top: 1px solid #1C1F1A; border-bottom: 1px solid #1C1F1A; padding: 6px 0; margin-bottom: 8px;">
                        <span>Output: <strong style="color: #EDEFE9; font-family: var(--font-mono);">{out_p}</strong></span>
                        <span>Context: <strong style="color: #EDEFE9; font-family: var(--font-mono);">{format_context(m['Context'])}</strong></span>
                        <span>Max Out: <strong style="color: #EDEFE9; font-family: var(--font-mono);">{max_out}</strong></span>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 12px;">
                        <span class="nexus-badge badge-neutral">{rate_str}</span>
                        <span class="nexus-badge badge-neutral">{modalities}</span>
                        <span class="nexus-badge badge-lime">{m['Capabilities']}</span>
                    </div>
                </div>
                """)
                cb1, cb2 = st.columns(2)
                with cb1:
                    if st.button("Deep Profile", key=f"card_prof_{m['version_id']}", use_container_width=True):
                        st.session_state.selected_models = m["version_id"]
                        st.switch_page(nav_pages["profile"])
                with cb2:
                    if st.button("+ Compare", key=f"card_cmp_{m['version_id']}", use_container_width=True):
                        if m["version_id"] not in st.session_state.compare_list:
                            st.session_state.compare_list = ([m["version_id"]] + st.session_state.compare_list)[:4]
                            st.toast(f"Added {m['Model']} to comparison list.")
                        else:
                            st.toast("Model is already in comparison list.")


# ==============================================================================
# WORKSPACE 2: HEAD-TO-HEAD COMPARISON
# ==============================================================================
def page_compare():
    render_header(
        "compare",
        "Head-to-Head Comparison",
        "Direct architectural, cost simulation, and benchmark performance comparison between candidate models.",
        help_title="Comparison Workspace",
        help_desc="Compare up to 4 models simultaneously. Adjust monthly token volume to project cost savings and review benchmark scores."
    )
    render_recent_history_sidebar()

    all_models = data.get_model_selection_list()
    model_opts = {f"{m['version_name']} ({m['provider_name']})": m['version_id'] for m in all_models}
    inv_opts = {v: k for k, v in model_opts.items()}

    # Multiselect bound to compare_list (max 4 per spec)
    current_default_keys = [inv_opts[vid] for vid in st.session_state.compare_list if vid in inv_opts]
    sel_models_keys = st.multiselect(
        "Select Models to Compare (Max 4):",
        options=list(model_opts.keys()),
        default=current_default_keys[:4],
        max_selections=4,
        help="Select between 2 and 4 foundation models for side-by-side technical evaluation.",
        key="cmp_multiselect"
    )

    if len(sel_models_keys) < 2:
        st.info("Please select at least 2 models to compare.")
        return

    st.session_state.compare_list = [model_opts[k] for k in sel_models_keys]

    # Token Cost Simulator Inputs (Stable Keys)
    st.markdown("#### Production Cost Estimator")
    cc1, cc2, cc3 = st.columns([2, 2, 3])
    with cc1:
        est_input_m = st.number_input("Monthly Input Tokens (Millions):", min_value=0.1, max_value=1000.0, value=10.0, step=1.0, key="cmp_input_tokens")
    with cc2:
        est_output_m = st.number_input("Monthly Output Tokens (Millions):", min_value=0.1, max_value=500.0, value=2.0, step=0.5, key="cmp_output_tokens")

    # Fetch comparison metrics through Data Layer
    cmp_res = data.compare_models(
        st.session_state.compare_list,
        currency=st.session_state.currency,
        est_input_m=est_input_m,
        est_output_m=est_output_m
    )

    sym = cmp_res["currency_symbol"]
    winners = cmp_res["winners"]

    with cc3:
        spend_items = "".join([
            f"<div style='display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 3px;'><span style='color: #A3A89C;'>{m['version_name']}:</span><strong style='color: #EDEFE9; font-family: var(--font-mono);'>{sym}{m['monthly_cost']:,.2f}/mo</strong></div>"
            for m in cmp_res["models_data"]
        ])
        render_html(f"""
        <div style="background: #131512; border: 1px solid #242722; border-radius: 8px; padding: 12px 16px;">
            {spend_items}
            <div style="border-top: 1px solid #242722; padding-top: 5px; margin-top: 5px; font-size: 0.80rem; color: #C8F169;">
                Cost Champion: <strong>{winners['cheapest']}</strong> ({sym}{winners['cheapest_cost']:,.2f}/mo)
            </div>
        </div>
        """)

    # Winner Strip (Cheapest, Largest Context, Best Rated)
    w1, w2, w3 = st.columns(3)
    with w1:
        render_html(f"""
        <div class="nexus-winner-item">
            <div class="nexus-winner-label">Cheapest Model</div>
            <div class="nexus-winner-name">{winners['cheapest']}</div>
            <div class="nexus-winner-sub">{sym}{winners['cheapest_cost']:,.2f} / month</div>
        </div>
        """)
    with w2:
        render_html(f"""
        <div class="nexus-winner-item">
            <div class="nexus-winner-label">Largest Context</div>
            <div class="nexus-winner-name">{winners['largest_ctx']}</div>
            <div class="nexus-winner-sub">{format_context(winners['largest_ctx_val'])} tokens buffer</div>
        </div>
        """)
    with w3:
        render_html(f"""
        <div class="nexus-winner-item">
            <div class="nexus-winner-label">Best Rated</div>
            <div class="nexus-winner-name">{winners['best_rated']}</div>
            <div class="nexus-winner-sub">★ {winners['best_rated_val']:.2f} / 5.00</div>
        </div>
        """)
    st.write("")

    # Section header with "Show only differences" toggle
    t_c1, t_c2 = st.columns([4, 1.5])
    with t_c1:
        st.markdown("#### Specification & Capability Cards")
    with t_c2:
        diff_only = st.toggle("Show only differences", value=False, key="cmp_diff_toggle", help="Hide rows where all compared models have identical values.")

    # Column-per-model Cards Layout (2 to 4 models)
    models_list = cmp_res["models_data"]
    n_models = len(models_list)
    card_cols = st.columns(n_models)

    # Compute bests for highlighting (lime badge for best, no red for worst)
    min_in_cost = min(m["input_price_conv"] for m in models_list)
    min_out_cost = min(m["output_price_conv"] for m in models_list)
    min_monthly = min(m["monthly_cost"] for m in models_list)
    max_context_len = max(m["context_length"] for m in models_list)
    max_out_tokens = max(m["max_output_tokens"] for m in models_list)
    max_user_rating = max(m["avg_rating"] for m in models_list)

    all_same_tools = len({m["supports_tool_use"] for m in models_list}) == 1
    all_same_cot = len({m["supports_reasoning"] for m in models_list}) == 1
    all_same_in = len({m["input_price_conv"] for m in models_list}) == 1
    all_same_out = len({m["output_price_conv"] for m in models_list}) == 1
    all_same_ctx = len({m["context_length"] for m in models_list}) == 1
    all_same_max_out = len({m["max_output_tokens"] for m in models_list}) == 1
    all_same_rate = len({m["avg_rating"] for m in models_list}) == 1

    for idx, m in enumerate(models_list):
        with card_cols[idx]:
            in_best = '<span class="nexus-best-badge">Best</span>' if (m["input_price_conv"] == min_in_cost and not all_same_in) else ""
            out_best = '<span class="nexus-best-badge">Best</span>' if (m["output_price_conv"] == min_out_cost and not all_same_out) else ""
            monthly_best = '<span class="nexus-best-badge">Best</span>' if (m["monthly_cost"] == min_monthly and len(models_list) > 1) else ""
            ctx_best = '<span class="nexus-best-badge">Best</span>' if (m["context_length"] == max_context_len and not all_same_ctx) else ""
            max_out_best = '<span class="nexus-best-badge">Best</span>' if (m["max_output_tokens"] == max_out_tokens and not all_same_max_out) else ""
            rate_best = '<span class="nexus-best-badge">Best</span>' if (m["avg_rating"] == max_user_rating and not all_same_rate and m["avg_rating"] > 0) else ""

            tools_val = "✓ Supported" if m["supports_tool_use"] else "✕ No"
            cot_val = "✓ Supported" if m["supports_reasoning"] else "✕ No"

            pricing_rows = ""
            if not (diff_only and all_same_in):
                pricing_rows += f'<div class="nexus-compare-row"><span class="nexus-compare-label">Input / 1M:</span><span class="nexus-compare-val">{sym}{m["input_price_conv"]:.3f}{in_best}</span></div>'
            if not (diff_only and all_same_out):
                pricing_rows += f'<div class="nexus-compare-row"><span class="nexus-compare-label">Output / 1M:</span><span class="nexus-compare-val">{sym}{m["output_price_conv"]:.3f}{out_best}</span></div>'
            pricing_rows += f'<div class="nexus-compare-row"><span class="nexus-compare-label">Est. Spend:</span><span class="nexus-compare-val" style="color: #C8F169;">{sym}{m["monthly_cost"]:,.2f}/mo{monthly_best}</span></div>'

            context_rows = ""
            if not (diff_only and all_same_ctx):
                context_rows += f'<div class="nexus-compare-row"><span class="nexus-compare-label">Context Window:</span><span class="nexus-compare-val">{format_context(m["context_length"])}{ctx_best}</span></div>'
            if not (diff_only and all_same_max_out):
                context_rows += f'<div class="nexus-compare-row"><span class="nexus-compare-label">Max Output:</span><span class="nexus-compare-val">{format_context(m["max_output_tokens"])}{max_out_best}</span></div>'

            cap_rows = ""
            if not (diff_only and all_same_rate):
                rating_str = f"★ {m['avg_rating']:.2f}" if m['avg_rating'] > 0 else "Unrated"
                cap_rows += f'<div class="nexus-compare-row"><span class="nexus-compare-label">Rating:</span><span class="nexus-compare-val">{rating_str}{rate_best}</span></div>'
            if not (diff_only and all_same_tools):
                cap_rows += f'<div class="nexus-compare-row"><span class="nexus-compare-label">Tool Calling:</span><span class="nexus-compare-val">{tools_val}</span></div>'
            if not (diff_only and all_same_cot):
                cap_rows += f'<div class="nexus-compare-row"><span class="nexus-compare-label">Reasoning:</span><span class="nexus-compare-val">{cot_val}</span></div>'

            render_html(f"""
            <div class="nexus-compare-card">
                <div class="nexus-compare-header">
                    <div class="nexus-compare-title">{m['version_name']}</div>
                    <div class="nexus-compare-meta">{m['provider_name']} · ISO {m['headquarters_country']}</div>
                </div>
                <div class="nexus-compare-section-title">Pricing & Spend</div>
                {pricing_rows}
                <div class="nexus-compare-section-title">Memory & Output</div>
                {context_rows}
                <div class="nexus-compare-section-title">Quality & Architecture</div>
                {cap_rows}
            </div>
            """)
            if st.button("Deep Profile →", key=f"cmp_prof_btn_{m['version_id']}_{idx}", use_container_width=True):
                st.session_state.selected_models = m["version_id"]
                st.switch_page(nav_pages["profile"])

    # Horizontal Grouped Bar Chart for Benchmarks using CHART_PALETTE
    st.markdown("#### Benchmark Suite Comparison")
    if cmp_res["benchmark_chart_rows"]:
        df_bench = pd.DataFrame(cmp_res["benchmark_chart_rows"])
        m_names = [m["version_name"] for m in cmp_res["models_data"]]
        color_scale = alt.Scale(domain=m_names, range=CHART_PALETTE[:len(m_names)])

        h_chart = alt.Chart(df_bench).mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3).encode(
            y=alt.Y('Benchmark:N', title=None, sort='-x', axis=alt.Axis(labelColor='#CCCFC7', labelFontSize=12)),
            x=alt.X('Score_Pct:Q', title='Score (% of Benchmark Suite Max)', scale=alt.Scale(domain=[0, 100])),
            yOffset='Model:N',
            color=alt.Color('Model:N', scale=color_scale, legend=alt.Legend(title=None, orient='top')),
            tooltip=[
                alt.Tooltip('Benchmark:N', title='Benchmark'),
                alt.Tooltip('Model:N', title='Model'),
                alt.Tooltip('Display_Score:N', title='Score'),
                alt.Tooltip('Score_Pct:Q', title='Normalized %', format='.1f')
            ]
        ).properties(height=360)
        st.altair_chart(apply_altair_dark_theme(h_chart), use_container_width=True)

    # Executive Decision Verdict & Strategic Conclusion
    m1_data = cmp_res["models_data"][0]
    m2_data = cmp_res["models_data"][1]
    cheapest_name = winners["cheapest"]
    ctx_winner_name = winners["largest_ctx"]
    intel_winner_name = winners["best_rated"]

    c1 = m1_data["monthly_cost"]
    c2 = m2_data["monthly_cost"]
    diff = abs(c1 - c2)
    pct_save = (diff / max(c1, c2, 1e-6)) * 100.0

    verdict_html = f"""
    <div class="nexus-verdict-box">
        <div class="nexus-verdict-header">
            <span class="nexus-verdict-tag">Executive Decision Verdict</span>
            <span class="nexus-verdict-title">{cheapest_name} vs {m2_data['version_name'] if cheapest_name == m1_data['version_name'] else m1_data['version_name']}</span>
        </div>
        <div class="nexus-verdict-body">
            <p style="margin-bottom: 8px;">
                <strong>Cost & Throughput Analysis:</strong> Deploying <strong>{cheapest_name}</strong> yields an estimated monthly saving of 
                <span style="color: #C8F169; font-weight: 700; font-family: var(--font-mono);">{sym}{diff:,.2f}</span> ({pct_save:.1f}% spend reduction) 
                at your projected monthly volume of {est_input_m:,.1f}M input / {est_output_m:,.1f}M output tokens.
            </p>
            <p style="margin-bottom: 8px;">
                <strong>Architectural Recommendation:</strong> For latency-sensitive user-facing agents, conversational interfaces, and batch extraction, 
                <strong>{cheapest_name}</strong> provides optimal return on investment. If your workload involves long-context codebases (over 100k tokens), multi-step reasoning, or autonomous tool execution, prioritize 
                <strong>{ctx_winner_name}</strong> with its {format_context(winners['largest_ctx_val'])} token context buffer.
            </p>
            <p style="margin-bottom: 0; color: #A3A89C; font-size: 0.82rem;">
                <strong>Summary Conclusion:</strong> Choose <strong>{cheapest_name}</strong> for cost leadership; choose <strong>{intel_winner_name}</strong> for highest verified developer satisfaction and accuracy benchmarks.
            </p>
        </div>
    </div>
    """
    render_html(verdict_html)


# ==============================================================================
# WORKSPACE 3: PERFORMANCE LEADERBOARDS (Artificial Analysis-style)
# ==============================================================================
BENCHMARK_DETAILS = {
    "SWE-bench Verified": {
        "domain": "Software Engineering & Autonomous Coding",
        "description": "Tests the model's ability to autonomously resolve real-world software engineering issues and pull requests sampled from popular open-source Python repositories (e.g. sympy, django, scikit-learn). Validates patch generation against hidden unit tests.",
        "metric": "Resolved Issue Rate (%)",
        "scale": "0% - 100% (Higher is better)",
        "why_it_matters": "The premier industry gold standard for agentic coding, automated bug fixing, and developer productivity tooling."
    },
    "MMLU-Pro": {
        "domain": "Advanced Collegiate Reasoning & STEM",
        "description": "An upgraded, harder variant of Massive Multitask Language Understanding spanning 14 collegiate-level disciplines (computer science, law, biology, physics, microeconomics, and mathematics) designed to challenge frontier LLMs.",
        "metric": "Multi-choice Accuracy (%)",
        "scale": "0% - 100% (Higher is better)",
        "why_it_matters": "Evaluates factual knowledge breadth, college-level domain expertise, and complex multi-step reasoning capabilities."
    },
    "Chatbot Arena Elo": {
        "domain": "Human Preference & Conversational Utility",
        "description": "Crowdsourced blind pairwise human evaluation from LMSYS Chatbot Arena where users submit arbitrary prompts and vote on side-by-side model completions without knowing the model identity.",
        "metric": "Bradley-Terry Elo Rating",
        "scale": "Typical frontier range: 1100 - 1450+ Elo",
        "why_it_matters": "Reflects real-world human satisfaction, helpfulness, formatting quality, and instruction adherence across unpredictable conversational prompts."
    },
    "GSM8K & MATH": {
        "domain": "Multi-Step Mathematical Problem Solving",
        "description": "Combines Grade School Math (GSM8K) word problems with challenging high-school and Olympiad-level competition mathematics (MATH) requiring symbolic reasoning and intermediate derivations.",
        "metric": "Exact Match Accuracy (%)",
        "scale": "0% - 100% (Higher is better)",
        "why_it_matters": "Validates logical consistency, quantitative deduction, and step-by-step chain-of-thought (CoT) reasoning accuracy."
    },
    "HumanEval": {
        "domain": "Functional Code Synthesis",
        "description": "OpenAI's benchmark evaluating Python function generation from docstrings and signatures, validating synthesized code against comprehensive hidden unit test suites.",
        "metric": "Pass@1 Correctness (%)",
        "scale": "0% - 100% (Higher is better)",
        "why_it_matters": "Measures core programming syntax mastery, algorithmic problem-solving, and functional correctness without execution errors."
    },
    "GPQA Diamond": {
        "domain": "Expert Scientific Research & Graduate STEM",
        "description": "Graduate-Level Google-Proof Q&A written and verified by domain experts (PhD holders in biology, physics, and organic chemistry) specifically designed to resist web search shortcuts.",
        "metric": "Accuracy (%)",
        "scale": "0% - 100% (Expert human baseline ~34%, frontier models >60%)",
        "why_it_matters": "Evaluates whether an AI model possesses genuine expert-level scientific intuition and can act as an autonomous research assistant."
    }
}


def page_leaderboard():
    render_header(
        "leaderboard",
        "Performance Leaderboards",
        "Ranked evaluations across verified benchmarks, cost-performance ratios, and context capabilities.",
        help_title="Leaderboard Workspace",
        help_desc="Explore ranked foundation models across verified academic evaluation suites, cost efficiency, and developer ratings."
    )
    render_recent_history_sidebar()

    b_suites = data.get_benchmark_suites()
    bench_dict = {b["name"]: b for b in b_suites}

    tab_score, tab_cost, tab_context, tab_rating, tab_all = st.tabs([
        "Benchmark Rankings", "Cost Efficiency", "Context Scaling", "Developer Ratings", "All Benchmarks Matrix"
    ])

    sym = curr_info["symbol"]

    with tab_score:
        l_col1, l_col2, l_col3 = st.columns([3, 2, 2])
        with l_col1:
            preferred = "SWE-bench Verified" if "SWE-bench Verified" in bench_dict else list(bench_dict.keys())[0]
            sel_suite = st.selectbox("Benchmark Suite", list(bench_dict.keys()), index=list(bench_dict.keys()).index(preferred), key="lead_suite_sel")
            suite_info = bench_dict[sel_suite]
        with l_col2:
            provider_list, _, _ = data.get_filter_options()
            lead_lab_filter = st.multiselect("Filter by Lab", provider_list, default=[], placeholder="All Labs", key="lead_lab_filter")
        with l_col3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            lead_cot_only = st.checkbox("Reasoning Only", value=False, key="lead_cot_filter")

        suite_meta = BENCHMARK_DETAILS.get(sel_suite, {
            "domain": suite_info.get("category", "General Evaluation"),
            "description": f"Verified evaluation suite measuring foundation model capability on {sel_suite}.",
            "metric": "Evaluation Score",
            "scale": f"0 - {suite_info.get('max_score', 100)}",
            "why_it_matters": "Industry benchmark evaluating production readiness."
        })

        render_html(f"""
        <div class="nexus-suite-banner">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
                <div>
                    <div style="font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.08em; color: #C8F169; font-weight: 700;">{suite_meta['domain']}</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #EDEFE9; margin-top: 2px;">{sel_suite}</div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <span class="nexus-badge badge-neutral">Metric: <strong style="color: #EDEFE9;">{suite_meta['metric']}</strong></span>
                    <span class="nexus-badge badge-neutral">Scale: <strong style="color: #EDEFE9;">{suite_meta['scale']}</strong></span>
                </div>
            </div>
            <div style="font-size: 0.85rem; color: #CCCFC7; line-height: 1.5; margin-top: 10px;">
                {suite_meta['description']}
            </div>
            <div style="font-size: 0.80rem; color: #A3A89C; margin-top: 8px; border-top: 1px solid #1C1F1A; padding-top: 6px;">
                <span style="color: #C8F169; font-weight: 600;">Why it matters:</span> {suite_meta['why_it_matters']}
            </div>
        </div>
        """)

        board_rows = data.get_leaderboard(
            metric="score",
            filters={"suite_id": suite_info["benchmark_id"], "labs": lead_lab_filter, "reasoning_only": lead_cot_only},
            currency=st.session_state.currency
        )
        if board_rows:
            df_board = pd.DataFrame(board_rows).drop(columns=["version_id", "Rank_Style"], errors='ignore')
            st.dataframe(
                df_board,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank": st.column_config.TextColumn("Rank", width="small"),
                    "Model": st.column_config.TextColumn("Model", width="medium"),
                    "Lab": st.column_config.TextColumn("Lab", width="medium"),
                    "Score": st.column_config.NumberColumn("Score", format="%.1f"),
                    "Relative Score": st.column_config.ProgressColumn("Relative Score (Top=100%)", min_value=0, max_value=100, format="%.0f%%"),
                    "Price": st.column_config.NumberColumn(f"Price ({sym}/1M)", format=f"{sym}%.3f"),
                }
            )

    with tab_cost:
        st.markdown("#### Lowest Token Ingestion Cost")
        cost_ranks = data.get_leaderboard(metric="cost", currency=st.session_state.currency)
        if cost_ranks:
            df_cost = pd.DataFrame(cost_ranks).drop(columns=["version_id", "Rank_Style"], errors='ignore')
            st.dataframe(
                df_cost,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank": st.column_config.TextColumn("Rank", width="small"),
                    "Model": st.column_config.TextColumn("Model", width="medium"),
                    "Lab": st.column_config.TextColumn("Lab", width="medium"),
                    "Input / 1M": st.column_config.NumberColumn(f"Input / 1M ({sym})", format=f"{sym}%.3f"),
                    "Output / 1M": st.column_config.NumberColumn(f"Output / 1M ({sym})", format=f"{sym}%.3f"),
                    "Context": st.column_config.NumberColumn("Context Window", format="%d"),
                }
            )

    with tab_context:
        st.markdown("#### Frontier Context Window Capacity")
        ctx_ranks = data.get_leaderboard(metric="context", currency=st.session_state.currency)
        if ctx_ranks:
            df_ctx = pd.DataFrame(ctx_ranks).drop(columns=["version_id", "Rank_Style"], errors='ignore')
            st.dataframe(
                df_ctx,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank": st.column_config.TextColumn("Rank", width="small"),
                    "Model": st.column_config.TextColumn("Model", width="medium"),
                    "Lab": st.column_config.TextColumn("Lab", width="medium"),
                    "Context Window": st.column_config.NumberColumn("Context Window", format="%d"),
                    "Max Output": st.column_config.NumberColumn("Max Output", format="%d"),
                    "Input / 1M": st.column_config.NumberColumn(f"Input / 1M ({sym})", format=f"{sym}%.3f"),
                }
            )

    with tab_rating:
        st.markdown("#### Highest Developer Satisfaction")
        rate_ranks = data.get_leaderboard(metric="rating", currency=st.session_state.currency)
        if rate_ranks:
            df_rate = pd.DataFrame(rate_ranks).drop(columns=["version_id", "Rank_Style"], errors='ignore')
            st.dataframe(
                df_rate,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank": st.column_config.TextColumn("Rank", width="small"),
                    "Model": st.column_config.TextColumn("Model", width="medium"),
                    "Lab": st.column_config.TextColumn("Lab", width="medium"),
                    "Rating": st.column_config.NumberColumn("Rating", format="%.2f"),
                    "Input / 1M": st.column_config.NumberColumn(f"Input / 1M ({sym})", format=f"{sym}%.3f"),
                    "Context": st.column_config.NumberColumn("Context Window", format="%d"),
                }
            )

    with tab_all:
        st.markdown("#### Frontier Multi-Suite Benchmark Comparison Matrix")
        st.caption("Cross-evaluation matrix comparing all models against every verified evaluation domain.")

        with st.expander("Benchmark Suites Reference Dossier (What Each Benchmark Refers To)", expanded=False):
            b_cols = st.columns(2)
            for idx, (b_name, b_info) in enumerate(BENCHMARK_DETAILS.items()):
                with b_cols[idx % 2]:
                    render_html(f"""
                    <div style="background: #131512; border: 1px solid #242722; border-radius: 6px; padding: 12px 14px; margin-bottom: 10px;">
                        <div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: #C8F169; font-weight: 700;">{b_info['domain']}</div>
                        <div style="font-size: 0.95rem; font-weight: 700; color: #EDEFE9; margin-top: 1px;">{b_name}</div>
                        <div style="font-size: 0.80rem; color: #CCCFC7; margin-top: 6px; line-height: 1.4;">{b_info['description']}</div>
                        <div style="display: flex; gap: 6px; margin-top: 8px;">
                            <span class="nexus-badge badge-neutral" style="font-size: 0.70rem;">Metric: {b_info['metric']}</span>
                            <span class="nexus-badge badge-neutral" style="font-size: 0.70rem;">Scale: {b_info['scale']}</span>
                        </div>
                    </div>
                    """)

        al_c1, al_c2, al_c3 = st.columns([2.5, 1.8, 1.8])
        with al_c1:
            provider_list, _, _ = data.get_filter_options()
            all_bench_labs = st.multiselect("Filter by Lab", provider_list, default=[], placeholder="All Labs", key="all_bench_lab_filter")
        with al_c2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            all_bench_cot = st.checkbox("Reasoning Models Only", value=False, key="all_bench_cot_filter")
        with al_c3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            all_bench_eval_only = st.checkbox("Evaluated Models Only", value=True, key="all_bench_eval_only_chk", help="Filter out models with no recorded evaluations")

        matrix_rows = data.get_all_benchmarks_matrix(
            filters={"labs": all_bench_labs, "reasoning_only": all_bench_cot},
            currency=st.session_state.currency
        )
        if all_bench_eval_only:
            matrix_rows = [r for r in matrix_rows if r.get("Average Score", 0) > 0]

        if matrix_rows:
            df_mat = pd.DataFrame(matrix_rows)
            suites_cols = [c for c in df_mat.columns if c not in ("version_id", "Model", "Lab", "Average Score", "Input / 1M", "Rating")]

            def _fmt_score(x):
                try:
                    if x is None or str(x) == "None":
                        return "—"
                    v = float(x)
                    return f"{v:.1f}" if v > 0 else "—"
                except Exception:
                    return "—"

            def _score_pct(x):
                """Return 0-100 float for heat fill."""
                try:
                    if x is None or str(x) == "None":
                        return 0
                    v = float(x)
                    # Chatbot Arena Elo is 1000-1600 range; normalise others to 0-100
                    if v > 200:
                        return min(100, round((v - 1000) / 6.0, 1))
                    return min(100, max(0, v))
                except Exception:
                    return 0

            # Build header
            th_suites = "".join([
                f'<th class="num" style="font-size:0.70rem;" title="{sc}">{sc[:10]}…</th>' if len(sc) > 11
                else f'<th class="num" style="font-size:0.70rem;">{sc}</th>'
                for sc in suites_cols
            ])
            matrix_header = f"""
            <tr>
                <th style="width:38px;">#</th>
                <th>Model</th>
                <th>Lab</th>
                <th class="num">Avg</th>
                <th class="num">Input/1M</th>
                <th class="num">★ Rtg</th>
                {th_suites}
            </tr>"""

            matrix_body = ""
            for idx, r in enumerate(matrix_rows):
                medal = ["🥇","🥈","🥉"][idx] if idx < 3 else f"<span style='color:#6B6E66;font-family:var(--font-mono);font-size:0.78rem;'>#{idx+1}</span>"
                avg_sc = r.get("Average Score", 0) or 0
                avg_disp = f"{avg_sc:.1f}" if avg_sc > 0 else "—"
                in_p = r.get("Input / 1M", 0) or 0
                in_disp = f"{sym}{in_p:.3f}" if in_p > 0 else "Free"
                rtg = r.get("Rating", 0) or 0
                rtg_disp = f"★ {rtg:.2f}" if rtg > 0 else "—"
                vid = r.get("version_id", 0)

                suite_tds = ""
                for sc in suites_cols:
                    raw_val = r.get(sc)
                    disp = _fmt_score(raw_val)
                    pct = _score_pct(raw_val)
                    if disp == "—":
                        suite_tds += f'<td class="num" style="color:#3D4139;font-family:var(--font-mono);font-size:0.78rem;">—</td>'
                    else:
                        # heat fill: lime at high score
                        heat = max(0, min(1, pct / 100.0))
                        r_col = int(200 * (1 - heat) + 54 * heat)
                        g_col = int(241 * heat + 95 * (1 - heat))
                        b_col = int(105 * heat + 55 * (1 - heat))
                        txt_col = "#0B0C0A" if heat > 0.6 else "#CCCFC7"
                        suite_tds += f'<td class="num" style="font-family:var(--font-mono);font-size:0.80rem;background:rgba({r_col},{g_col},{b_col},0.18);color:{txt_col};">{disp}</td>'

                matrix_body += f"""
                <tr data-vid="{vid}">
                    <td style="width:38px;">{medal}</td>
                    <td style="font-weight:600;color:#EDEFE9;font-size:0.86rem;">{r.get('Model','')}</td>
                    <td><span class="nexus-badge badge-neutral" style="font-size:0.72rem;">{r.get('Lab','')}</span></td>
                    <td class="num" style="font-weight:700;color:#C8F169;font-family:var(--font-mono);font-size:0.84rem;">{avg_disp}</td>
                    <td class="num" style="color:#A3A89C;font-family:var(--font-mono);font-size:0.80rem;">{in_disp}</td>
                    <td class="num" style="color:#F5B94A;font-size:0.80rem;">{rtg_disp}</td>
                    {suite_tds}
                </tr>"""

            render_html(f"""
            <div class="nexus-table-container" style="overflow-x:auto;max-height:580px;">
                <table class="nexus-table" style="min-width:900px;">
                    <thead>{matrix_header}</thead>
                    <tbody>{matrix_body}</tbody>
                </table>
            </div>
            """)

            # Quick profile jump
            model_names_mat = [r.get("Model","") for r in matrix_rows]
            mc1, mc2 = st.columns([4, 2])
            with mc1:
                sel_mat_name = st.selectbox("Jump to Model Profile:", model_names_mat, key="matrix_jump_sel", label_visibility="collapsed")
            with mc2:
                if st.button("Open Deep Profile →", key="matrix_open_profile_btn", type="primary", use_container_width=True):
                    sel_mat_vid = next((r["version_id"] for r in matrix_rows if r.get("Model") == sel_mat_name), None)
                    if sel_mat_vid:
                        st.session_state.selected_models = sel_mat_vid
                        st.switch_page(nav_pages["profile"])
        else:
            st.info("No models match the selected benchmark filters.")


# ==============================================================================
# WORKSPACE 4: DEEP MODEL PROFILE
# ==============================================================================
def page_profile():
    models_dir = data.get_model_selection_list()
    names_map = {f"{m['version_name']} ({m['provider_name']})": m['version_id'] for m in models_dir}

    default_idx = 0
    for idx, (label, vid) in enumerate(names_map.items()):
        if vid == st.session_state.selected_models:
            default_idx = idx
            break

    render_header(
        "profile",
        "Deep Model Profile",
        "Exhaustive architectural specifications, enterprise workload fit, community audits, and production logs.",
        help_title="Profile Workspace",
        help_desc="Examine complete model technical specifications, historical pricing changes, API gateway code snippets, and error reports."
    )
    render_recent_history_sidebar()

    m_sel_col1, _ = st.columns([4, 2])
    with m_sel_col1:
        profile_choice = st.selectbox("Target Model to Audit:", list(names_map.keys()), index=default_idx, key="prof_target_sel")
        target_vid = names_map[profile_choice]
        st.session_state.selected_models = target_vid

    # Fetch deep profile data via Data Layer
    model_detail = data.get_model(target_vid, currency=st.session_state.currency)
    if not model_detail:
        st.error("Model specifications could not be loaded.")
        return

    model_data = model_detail["profile"]
    sym = model_detail["currency_symbol"]

    # Enqueue to Recent Views Circular Queue DSA
    data.add_recent_view(st.session_state.session_id, target_vid, model_data.get("version_name", "Model"))

    model_country = format_country(model_data.get('headquarters_country'))
    m_in_price = f"{sym}{model_detail['input_price_converted']:.3f}" if model_detail['input_price_converted'] > 0 else "Free"

    # Header Row
    render_html(f"""
    <div style="background: #131512; border: 1px solid #242722; border-radius: 8px; padding: 18px 22px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="font-size: 1.35rem; font-weight: 700; color: #EDEFE9; letter-spacing: -0.02em;">{model_data.get('version_name', '')}</div>
                <div style="font-size: 0.85rem; color: #A3A89C; margin-top: 2px;">{model_data.get('provider_name', '')} ({model_country}) · Family: {model_data.get('family_name', '')} · Released: {str(model_data.get('release_date', ''))[:10]}</div>
            </div>
            <div style="display: flex; gap: 6px;">
                <span class="nexus-badge badge-neutral">{m_in_price} / 1M Input</span>
                <span class="nexus-badge badge-neutral">{format_context(model_data.get('context_length'))} Context</span>
                <span class="nexus-badge badge-neutral">{str(model_data.get('input_modalities', 'Text')).upper()}</span>
            </div>
        </div>
        <p style="color: #CCCFC7; margin-top: 10px; font-size: 0.88rem; line-height: 1.5; margin-bottom: 0;">{model_data.get('description', '')}</p>
    </div>
    """)

    tab_overview, tab_pricing, tab_benchmarks, tab_usecases, tab_reviews, tab_incidents = st.tabs([
        "Overview", "Pricing", "Benchmarks", "Use-Case Fit", "Reviews", "Incidents"
    ])

    with tab_overview:
        caps = model_detail["capabilities"]
        if caps:
            st.markdown("#### Operational Capabilities")
            cap_cards = "".join([
                f"""<div class="nexus-spec-card">
                    <div class="nexus-spec-card-label">{c['name']}</div>
                    <div class="nexus-spec-card-val" style="color: #C8F169;">{c['proficiency'].title()}</div>
                    <div style="font-size: 0.78rem; color: #A3A89C; margin-top: 4px;">{c.get('description', 'Verified in production workloads.')}</div>
                </div>"""
                for c in caps
            ])
            render_html(f'<div class="nexus-spec-grid">{cap_cards}</div>')

        api_data = model_detail["api_gateway"]
        if api_data:
            st.markdown("#### API Gateway Specification")
            st.caption(f"Base Endpoint: `{api_data['base_url']}` | Auth: {api_data['auth_type']} | Rate Limit: {api_data['rate_limit_rpm']} RPM")
            snippet = f"""import requests

response = requests.post(
    "{api_data['base_url']}/chat/completions",
    headers={{"Authorization": "Bearer YOUR_API_KEY", "Content-Type": "application/json"}},
    json={{"model": "{model_data.get('external_id', '')}", "messages": [{{"role": "user", "content": "Explain quantum cryptography."}}]}}
)
print(response.json())"""
            st.code(snippet, language="python")

    with tab_pricing:
        st.markdown(f"#### Pricing Ledger ({curr_info['name']})")
        if model_detail["pricing_history"]:
            ph_rows_html = ""
            for r in model_detail["pricing_history"]:
                eff_date = str(r.get("Effective Date", ""))[:10]
                in_p = float(r.get("Input / 1M", 0))
                out_p = float(r.get("Output / 1M", 0))
                in_usd = float(r.get("Input (USD Base)", 0))
                out_usd = float(r.get("Output (USD Base)", 0))
                ph_rows_html += f"""
                <tr>
                    <td style="color: #A3A89C; font-family: var(--font-mono);">{eff_date}</td>
                    <td class="num" style="color: #C8F169; font-weight: 600;">{sym}{in_p:.4f}</td>
                    <td class="num">{sym}{out_p:.4f}</td>
                    <td class="num" style="color: #A3A89C;">${in_usd:.4f}</td>
                    <td class="num" style="color: #A3A89C;">${out_usd:.4f}</td>
                </tr>
                """
            render_html(f"""
            <div class="nexus-table-container">
                <table class="nexus-table">
                    <thead>
                        <tr>
                            <th>Effective Date</th>
                            <th class="num">Input / 1M ({sym})</th>
                            <th class="num">Output / 1M ({sym})</th>
                            <th class="num">Input Base ($ USD)</th>
                            <th class="num">Output Base ($ USD)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {ph_rows_html}
                    </tbody>
                </table>
            </div>
            """)
        else:
            st.info("No historical pricing records found.")

    with tab_benchmarks:
        st.markdown("#### Verified Benchmark Evaluations")
        bench_ranks = data.get_model_benchmark_ranks(target_vid)
        if bench_ranks:
            df_br = pd.DataFrame(bench_ranks)

            # Horizontal bar chart of this model's scores (one bar per suite, shared chart theme)
            b_chart = alt.Chart(df_br).mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3).encode(
                y=alt.Y('suite_name:N', sort='-x', title=None, axis=alt.Axis(labelColor='#CCCFC7', labelFontSize=12)),
                x=alt.X('pct_score:Q', title='Score (% of Suite Max)', scale=alt.Scale(domain=[0, 100])),
                color=alt.value('#C8F169'),
                tooltip=[
                    alt.Tooltip('suite_name:N', title='Benchmark Suite'),
                    alt.Tooltip('display_score:N', title='Score'),
                    alt.Tooltip('pct_score:Q', title='Normalized %', format='.1f'),
                    alt.Tooltip('rank_str:N', title='Catalog Rank')
                ]
            ).properties(height=260)
            st.altair_chart(apply_altair_dark_theme(b_chart), use_container_width=True)

            # Compact list/grid: suite name, score, rank among all models
            st.markdown("##### Performance by Suite & Relative Rank")
            rank_cards = "".join([
                f"""<div class="nexus-spec-card">
                    <div class="nexus-spec-card-label" title="{b.get('category', 'Benchmark')}">{b['suite_name']}</div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 4px;">
                        <span class="nexus-spec-card-val" style="color: #C8F169;">{b['display_score']}</span>
                        <span class="nexus-badge badge-neutral" style="font-family: var(--font-mono); font-size: 0.76rem;">{b['rank_str']}</span>
                    </div>
                </div>"""
                for b in bench_ranks
            ])
            render_html(f'<div class="nexus-spec-grid">{rank_cards}</div>')

            # View in Leaderboard button
            st.write("")
            b_c1, b_c2 = st.columns([4, 1.6])
            with b_c2:
                if st.button("View in Leaderboard →", key="prof_view_in_leaderboard_btn", type="primary", use_container_width=True):
                    st.switch_page(nav_pages["leaderboard"])
        else:
            st.info("No quantitative benchmark evaluation records registered for this model.")

    with tab_usecases:
        st.markdown("#### Enterprise Workload Suitability")
        workloads = model_detail["use_cases"]
        if workloads:
            uc_cards = "".join([
                f"""<div class="nexus-spec-card">
                    <div class="nexus-spec-card-label">{w.get('task_name', 'Task')}</div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 4px;">
                        <span class="nexus-spec-card-val" style="color: #C8F169;">{float(w.get('suitability_score') or 0):.2f} / 1.00 ({int(float(w.get('suitability_score') or 0) * 100)}%)</span>
                        <span class="nexus-badge badge-neutral">{w.get('cost_efficiency_tier', 'Standard').title()}</span>
                    </div>
                    <div style="font-size: 0.78rem; color: #A3A89C; margin-top: 6px;">{w.get('notes', 'Verified for enterprise workloads.')}</div>
                </div>"""
                for w in workloads
            ])
            render_html(f'<div class="nexus-spec-grid">{uc_cards}</div>')
        else:
            st.info("No use-case assessments available.")

    with tab_reviews:
        st.markdown("#### Verified Developer Reviews")
        model_reviews = model_detail["reviews"]
        if model_reviews:
            rev_rows_html = ""
            for rev in model_reviews:
                score = int(rev.get("rating", 5))
                stars_str = "★" * score + "☆" * (5 - score)
                rev_rows_html += f"""
                <tr>
                    <td style="color: #C8F169; font-weight: 700; width: 110px;">{stars_str}</td>
                    <td style="font-weight: 600; color: #EDEFE9; width: 200px;">{rev.get('title', '')}</td>
                    <td style="width: 150px; color: #A3A89C; font-size: 0.82rem;">{rev.get('reviewer_name', '')}</td>
                    <td style="color: #CCCFC7; line-height: 1.4;">{rev.get('review_text', '')}</td>
                    <td class="num" style="width: 110px; font-size: 0.78rem; color: #A3A89C;">{str(rev.get('created_at', ''))[:10]}</td>
                </tr>
                """
            render_html(f"""
            <div class="nexus-table-container">
                <table class="nexus-table">
                    <thead>
                        <tr>
                            <th style="width: 110px;">Rating</th>
                            <th style="width: 200px;">Title</th>
                            <th style="width: 150px;">Reviewer</th>
                            <th>Observations</th>
                            <th class="num" style="width: 110px;">Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rev_rows_html}
                    </tbody>
                </table>
            </div>
            """)
        else:
            st.info("No developer reviews submitted for this model yet.")

        with st.expander("Submit a Production Review"):
            with st.form(f"review_form_{target_vid}"):
                rf1, rf2 = st.columns(2)
                with rf1:
                    r_name = st.text_input("Reviewer Name / Organization:", value="AI Systems Engineer")
                    r_stars = st.slider("Rating Score (1-5):", 1, 5, 5)
                with rf2:
                    r_title = st.text_input("Review Title:", placeholder="e.g. Robust throughput and low latency")
                    r_body = st.text_area("Review Observations:")
                sub_btn = st.form_submit_button("Publish Developer Review", type="primary")
                if sub_btn:
                    if r_title and r_body:
                        data.submit_review(target_vid, r_name, r_stars, r_title, r_body)
                        st.success("Review published.")
                        st.rerun()
                    else:
                        st.warning("Please provide both a title and review observations.")

    with tab_incidents:
        st.markdown("#### Production Incidents Ledger")
        incidents = model_detail["incidents"]
        if incidents:
            inc_rows_html = ""
            for inc in incidents:
                sev = str(inc.get("severity", "medium")).lower()
                if sev in ("high", "critical"):
                    sev_badge = '<span class="nexus-badge badge-high">HIGH</span>'
                elif sev == "medium":
                    sev_badge = '<span class="nexus-badge badge-med">MEDIUM</span>'
                else:
                    sev_badge = '<span class="nexus-badge badge-low">LOW</span>'

                mode = str(inc.get("error_type", "hallucination")).title()
                time_str = str(inc.get("created_at", ""))[:19]
                desc_str = str(inc.get("description", ""))

                inc_rows_html += f"""
                <tr>
                    <td style="width: 100px;">{sev_badge}</td>
                    <td style="width: 140px;"><span class="nexus-badge badge-neutral">{mode}</span></td>
                    <td style="color: #CCCFC7; line-height: 1.4;">{desc_str}</td>
                    <td style="width: 140px; color: #A3A89C; font-size: 0.82rem;">{inc.get('reporter_name', 'Auditor')}</td>
                    <td class="num" style="width: 160px; font-size: 0.78rem; color: #A3A89C;">{time_str}</td>
                </tr>
                """

            render_html(f"""
            <div class="nexus-table-container">
                <table class="nexus-table">
                    <thead>
                        <tr>
                            <th style="width: 100px;">Severity</th>
                            <th style="width: 140px;">Failure Mode</th>
                            <th>Description</th>
                            <th style="width: 140px;">Reporter</th>
                            <th class="num" style="width: 160px;">Logged At</th>
                        </tr>
                    </thead>
                    <tbody>
                        {inc_rows_html}
                    </tbody>
                </table>
            </div>
            """)
        else:
            st.success("Zero active incidents recorded for this model.")

        with st.expander("Report Incident or Hallucination"):
            with st.form(f"incident_form_{target_vid}"):
                bf1, bf2 = st.columns(2)
                with bf1:
                    err_t = st.selectbox("Failure Mode:", ["hallucination", "refusal", "timeout", "formatting", "incorrect"])
                    err_s = st.selectbox("Severity Level:", ["low", "medium", "high", "critical"])
                with bf2:
                    err_d = st.text_area("Incident Description:", placeholder="Detail unexpected refusal or incorrect output...")
                inc_btn = st.form_submit_button("Log Incident Report", type="primary")
                if inc_btn:
                    if err_d:
                        data.log_incident(target_vid, "Auditor", err_t, err_s, err_d)
                        st.success("Incident registered.")
                        st.rerun()
                    else:
                        st.warning("Please provide incident details.")


# ==============================================================================
# WORKSPACE 5: SMART COST & TASK MATCHER
# ==============================================================================
def page_matcher():
    render_header(
        "matcher",
        "Smart Cost & Task Matcher",
        "Constraint-based model recommendation engine matching enterprise workload requirements against token budget caps.",
        help_title="Matcher Workspace",
        help_desc="Define your application workload, budget ceiling, and minimum memory context to receive optimized model recommendations."
    )
    render_recent_history_sidebar()

    _, _, uc_options = data.get_filter_options()

    # Inputs in ONE single row per spec
    r1, r2, r3, r4 = st.columns([3, 2, 2, 1.5])
    with r1:
        task_needed = st.selectbox("Workload:", uc_options, key="matcher_workload_sel")
    with r2:
        max_b_slider = float(round(20.0 * curr_info["rate"], 1))
        def_b_slider = float(round(5.0 * curr_info["rate"], 1))
        budget_cap = st.slider(f"Max Budget ({curr_info['symbol']}/1M)", 0.0, max_b_slider, def_b_slider, 0.5, key="matcher_budget_slider")
    with r3:
        context_req = st.selectbox(
            "Min Context:",
            [8000, 32000, 128000, 200000, 1000000],
            index=1,
            format_func=lambda x: f"{format_context(x)} Tokens",
            key="matcher_context_sel"
        )
    with r4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        run_match = st.button("Calculate Optimal", key="matcher_run_btn", type="primary", use_container_width=True)

    if run_match:
        st.session_state.matcher_results = data.get_recommendations(
            use_case=task_needed,
            budget_cap=budget_cap,
            min_context=context_req,
            currency=st.session_state.currency
        )

    # Render persisted matcher results
    if st.session_state.matcher_results is not None:
        matches = st.session_state.matcher_results
        sym = curr_info["symbol"]
        if matches:
            best_m = matches[0]
            st.markdown(f"<span style='color: #C8F169; font-weight: 600;'>Optimal Match: {best_m['Model']}</span> <span class='nexus-badge badge-lime' style='margin-left: 8px;'>Best Value</span>", unsafe_allow_html=True)
            # Render Result Cards instead of a table
            for idx, m in enumerate(matches):
                in_cost = m["Input / 1M"]
                out_cost = m["Output / 1M"]
                suit = float(m["Suitability Score"])
                suit_pct = min(100, max(0, int(suit * 100)))
                m_ctx = format_context(m["Context"])
                is_best = (idx == 0)
                best_cls = "best-card" if is_best else ""
                best_tag = '<span class="nexus-badge badge-lime">Optimal Recommendation</span>' if is_best else ""

                # Monthly volume simulation (10M In, 2M Out)
                est_monthly = (10.0 * in_cost) + (2.0 * out_cost)
                budget_monthly = (10.0 * budget_cap) + (2.0 * budget_cap * 1.5)
                savings_pct = max(0, round(((budget_monthly - est_monthly) / max(budget_monthly, 0.01)) * 100))
                savings_badge = f'<span class="nexus-savings-badge">-{savings_pct}% vs Budget Ceiling</span>' if savings_pct > 0 else ""

                card_html = f"""
                <div class="nexus-match-card {best_cls}">
                    <div class="nexus-match-header">
                        <div>
                            <div class="nexus-match-title">{m['Model']} {best_tag}</div>
                            <div style="font-size: 0.82rem; color: #A3A89C; margin-top: 2px;">{m['Provider']} · Context: {m_ctx}</div>
                        </div>
                        <div style="text-align: right;">
                            <div class="nexus-match-cost">{sym}{est_monthly:,.2f}<span style="font-size: 0.72rem; color: #6B6E66; font-family: var(--font-sans); font-weight: normal;"> / mo</span></div>
                            <div style="font-size: 0.72rem; color: #A3A89C; font-family: var(--font-mono);">{sym}{in_cost:.3f} In / {sym}{out_cost:.3f} Out</div>
                        </div>
                    </div>
                    <div style="margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.76rem; color: #A3A89C; margin-bottom: 4px;">
                            <span>Task Suitability Alignment</span>
                            <span style="color: #EDEFE9; font-weight: 600;">{suit:.2f} / 1.00 ({suit_pct}%)</span>
                        </div>
                        <div style="background: #1C1F1A; border: 1px solid #242722; border-radius: 4px; height: 6px; width: 100%;">
                            <div style="background: #C8F169; width: {suit_pct}%; height: 6px; border-radius: 4px;"></div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                        <div>{savings_badge}</div>
                    </div>
                </div>
                """
                render_html(card_html)
                m_c1, m_c2 = st.columns([4, 1.4])
                with m_c2:
                    if st.button("Deep Profile →", key=f"match_prof_btn_{m['version_id']}_{idx}", use_container_width=True):
                        st.session_state.selected_models = m["version_id"]
                        st.switch_page(nav_pages["profile"])

            # Match Verdict & Procurement Takeaway
            in_cost = best_m["Input / 1M"]
            suit = float(best_m["Suitability Score"])
            m_ctx = format_context(best_m["Context"])
            render_html(f"""
            <div class="nexus-verdict-box">
                <div class="nexus-verdict-header">
                    <span class="nexus-verdict-tag">Procurement Verdict</span>
                    <span class="nexus-verdict-title">Optimal Enterprise Choice: {best_m['Model']} ({best_m['Provider']})</span>
                </div>
                <div class="nexus-verdict-body">
                    <p style="margin-bottom: 6px;">
                        <strong>Workload Alignment:</strong> For <strong>{task_needed}</strong>, <strong>{best_m['Model']}</strong> achieves the highest suitability score (<span style="color: #C8F169; font-weight: 700;">{suit:.2f} / 1.00 ({int(suit * 100)}%)</span>) while maintaining a unit cost of <span style="color: #C8F169; font-weight: 700; font-family: var(--font-mono);">{sym}{in_cost:.3f}/1M tokens</span>, staying well below your budget ceiling of {sym}{budget_cap:.2f}/1M.
                    </p>
                    <p style="margin-bottom: 0; color: #A3A89C; font-size: 0.82rem;">
                        <strong>Operational Takeaway:</strong> With {m_ctx} context capacity, this model accommodates typical prompt payloads without truncation. Recommend provisioning via its dedicated API gateway endpoint with fallback routing enabled.
                    </p>
                </div>
            </div>
            """)
        else:
            st.warning("No models found within this price range and context length. Loosen your budget cap.")


# ==============================================================================
# WORKSPACE 6: DEVELOPER REVIEWS & AUDIT
# ==============================================================================
def page_reviews():
    render_header(
        "reviews",
        "Developer Reviews & Audit",
        "Crowdsourced engineering feedback, developer satisfaction audits, and production incident ledger.",
        help_title="Audit & Incident Ledger",
        help_desc="Track production hallucinations, API timeouts, and model refusals. Submit peer reviews and report operational defects."
    )
    render_recent_history_sidebar()

    tab_ledger, tab_revs, tab_submit = st.tabs(["Incident Ledger", "Community Reviews", "Submit Audit / Report"])

    with tab_ledger:
        # Filter controls for incident ledger (Status removed per spec)
        if1, if2 = st.columns([2, 3])
        with if1:
            sel_sev = st.selectbox("Severity Filter:", ["All", "High", "Medium", "Low"], key="inc_filter_sev")
        with if2:
            sel_mod = st.text_input("Filter by Model Name:", placeholder="e.g. Gemini, Claude, Llama...", key="inc_filter_mod")

        filter_dict = {
            "severity": "" if sel_sev == "All" else sel_sev.lower(),
            "model": sel_mod.strip()
        }
        all_incidents = data.get_incidents(filter_dict)
        if all_incidents:
            inc_rows_html = ""
            for inc in all_incidents:
                sev = str(inc.get("Severity", "medium")).lower()
                if sev in ("high", "critical"):
                    sev_badge = '<span class="nexus-badge badge-high">HIGH</span>'
                elif sev == "medium":
                    sev_badge = '<span class="nexus-badge badge-med">MEDIUM</span>'
                else:
                    sev_badge = '<span class="nexus-badge badge-low">LOW</span>'

                mode = str(inc.get("Failure Mode", "Unknown")).title()
                time_str = str(inc.get("Time", ""))[:19]
                desc_str = str(inc.get("Description", ""))
                model_str = str(inc.get("Model", ""))

                inc_rows_html += f"""
                <tr>
                    <td style="width: 100px;">{sev_badge}</td>
                    <td style="font-weight: 600; color: #EDEFE9; width: 180px;">{model_str}</td>
                    <td style="width: 140px;"><span class="nexus-badge badge-neutral">{mode}</span></td>
                    <td style="color: #CCCFC7; line-height: 1.4;">{desc_str}</td>
                    <td class="num" style="width: 160px; font-size: 0.78rem; color: #A3A89C;">{time_str}</td>
                </tr>
                """

            render_html(f"""
            <div class="nexus-table-container">
                <table class="nexus-table">
                    <thead>
                        <tr>
                            <th style="width: 100px;">Severity</th>
                            <th style="width: 180px;">Model</th>
                            <th style="width: 140px;">Failure Mode</th>
                            <th>Incident Description</th>
                            <th class="num" style="width: 160px;">Logged At</th>
                        </tr>
                    </thead>
                    <tbody>
                        {inc_rows_html}
                    </tbody>
                </table>
            </div>
            """)
        else:
            st.info("Zero active production incidents matching criteria.")

    with tab_revs:
        all_reviews = data.get_reviews()
        if all_reviews:
            rev_rows_html = ""
            for rev in all_reviews:
                score = int(rev.get("Rating", 5))
                stars_str = "★" * score + "☆" * (5 - score)
                rev_rows_html += f"""
                <tr>
                    <td style="font-weight: 600; color: #EDEFE9; width: 170px;">{rev.get('Model', '')}</td>
                    <td style="color: #C8F169; font-weight: 700; width: 110px;">{stars_str}</td>
                    <td style="width: 150px; color: #A3A89C; font-size: 0.82rem;">{rev.get('Reviewer', '')}</td>
                    <td style="font-weight: 500; color: #EDEFE9; width: 220px;">{rev.get('Title', '')}</td>
                    <td style="color: #CCCFC7; line-height: 1.4;">{rev.get('Observations', '')}</td>
                    <td class="num" style="width: 110px; font-size: 0.78rem; color: #A3A89C;">{str(rev.get('Date', ''))[:10]}</td>
                </tr>
                """
            render_html(f"""
            <div class="nexus-table-container">
                <table class="nexus-table">
                    <thead>
                        <tr>
                            <th style="width: 170px;">Model</th>
                            <th style="width: 110px;">Rating</th>
                            <th style="width: 150px;">Reviewer</th>
                            <th style="width: 220px;">Headline</th>
                            <th>Observations</th>
                            <th class="num" style="width: 110px;">Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rev_rows_html}
                    </tbody>
                </table>
            </div>
            """)
        else:
            st.info("No reviews logged yet.")

    with tab_submit:
        models_list = data.get_model_selection_list()
        m_dict = {m["version_name"]: m["version_id"] for m in models_list}
        s1, s2 = st.columns(2)
        with s1:
            st.markdown("#### Submit Developer Review")
            with st.form("global_review_form"):
                target_m = st.selectbox("Target Model:", list(m_dict.keys()), key="global_sub_rev_m")
                rev_user = st.text_input("Reviewer Name:", value="AI Systems Engineer")
                rev_score = st.slider("Rating (1-5):", 1, 5, 5)
                rev_head = st.text_input("Title:", placeholder="e.g. Robust throughput and low latency")
                rev_det = st.text_area("Details:")
                pub_btn = st.form_submit_button("Publish Review", type="primary")
                if pub_btn:
                    if rev_head and rev_det:
                        data.submit_review(m_dict[target_m], rev_user, rev_score, rev_head, rev_det)
                        st.success("Review published.")
                        st.rerun()
                    else:
                        st.warning("Please provide title and details.")
        with s2:
            st.markdown("#### Report Production Incident")
            with st.form("global_incident_form"):
                err_m = st.selectbox("Affected Model:", list(m_dict.keys()), key="global_bug_m")
                err_tp = st.selectbox("Failure Mode:", ["hallucination", "refusal", "timeout", "formatting", "incorrect"])
                err_sv = st.selectbox("Severity Level:", ["low", "medium", "high", "critical"])
                err_dsc = st.text_area("Incident Summary:", placeholder="Describe the failure...")
                log_btn = st.form_submit_button("Log Incident", type="primary")
                if log_btn:
                    if err_dsc:
                        data.log_incident(m_dict[err_m], "Auditor", err_tp, err_sv, err_dsc)
                        st.success("Incident logged.")
                        st.rerun()
                    else:
                        st.warning("Please provide description.")


# ==============================================================================
# WORKSPACE 7: ENTERPRISE ANALYTICS & REPORTS
# ==============================================================================
def page_analytics():
    render_header(
        "analytics",
        "Enterprise Analytics & Reports",
        "Dynamic multi-dimensional intelligence, cost telemetry, risk modeling, and catalog distributions.",
        help_title="Analytics Workspace",
        help_desc="Configure custom analytical reports, review automated KPI telemetry, inspect visual charts, and export executive summaries."
    )
    render_recent_history_sidebar()

    # 17-Table Schema Storage Distribution (Expander)
    with st.expander("Relational Database Storage Distribution (17 Tables)", expanded=False):
        counts_map = data.get_schema_counts()
        df_counts = pd.DataFrame(list(counts_map.items()), columns=["Table", "Rows"])
        dist_chart = alt.Chart(df_counts).mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3).encode(
            x=alt.X('Rows:Q', title='Record Count'),
            y=alt.Y('Table:N', sort='-x', title=None, axis=alt.Axis(labelColor='#CCCFC7')),
            color=alt.value('#C8F169')
        ).properties(height=340)
        st.altair_chart(apply_altair_dark_theme(dist_chart), use_container_width=True)

    # --------------------------------------------------------------------------
    # REPORT BUILDER BAR
    # --------------------------------------------------------------------------
    st.markdown("#### Enterprise Report Builder")
    provider_opts, _, _ = data.get_filter_options()
    report_list = list(data.ANALYTICS_REPORTS.keys())

    rb1, rb2, rb3 = st.columns([3, 2, 1.8])
    with rb1:
        sel_report = st.selectbox(
            "Select Analytical Report Suite:",
            report_list,
            index=0,
            help="Choose from 10 enterprise intelligence dimensions.",
            key="analytics_report_sel"
        )
    with rb2:
        an_labs = st.multiselect(
            "Filter Labs / Vendors:",
            provider_opts,
            default=[],
            placeholder="All AI Labs",
            help="Filter analytical cohort by foundation provider.",
            key="analytics_labs_filter"
        )
    with rb3:
        an_group = st.selectbox(
            "Group Dimension:",
            ["Lab", "Country", "Capability", "Price Tier"],
            index=0,
            key="analytics_group_by_sel"
        )

    # Presets Row (Save / Load Report Presets in session_state)
    ps_c1, ps_c2, ps_c3, ps_c4 = st.columns([2, 1.2, 1.2, 2.5])
    with ps_c1:
        preset_name = st.text_input("Preset Name:", value=f"{sel_report[:12]} Filter", key="analytics_preset_name_input", label_visibility="collapsed")
    with ps_c2:
        if st.button("Save Preset", key="analytics_save_preset_btn", use_container_width=True):
            st.session_state.saved_analytics_presets[preset_name] = {
                "report": sel_report,
                "labs": an_labs,
                "group": an_group
            }
            st.toast(f"Saved preset '{preset_name}'.")
    with ps_c3:
        if st.session_state.saved_analytics_presets:
            p_choices = list(st.session_state.saved_analytics_presets.keys())
            loaded_p = st.selectbox("Load Preset:", p_choices, key="analytics_load_preset_sel", label_visibility="collapsed")
            if st.button("Apply", key="analytics_apply_preset_btn", use_container_width=True):
                p_cfg = st.session_state.saved_analytics_presets[loaded_p]
                st.session_state.analytics_report_sel = p_cfg["report"]
                st.session_state.analytics_labs_filter = p_cfg["labs"]
                st.session_state.analytics_group_by_sel = p_cfg["group"]
                st.rerun()

    st.write("")

    # --------------------------------------------------------------------------
    # DATA LAYER INVOCATION (get_analytics)
    # --------------------------------------------------------------------------
    rep_rows, rep_kpis, rep_meta = data.get_analytics(
        report_type=sel_report,
        filters={"labs": an_labs, "group_by": an_group},
        currency=st.session_state.currency
    )

    # --------------------------------------------------------------------------
    # KPI CARDS ROW (Insight Cards)
    # --------------------------------------------------------------------------
    if rep_kpis:
        k_cols = st.columns(len(rep_kpis))
        for idx, k in enumerate(rep_kpis):
            with k_cols[idx]:
                pos_cls = "nexus-card-pos-first" if idx == 0 else ("nexus-card-pos-last" if idx == len(rep_kpis) - 1 else "nexus-card-pos-mid")
                render_html(f"""
                <div class="nexus-insight-card {pos_cls}">
                    <div class="nexus-insight-label-row">
                        <span class="nexus-insight-label">{k['label']}</span>
                        <span class="nexus-card-info-badge">ⓘ</span>
                    </div>
                    <div class="nexus-insight-val">{k['val']}</div>
                    <div class="nexus-insight-desc">{k['desc']}</div>
                    <div class="nexus-card-tooltip">
                        <div class="nexus-tooltip-hdr">TELEMETRY INSIGHT</div>
                        <div class="nexus-tooltip-title">{k['label']}: <span style="color:#C8F169;">{k['val']}</span></div>
                        <div class="nexus-tooltip-body">{k['desc']}. Calculated live across all active models matching the selected cohort criteria.</div>
                    </div>
                </div>
                """)
        st.write("")

    # --------------------------------------------------------------------------
    # PRIMARY VISUALIZATION (Altair Chart matching palette)
    # --------------------------------------------------------------------------
    if rep_rows:
        df_chart = pd.DataFrame(rep_rows)
        st.markdown(f"##### {sel_report} Visualization")

        if rep_meta.get("type") == "scatter":
            x_field = rep_meta.get("x")
            y_field = rep_meta.get("y")
            color_field = rep_meta.get("color", "Lab")
            unique_labs = sorted(df_chart[color_field].unique().tolist())
            col_scale = alt.Scale(domain=unique_labs, range=CHART_PALETTE[:len(unique_labs)])

            sc_chart = alt.Chart(df_chart).mark_circle(size=85, opacity=0.85).encode(
                x=alt.X(f"{x_field}:Q", title=x_field),
                y=alt.Y(f"{y_field}:Q", title=y_field, scale=alt.Scale(zero=False)),
                color=alt.Color(f"{color_field}:N", scale=col_scale, legend=alt.Legend(title=None, orient="top")),
                tooltip=[alt.Tooltip(c) for c in df_chart.columns]
            ).properties(height=380)
            st.altair_chart(apply_altair_dark_theme(sc_chart), use_container_width=True)

        elif rep_meta.get("type") == "bar":
            x_field = rep_meta.get("x")
            y_field = rep_meta.get("y")
            b_chart = alt.Chart(df_chart.head(20)).mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3).encode(
                y=alt.Y(f"{y_field}:N", sort="-x", title=None, axis=alt.Axis(labelColor="#CCCFC7", labelFontSize=12)),
                x=alt.X(f"{x_field}:Q", title=rep_meta.get("title", x_field)),
                color=alt.value("#C8F169"),
                tooltip=[alt.Tooltip(c) for c in df_chart.columns]
            ).properties(height=max(280, min(500, len(df_chart[:20]) * 24)))
            st.altair_chart(apply_altair_dark_theme(b_chart), use_container_width=True)

            # ---- MODEL DRILLDOWN: show which models are in each group/tier ----
            _REPORTS_WITH_GROUPS = {
                "Context Window Distribution": ("Context Tier", "context_length"),
                "Lab Market Share": ("Lab", "provider_name"),
                "Price Tier Breakdown": ("Price Tier", "input_price_per_1m_tokens"),
                "Capability Coverage": ("Capability", None),
                "Rating Distribution": ("Rating Band", "avg_rating"),
            }
            if sel_report in _REPORTS_WITH_GROUPS:
                group_col = _REPORTS_WITH_GROUPS[sel_report][0]
                # Get list of group labels from chart rows
                group_labels = [r.get(group_col) or r.get(y_field, "") for r in rep_rows if r.get(group_col) or r.get(y_field)]
                group_labels = [g for g in group_labels if g]

                with st.expander(f"🔍 See which models are in each {group_col.lower()}", expanded=False):
                    if group_labels:
                        # Build lookup from raw_models in data layer
                        all_raw_named = data.get_models(filters={"q": "", "providers": an_labs, "capabilities": [], "max_budget": 9999, "min_ctx": 0, "sort_by": "Model Name"}, currency=st.session_state.currency)
                        # Also fetch raw data for backend fields
                        try:
                            from services import BackendService as _BS
                            all_raw = _BS.get_all_models_for_catalog() or []
                        except Exception:
                            all_raw = []
                        if an_labs:
                            all_raw = [m for m in all_raw if m.get("provider_name") in an_labs]

                        for grp in group_labels:
                            # Filter models per group
                            if sel_report == "Context Window Distribution":
                                tier_ranges = {
                                    "Standard (<=32k)": (0, 32000),
                                    "Expanded (33k - 128k)": (32001, 128000),
                                    "High Capacity (129k - 256k)": (128001, 256000),
                                    "Mega Context (257k - 1M)": (256001, 1000000),
                                    "Ultra Context (1M+)": (1000001, 999999999),
                                }
                                lo, hi = tier_ranges.get(grp, (0, 0))
                                tier_models = [m for m in all_raw if lo <= int(m.get("context_length") or 0) <= hi]
                            elif sel_report == "Lab Market Share":
                                tier_models = [m for m in all_raw if m.get("provider_name") == grp]
                            elif sel_report == "Price Tier Breakdown":
                                price_ranges = {
                                    "Free ($0)": (0, 0),
                                    "Budget (<$1/1M)": (0.0001, 0.9999),
                                    "Mid-Tier ($1-$5/1M)": (1.0, 5.0),
                                    "Flagship (>$5/1M)": (5.0001, 999999),
                                }
                                p_lo, p_hi = price_ranges.get(grp, (0, 999999))
                                tier_models = [m for m in all_raw if p_lo <= float(m.get("input_price_per_1m_tokens") or 0) <= p_hi]
                            elif sel_report == "Capability Coverage":
                                cap_map = {
                                    "Tool Calling / Agentic": lambda m: bool(m.get("supports_tool_use")),
                                    "Step Reasoning (CoT)": lambda m: bool(m.get("supports_reasoning")),
                                    "Vision / Multimodal": lambda m: "image" in (m.get("input_modalities") or "").lower(),
                                    "Free / Open Tier": lambda m: bool(m.get("is_free")) or float(m.get("input_price_per_1m_tokens") or 0) == 0,
                                }
                                fn = cap_map.get(grp)
                                tier_models = [m for m in all_raw if fn and fn(m)] if fn else []
                            elif sel_report == "Rating Distribution":
                                rating_ranges = {
                                    "⭐⭐⭐⭐⭐ 4.5-5.0": (4.5, 5.0),
                                    "⭐⭐⭐⭐ 3.5-4.5": (3.5, 4.499),
                                    "⭐⭐⭐ 2.5-3.5": (2.5, 3.499),
                                    "⭐⭐ 1.5-2.5": (1.5, 2.499),
                                    "⭐ 0-1.5": (0, 1.499),
                                    "Unrated": (0, 0),
                                }
                                r_lo, r_hi = rating_ranges.get(grp, (0, 5))
                                if grp == "Unrated":
                                    tier_models = [m for m in all_raw if not (m.get("avg_rating") and float(m.get("avg_rating") or 0) > 0)]
                                else:
                                    tier_models = [m for m in all_raw if r_lo <= float(m.get("avg_rating") or 0) <= r_hi]
                            else:
                                tier_models = []

                            if not tier_models:
                                continue

                            cnt = len(tier_models)
                            st.markdown(f"**{grp}** — {cnt} model{'s' if cnt != 1 else ''}")
                            pill_html = " ".join([
                                f'<span style="display:inline-block;background:#1C1F1A;border:1px solid #242722;border-radius:4px;padding:3px 9px;margin:2px 3px 2px 0;font-size:0.76rem;color:#CCCFC7;font-family:var(--font-mono);">'
                                f'{m["version_name"]}'
                                f'<span style="color:#6B6E66;margin-left:5px;">{m["provider_name"]}</span>'
                                f'</span>'
                                for m in tier_models[:20]
                            ])
                            if cnt > 20:
                                pill_html += f'<span style="color:#6B6E66;font-size:0.74rem;margin-left:4px;">+{cnt-20} more</span>'
                            render_html(f'<div style="margin-bottom:14px;line-height:2.0;">{pill_html}</div>')

        # --------------------------------------------------------------------------
        # VIEW DATA (Optional Expander per rule 1: Tables only where necessary)
        # --------------------------------------------------------------------------
        with st.expander(f"View Raw Data Table ({len(rep_rows)} records)", expanded=False):
            st.dataframe(df_chart, use_container_width=True, hide_index=True)

        # --------------------------------------------------------------------------
        # EXPORT & SUMMARY BAR
        # --------------------------------------------------------------------------
        st.write("")
        ex1, ex2, ex3 = st.columns([2, 2, 3])
        with ex1:
            csv_data = df_chart.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Export CSV",
                data=csv_data,
                file_name=f"nexus_{sel_report.lower().replace(' ', '_')}.csv",
                mime="text/csv",
                key="analytics_csv_dl_btn",
                use_container_width=True
            )
        with ex2:
            json_str = df_chart.to_json(orient="records", indent=2)
            st.download_button(
                label="Export JSON",
                data=json_str,
                file_name=f"nexus_{sel_report.lower().replace(' ', '_')}.json",
                mime="application/json",
                key="analytics_json_dl_btn",
                use_container_width=True
            )
        with ex3:
            show_summary = st.checkbox("Generate Executive Summary Text", key="analytics_show_summary_chk")

        if show_summary:
            summary_lines = [f"NEXUS AI Enterprise Intelligence Report: {sel_report}"]
            summary_lines.append(f"Currency: {st.session_state.currency} | Filtered Labs: {', '.join(an_labs) if an_labs else 'All'}")
            summary_lines.append("Key Telemetry Highlights:")
            for k in rep_kpis:
                summary_lines.append(f"- {k['label']}: {k['val']} ({k['desc']})")
            summary_lines.append(f"Cohort Size: {len(rep_rows)} records evaluated.")
            summary_text = "\n".join(summary_lines)
            st.code(summary_text, language="markdown")
    else:
        st.info("No telemetry records found for the selected criteria.")


# ==============================================================================
# TOP NAVIGATION SETUP & ENTRYPOINT
# ==============================================================================
nav_pages = {
    "directory": st.Page(page_directory, title="Models", icon=":material/view_list:", default=True),
    "compare": st.Page(page_compare, title="Compare", icon=":material/compare_arrows:"),
    "leaderboard": st.Page(page_leaderboard, title="Leaderboard", icon=":material/leaderboard:"),
    "profile": st.Page(page_profile, title="Profile", icon=":material/psychology:"),
    "matcher": st.Page(page_matcher, title="Cost Matcher", icon=":material/calculate:"),
    "reviews": st.Page(page_reviews, title="Audit & Incidents", icon=":material/rate_review:"),
    "analytics": st.Page(page_analytics, title="Analytics", icon=":material/analytics:"),
}

pg = st.navigation(list(nav_pages.values()), position="top")
pg.run()
