"""
NEXUS AI — Enterprise Design System & Styling Engine (ui/styles.py)
==================================================================
Cohesive "Ink + Acid Lime" dark theme per design specification:
- Background: Deep Ink (#0B0C0A)
- Surface/Cards: #131512, flat 1px borders (#242722), radius 8px
- Accent: Acid Lime (#C8F169), softer fallback (#B4D957)
- Text: Off-White (#EDEFE9), Secondary (#A3A89C), Muted (#6B6E66)
- Severity only: High (#FF6B6B), Medium (#F5B94A), Low/OK neutral gray
- Fonts: Inter (UI), JetBrains Mono (numbers, tokens, prices)
- Focus ring: #C8F169 with 2px shadow
- Consistent 16-24px spacing, max-width ~1200px
"""

import streamlit as st
import altair as alt

THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* Global Root Variables */
    :root {
        --bg-main: #0B0C0A;
        --bg-surface: #11140F;
        --bg-card: #131512;
        --bg-card-hover: #181B16;
        --border-subtle: #242722;
        --border-hover: rgba(200,241,105,0.4);
        --accent-lime: #C8F169;
        --accent-lime-soft: #B4D957;
        --accent-amber: #F5B94A;
        --accent-rose: #FF6B6B;
        --text-primary: #EDEFE9;
        --text-secondary: #A3A89C;
        --text-muted: #6B6E66;
        --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
    }

    /* Streamlit Global Container */
    html, body, [class*="css"] {
        font-family: var(--font-sans);
        color: var(--text-primary);
        background-color: var(--bg-main);
        font-size: 14.5px;
    }

    .stApp {
        background: radial-gradient(900px 500px at 85% -10%, rgba(200,241,105,0.14), transparent 60%),
                    radial-gradient(700px 500px at -10% 110%, rgba(200,241,105,0.06), transparent 60%),
                    linear-gradient(180deg, #0B0C0A, #0E100C);
        background-attachment: fixed;
        color: var(--text-primary);
    }

    /* Modern Top Navigation & Header */
    [data-testid="stHeader"] {
        background: #0B0C0A !important;
        border-bottom: 1px solid #242722 !important;
    }

    [data-testid="stHeader"] nav a,
    [data-testid="stHeader"] button {
        color: #A3A89C !important;
        font-family: var(--font-sans) !important;
        font-size: 0.86rem !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
        transition: all 0.15s ease !important;
    }

    [data-testid="stHeader"] nav a:hover,
    [data-testid="stHeader"] button:hover {
        color: #EDEFE9 !important;
        background: rgba(200,241,105,0.06) !important;
    }

    [data-testid="stHeader"] nav a[aria-current="page"],
    [data-testid="stHeader"] nav a[data-active="true"] {
        color: #C8F169 !important;
        background: rgba(200,241,105,0.12) !important;
        font-weight: 600 !important;
    }

    .block-container {
        padding-top: 5.5rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1200px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #080907 !important;
        border-right: 1px solid #242722 !important;
    }

    /* Page Titles */
    .nexus-page-title {
        font-size: 24px;
        font-weight: 600;
        color: #EDEFE9;
        letter-spacing: -0.02em;
        margin: 0;
        line-height: 1.2;
    }

    .nexus-page-desc {
        font-size: 14px;
        color: #A3A89C;
        margin-top: 4px;
        margin-bottom: 16px;
        line-height: 1.4;
    }

    /* Dismissible Info Box */
    .nexus-help-box {
        background: #131512;
        border: 1px solid #242722;
        border-left: 3px solid #C8F169;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .nexus-help-title {
        font-size: 0.86rem;
        font-weight: 600;
        color: #EDEFE9;
        margin-bottom: 2px;
    }

    .nexus-help-desc {
        font-size: 0.80rem;
        color: #A3A89C;
        line-height: 1.4;
    }

    /* Inputs, Selectboxes & Textareas with Lime Focus Ring */
    input[type="text"], input[type="number"], textarea, .stSelectbox [data-baseweb="select"] {
        background-color: #131512 !important;
        border: 1px solid #242722 !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-family: var(--font-sans) !important;
        font-size: 0.88rem !important;
        transition: border-color 0.18s, box-shadow 0.18s;
    }

    input[type="text"]:focus, input[type="number"]:focus, textarea:focus,
    .stSelectbox [data-baseweb="select"]:focus-within {
        border-color: #C8F169 !important;
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(200,241,105,0.3) !important;
    }

    /* Buttons */
    button[kind="primary"], .stButton > button[kind="primary"] {
        background: #C8F169 !important;
        border: 1px solid #C8F169 !important;
        border-radius: 8px !important;
        color: #0B0C0A !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.45rem 1.1rem !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }

    button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover {
        background: #D4F67F !important;
        border-color: #D4F67F !important;
        color: #0B0C0A !important;
        transform: translateY(-1px) !important;
    }

    button[kind="secondary"], .stButton > button {
        background: #1C1F1A !important;
        border: 1px solid #242722 !important;
        border-radius: 8px !important;
        color: #EDEFE9 !important;
        font-weight: 500 !important;
        font-size: 0.86rem !important;
        padding: 0.45rem 1rem !important;
        transition: all 0.15s ease !important;
    }

    button[kind="secondary"]:hover, .stButton > button:hover {
        background: #181B16 !important;
        border-color: rgba(200,241,105,0.4) !important;
        color: #EDEFE9 !important;
        transform: translateY(-1px) !important;
    }

    /* Streamlit Tabs: Only active tab is lime; inactive tabs neutral gray */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
        border-bottom: 1px solid #242722;
        padding-bottom: 2px;
        margin-bottom: 16px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #A3A89C !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        padding: 8px 16px !important;
        border-radius: 6px !important;
        border: 1px solid transparent !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.15s ease !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #EDEFE9 !important;
        background: rgba(255, 255, 255, 0.03) !important;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(200,241,105,0.08) !important;
        border-bottom: 2px solid #C8F169 !important;
        color: #C8F169 !important;
        font-weight: 600 !important;
    }

    /* Slider track */
    .stSlider [data-baseweb="slider"] {
        color: #C8F169 !important;
    }

    /* Code blocks */
    code, pre {
        font-family: var(--font-mono) !important;
        background-color: #0A0B09 !important;
        border: 1px solid #242722 !important;
        border-radius: 6px !important;
        color: #D4D6CE !important;
    }

    /* Stat Cards: One Row, Equal Height, Short Labels, Large Mono Numbers */
    .nexus-kpi-card {
        background: #131512;
        border: 1px solid #242722;
        border-radius: 8px;
        padding: 12px 14px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 74px;
        position: relative;
        cursor: default;
        transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, transform 0.2s ease;
    }

    .nexus-kpi-card:hover {
        border-color: rgba(200,241,105,0.6) !important;
        background: #161A13 !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7), 0 0 12px rgba(200, 241, 105, 0.15) !important;
        transform: translateY(-2px);
    }

    .nexus-kpi-label-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 3px;
    }

    .nexus-kpi-label {
        font-size: 0.72rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #A3A89C;
    }

    .nexus-kpi-icon {
        font-size: 0.72rem;
        color: #6B6E66;
        cursor: help;
        transition: color 0.15s;
    }

    .nexus-kpi-icon:hover {
        color: #A3A89C;
    }

    .nexus-kpi-val {
        font-family: var(--font-mono);
        font-size: 1.45rem;
        font-weight: 700;
        color: #EDEFE9;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }

    /* Preset Filter Pills */
    .nexus-preset-btn {
        background: #1C1F1A;
        border: 1px solid #242722;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.78rem;
        color: #A3A89C;
        cursor: pointer;
        transition: all 0.15s;
    }

    .nexus-preset-btn.active {
        border-color: #C8F169;
        color: #C8F169;
        background: rgba(200,241,105,0.08);
    }

    /* Badges & Chips */
    .nexus-badge {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.74rem;
        font-weight: 500;
        line-height: 1.3;
    }

    .badge-neutral {
        background: #1C1F1A;
        border: 1px solid #242722;
        color: #EDEFE9;
    }

    .badge-lime {
        background: rgba(200,241,105,0.12);
        border: 1px solid rgba(200,241,105,0.4);
        color: #C8F169;
        font-weight: 600;
    }

    .badge-high {
        background: rgba(255,107,107,0.12);
        border: 1px solid rgba(255,107,107,0.4);
        color: #FF6B6B;
        font-weight: 600;
    }

    .badge-med {
        background: rgba(245,185,74,0.12);
        border: 1px solid rgba(245,185,74,0.4);
        color: #F5B94A;
        font-weight: 600;
    }

    .badge-low {
        background: #1C1F1A;
        border: 1px solid #242722;
        color: #A3A89C;
    }

    /* Tooltip styles */
    .nexus-term {
        border-bottom: 1px dotted #6B6E66;
        cursor: help;
        position: relative;
    }

    .nexus-term:hover::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        background: #131512;
        border: 1px solid #242722;
        color: #EDEFE9;
        padding: 6px 10px;
        border-radius: 6px;
        font-size: 0.74rem;
        white-space: nowrap;
        z-index: 1000;
        pointer-events: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }

    /* Cards view in directory */
    .nexus-model-card {
        background: #131512;
        border: 1px solid #242722;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 14px;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }

    .nexus-model-card:hover {
        border-color: rgba(200,241,105,0.4);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    }

    /* Hide unnecessary column menu dropdowns on dataframe headers and floating toolbars */
    [data-testid="stDataFrame"] .dvn-header-cell-menu,
    [data-testid="stDataFrame"] button[aria-label="Column menu"],
    [data-testid="stDataFrame"] [data-testid="stDataFrameColumnMenu"],
    [data-testid="stDataFrame"] [data-testid="StyledColumnMenuButton"],
    [data-testid="stDataFrame"] [aria-haspopup="menu"],
    [data-testid="stElementToolbar"] {
        display: none !important;
    }

    /* Checkbox styling inside Streamlit Dataframe */
    [data-testid="stDataFrame"] input[type="checkbox"] {
        accent-color: #C8F169 !important;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #242722 !important;
        border-radius: 8px !important;
        background: #11140F !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }

    [data-testid="stDataFrame"]:hover {
        border-color: rgba(200, 241, 105, 0.35) !important;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.6) !important;
    }

    /* Nexus Styled Matrix & Leaderboard Table */
    .nexus-table-container {
        width: 100%;
        overflow-x: auto;
        border: 1px solid #242722;
        border-radius: 8px;
        background: #11140F;
        margin-bottom: 20px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }

    .nexus-table-container:hover {
        border-color: rgba(200, 241, 105, 0.35);
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.55);
    }

    .nexus-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.88rem;
        text-align: left;
    }

    .nexus-table th {
        background: #161914;
        color: #A3A89C;
        font-weight: 600;
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 13px 16px;
        border-bottom: 1px solid #242722;
        position: sticky;
        top: 0;
        z-index: 2;
    }

    .nexus-table th.num {
        text-align: right;
    }

    .nexus-table td {
        padding: 13px 16px;
        border-bottom: 1px solid #1A1D17;
        color: #EDEFE9;
        font-size: 0.88rem;
        vertical-align: middle;
    }

    .nexus-table td.num {
        font-family: var(--font-mono);
        text-align: right;
        color: #EDEFE9;
    }

    .nexus-table tr:last-child td {
        border-bottom: none;
    }

    .nexus-table tr:hover td {
        background: #1C1F1A;
    }

    .nexus-table td.winner-cell {
        color: #C8F169;
        font-weight: 600;
        background: rgba(200, 241, 105, 0.06);
    }

    /* Rank Pills */
    .nexus-rank-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: var(--font-mono);
        font-size: 0.76rem;
        font-weight: 700;
    }

    .nexus-rank-pill.gold {
        background: rgba(245, 185, 74, 0.16);
        border: 1px solid rgba(245, 185, 74, 0.5);
        color: #F5B94A;
    }

    .nexus-rank-pill.silver {
        background: rgba(205, 214, 224, 0.14);
        border: 1px solid rgba(205, 214, 224, 0.4);
        color: #CDD6E0;
    }

    .nexus-rank-pill.bronze {
        background: rgba(217, 131, 84, 0.15);
        border: 1px solid rgba(217, 131, 84, 0.4);
        color: #D98354;
    }

    .nexus-rank-pill.plain {
        background: #1C1F1A;
        border: 1px solid #242722;
        color: #A3A89C;
    }

    /* Suite Info Dossier Card */
    .nexus-suite-banner {
        background: #131512;
        border: 1px solid #242722;
        border-left: 3px solid #C8F169;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 18px;
    }

    .nexus-bar-track {
        background: #1C1F1A;
        border: 1px solid #242722;
        border-radius: 4px;
        height: 6px;
        width: 100%;
        overflow: hidden;
    }

    .nexus-bar-fill {
        background: linear-gradient(90deg, #99C537, #C8F169);
        height: 6px;
        border-radius: 4px;
    }

    .winner-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(200, 241, 105, 0.15);
        color: #C8F169;
        border-radius: 4px;
        padding: 1px 6px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-left: 6px;
    }

    /* Executive Verdict & Strategic Recommendation Box */
    .nexus-verdict-box {
        background: linear-gradient(180deg, #161914 0%, #11140F 100%);
        border: 1px solid #242722;
        border-left: 4px solid #C8F169;
        border-radius: 8px;
        padding: 18px 22px;
        margin-top: 20px;
        margin-bottom: 24px;
    }

    .nexus-verdict-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }

    .nexus-verdict-tag {
        background: rgba(200, 241, 105, 0.15);
        border: 1px solid rgba(200, 241, 105, 0.4);
        color: #C8F169;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 2px 8px;
        border-radius: 4px;
    }

    .nexus-verdict-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #EDEFE9;
    }

    .nexus-verdict-body {
        font-size: 0.88rem;
        color: #CCCFC7;
        line-height: 1.55;
    }

    /* Column-per-model Comparison Cards */
    .nexus-winner-strip {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 12px;
        margin-bottom: 20px;
    }

    .nexus-winner-item {
        background: #131512;
        border: 1px solid #242722;
        border-top: 3px solid #C8F169;
        border-radius: 8px;
        padding: 14px 16px;
    }

    .nexus-winner-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #A3A89C;
        margin-bottom: 4px;
    }

    .nexus-winner-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #EDEFE9;
        letter-spacing: -0.01em;
    }

    .nexus-winner-sub {
        font-size: 0.78rem;
        color: #A3A89C;
        margin-top: 2px;
        font-family: var(--font-mono);
    }

    .nexus-compare-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }

    .nexus-compare-card {
        background: #131512;
        border: 1px solid #242722;
        border-radius: 8px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        transition: border-color 0.15s ease;
    }

    .nexus-compare-card:hover {
        border-color: rgba(200, 241, 105, 0.4);
    }

    .nexus-compare-header {
        border-bottom: 1px solid #242722;
        padding-bottom: 14px;
        margin-bottom: 14px;
    }

    .nexus-compare-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #EDEFE9;
        letter-spacing: -0.02em;
        margin-bottom: 4px;
    }

    .nexus-compare-meta {
        font-size: 0.80rem;
        color: #A3A89C;
    }

    .nexus-compare-section-title {
        font-size: 0.70rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #6B6E66;
        margin-top: 10px;
        margin-bottom: 6px;
    }

    .nexus-compare-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 7px 0;
        border-bottom: 1px solid #1A1D17;
        font-size: 0.86rem;
    }

    .nexus-compare-row:last-child {
        border-bottom: none;
    }

    .nexus-compare-label {
        color: #A3A89C;
    }

    .nexus-compare-val {
        font-family: var(--font-mono);
        color: #EDEFE9;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Cost Matcher Result Cards */
    .nexus-match-grid {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-top: 16px;
        margin-bottom: 24px;
    }

    .nexus-match-card {
        background: #131512;
        border: 1px solid #242722;
        border-radius: 8px;
        padding: 18px 20px;
        transition: border-color 0.15s ease;
    }

    .nexus-match-card:hover {
        border-color: rgba(200, 241, 105, 0.4);
    }

    .nexus-match-card.best-card {
        border-left: 4px solid #C8F169;
        background: linear-gradient(90deg, rgba(200, 241, 105, 0.04) 0%, #131512 100%);
    }

    .nexus-match-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 12px;
    }

    .nexus-match-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #EDEFE9;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .nexus-match-cost {
        font-family: var(--font-mono);
        font-size: 1.35rem;
        font-weight: 700;
        color: #C8F169;
    }

    .nexus-savings-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(200, 241, 105, 0.12);
        border: 1px solid rgba(200, 241, 105, 0.35);
        color: #C8F169;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.74rem;
        font-weight: 600;
        font-family: var(--font-mono);
    }

    /* Profile Spec Grid */
    .nexus-spec-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 12px;
        margin-bottom: 16px;
    }

    .nexus-spec-card {
        background: #131512;
        border: 1px solid #242722;
        border-radius: 8px;
        padding: 14px 16px;
    }

    .nexus-spec-card-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #A3A89C;
        margin-bottom: 4px;
    }

    .nexus-spec-card-val {
        font-size: 1.05rem;
        font-weight: 600;
        color: #EDEFE9;
    }

    /* Analytics Insight Cards */
    .nexus-insight-card {
        background: #131512;
        border: 1px solid #242722;
        border-radius: 8px;
        padding: 16px 18px;
        min-height: 84px;
        position: relative;
        cursor: default;
        transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease, transform 0.2s ease;
    }

    .nexus-insight-card:hover {
        border-color: rgba(200, 241, 105, 0.6) !important;
        background: #161A13 !important;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.7), 0 0 16px rgba(200, 241, 105, 0.15) !important;
        transform: translateY(-2px);
    }

    .nexus-insight-label-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }

    .nexus-insight-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #A3A89C;
        margin-bottom: 0;
    }

    .nexus-card-info-badge {
        font-size: 0.70rem;
        color: #6B6E66;
        background: #1C1F1A;
        border: 1px solid #242722;
        border-radius: 50%;
        width: 17px;
        height: 17px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
    }

    .nexus-insight-card:hover .nexus-card-info-badge,
    .nexus-kpi-card:hover .nexus-card-info-badge {
        color: #0B0C0A !important;
        background: #C8F169 !important;
        border-color: #C8F169 !important;
        font-weight: 700 !important;
    }

    .nexus-insight-val {
        font-family: var(--font-mono);
        font-size: 1.4rem;
        font-weight: 700;
        color: #EDEFE9;
        letter-spacing: -0.02em;
    }

    .nexus-insight-desc {
        font-size: 0.76rem;
        color: #6B6E66;
        margin-top: 3px;
    }

    /* Stacking Context Elevation: Hover tooltips are NEVER covered by adjacent cards, boxes or tabs */
    div[data-testid="column"]:has(.nexus-insight-card:hover),
    div[data-testid="column"]:has(.nexus-kpi-card:hover),
    div[data-testid="column"]:has(.nexus-spec-card:hover) {
        z-index: 9999999 !important;
        position: relative !important;
    }

    [data-testid="stHorizontalBlock"] {
        overflow: visible !important;
        position: relative !important;
    }

    div[data-testid="column"] {
        overflow: visible !important;
    }

    /* Floating Hover Tooltip Box */
    .nexus-card-tooltip {
        position: absolute;
        bottom: calc(100% + 10px);
        left: 50%;
        transform: translateX(-50%) translateY(4px);
        min-width: 220px;
        max-width: 280px;
        background: #11140E;
        border: 1px solid #C8F169;
        border-radius: 8px;
        padding: 10px 14px;
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.95), 0 0 16px rgba(200, 241, 105, 0.2);
        z-index: 99999999 !important;
        pointer-events: none;
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1), transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .nexus-card-tooltip::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border-width: 6px;
        border-style: solid;
        border-color: #C8F169 transparent transparent transparent;
    }

    /* Alignment adjustments for outer columns to prevent viewport clipping */
    .nexus-card-pos-first .nexus-card-tooltip {
        left: 0 !important;
        transform: translateY(4px) !important;
    }
    .nexus-card-pos-first .nexus-card-tooltip::after {
        left: 28px !important;
        transform: none !important;
    }

    .nexus-card-pos-last .nexus-card-tooltip {
        left: auto !important;
        right: 0 !important;
        transform: translateY(4px) !important;
    }
    .nexus-card-pos-last .nexus-card-tooltip::after {
        left: auto !important;
        right: 28px !important;
        transform: none !important;
    }

    /* Reveal on hover */
    .nexus-insight-card:hover .nexus-card-tooltip,
    .nexus-kpi-card:hover .nexus-card-tooltip {
        opacity: 1 !important;
        visibility: visible !important;
        transform: translateX(-50%) translateY(0) !important;
    }
    .nexus-card-pos-first:hover .nexus-card-tooltip {
        transform: translateY(0) !important;
    }
    .nexus-card-pos-last:hover .nexus-card-tooltip {
        transform: translateY(0) !important;
    }

    .nexus-tooltip-hdr {
        font-size: 0.68rem;
        font-weight: 700;
        color: #C8F169;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 2px;
    }

    .nexus-tooltip-title {
        font-size: 0.84rem;
        font-weight: 600;
        color: #EDEFE9;
        margin-bottom: 4px;
    }

    .nexus-tooltip-body {
        font-size: 0.76rem;
        color: #CCCFC7;
        line-height: 1.45;
    }

    /* Streamlit Dataframe modern overrides */
    [data-testid="stDataFrame"] div[role="columnheader"] {
        background: #131512 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #A3A89C !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #242722 !important;
    }

    [data-testid="stDataFrame"] div[role="row"]:hover {
        background: #1C1F1A !important;
    }

    /* Hide Streamlit default branding */
    #MainMenu, footer { visibility: hidden; }
</style>
"""

# Series palette on dark (distinct, colorblind-safe) per specification
CHART_PALETTE = ["#C8F169", "#5BC0EB", "#F5B94A", "#FF7A7A", "#A78BFA", "#2DD4BF"]

# Multi-currency conversion matrix (55+ Real-world Currencies)
CURRENCIES = {
    "USD ($)": {"symbol": "$", "rate": 1.0, "code": "USD", "name": "US Dollar"},
    "PKR (Rs)": {"symbol": "Rs", "rate": 278.5, "code": "PKR", "name": "Pakistani Rupee"},
    "EUR (€)": {"symbol": "€", "rate": 0.92, "code": "EUR", "name": "Euro"},
    "GBP (£)": {"symbol": "£", "rate": 0.79, "code": "GBP", "name": "British Pound"},
    "INR (₹)": {"symbol": "₹", "rate": 84.5, "code": "INR", "name": "Indian Rupee"},
    "AED (AED)": {"symbol": "AED", "rate": 3.67, "code": "AED", "name": "UAE Dirham"},
    "SAR (SAR)": {"symbol": "SAR", "rate": 3.75, "code": "SAR", "name": "Saudi Riyal"},
    "CAD (C$)": {"symbol": "C$", "rate": 1.38, "code": "CAD", "name": "Canadian Dollar"},
    "AUD (A$)": {"symbol": "A$", "rate": 1.53, "code": "AUD", "name": "Australian Dollar"},
    "JPY (¥)": {"symbol": "¥", "rate": 154.5, "code": "JPY", "name": "Japanese Yen"},
    "CNY (¥)": {"symbol": "¥", "rate": 7.24, "code": "CNY", "name": "Chinese Yuan"},
    "CHF (Fr)": {"symbol": "CHF", "rate": 0.88, "code": "CHF", "name": "Swiss Franc"},
    "SGD (S$)": {"symbol": "S$", "rate": 1.34, "code": "SGD", "name": "Singapore Dollar"},
    "HKD (HK$)": {"symbol": "HK$", "rate": 7.78, "code": "HKD", "name": "Hong Kong Dollar"},
    "KRW (₩)": {"symbol": "₩", "rate": 1395.0, "code": "KRW", "name": "South Korean Won"},
}

ISO_COUNTRY_MAP = {
    "United States": "US", "United Kingdom": "GB", "France": "FR",
    "China": "CN", "Canada": "CA", "Germany": "DE", "Japan": "JP",
    "India": "IN", "Switzerland": "CH", "Israel": "IL", "Singapore": "SG"
}


def format_country(country_name: str) -> str:
    """Formats full country names to standard 2-letter ISO country codes."""
    if not country_name:
        return "GL"
    return ISO_COUNTRY_MAP.get(country_name, country_name[:2].upper())


def format_context(tokens: Any) -> str:
    """Formats integer token contexts into standard 128k / 2M representations."""
    if not tokens:
        return "0"
    try:
        t = int(tokens)
    except (ValueError, TypeError):
        return str(tokens)

    if t >= 1_000_000:
        m = t / 1_000_000
        return f"{int(m)}M" if m.is_integer() else f"{m:.1f}M"
    elif t >= 1_000:
        k = t / 1_000
        return f"{int(k)}k" if k.is_integer() else f"{k:.1f}k"
    return str(t)


def apply_theme():
    """Injects the complete dark-first SaaS styling system into the Streamlit session."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def apply_altair_dark_theme(chart: alt.Chart) -> alt.Chart:
    """Configures Altair charts to match the dark-first design system with minimum 12px text."""
    return chart.configure(
        background="transparent"
    ).configure_view(
        stroke="transparent"
    ).configure_axis(
        domainColor="#242722",
        gridColor="rgba(36, 39, 34, 0.45)",
        gridDash=[2, 4],
        labelColor="#A3A89C",
        labelFont="Inter, sans-serif",
        labelFontSize=12,
        titleColor="#EDEFE9",
        titleFont="Inter, sans-serif",
        titleFontSize=13,
        titleFontWeight=500,
        tickColor="#242722"
    ).configure_legend(
        labelColor="#A3A89C",
        labelFont="Inter, sans-serif",
        labelFontSize=12,
        titleColor="#EDEFE9",
        titleFont="Inter, sans-serif",
        titleFontSize=13
    )
