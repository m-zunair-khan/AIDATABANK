# NEXUS AI Changelog

All notable changes to the NEXUS AI platform and data layer are documented here.

---

## [Patch Pass v2.2.0] — Component Overhaul, Custom Card Layouts & Dynamic Intelligence

### 1. Component Overhaul: Tables Only Where Necessary
* **Deep Model Profile**:
  - Replaced operational capability tables with responsive `.nexus-spec-grid` key-value cards and proficiency chips.
  - Eliminated redundant narrative sections in the Benchmarks tab (Methodology, Coverage, and Footnotes) in favor of a clean, focused horizontal bar chart, relative `#X of Y` suite rankings, and a direct "View in Leaderboard" transition.
* **Smart Cost Matcher**:
  - Replaced raw dataframe table with visual `.nexus-match-card` cards.
  - Added large mono monthly projected spend, `-X% vs Budget` savings badges, and dual-tone progress bars reflecting workload suitability scores.
  - Retained executive procurement decision verdict container.
* **Head-to-Head Compare**:
  - Replaced matrix table with a column-per-model layout (2 to 4 models side-by-side).
  - Added top "Winner" strip highlighting the Cheapest Model, Largest Context Window, and Best Developer Rating.
  - Added "Show only differences" toggle to filter out identical parameters across models.
  - Retained horizontal grouped bar benchmark chart and executive recommendation verdict.
* **Enterprise Analytics**:
  - Transformed into an insight-first visual workspace: dynamic KPI summary cards and Altair charts with raw data placed in an optional "View Raw Telemetry Data" expander.

### 2. Advanced Enterprise Analytics & Report Builder
* **Dynamic Report Builder**:
  - Added top controls for selecting from 10 intelligence dimensions:
    1. *Cost Overview* (Pricing spread, median rates, flagship vs budget)
    2. *Cost vs Performance* (Interactive scatter plot correlating token price with benchmark score)
    3. *Lab Market Share* (Vendor catalog distribution and portfolio depth)
    4. *Context Window Distribution* (Memory buffer tiers from <=32k to 1M+ tokens)
    5. *Capability Coverage* (Adoption rates for Tool Calling, Step Reasoning, Vision, Free Tiers)
    6. *Price Tier Breakdown* (Free, Budget, Mid-Tier, and Flagship distribution)
    7. *Rating Distribution* (Developer satisfaction brackets and unrated ratios)
    8. *Incident Trends* (Failure mode breakdown: hallucinations, refusals, timeouts)
    9. *Model Risk Score* (Composite risk index based on incident density and verification)
    10. *Country/Region Breakdown* (Geographic dispersion of foundation model hosts)
  - Added multiselect filtering by lab and grouping by dimension.
  - Added in-memory preset saving and loading via `st.session_state`.
  - Added multi-format exports: CSV, JSON, and executive markdown text summary.

### 3. Cross-Model Benchmark Matrix
* **Leaderboard All Benchmarks View**:
  - Added new 5th tab `All Benchmarks Matrix` in Performance Leaderboard.
  - Cross-evaluates every catalog model across all 6 benchmark suites (*SWE-bench Verified*, *MMLU-Pro*, *Chatbot Arena Elo*, *GSM8K & MATH*, *HumanEval*, *GPQA Diamond*).
  - Heat-style progress indicators for normalized average scores, with lab multiselect and reasoning-only filters.
  - Interactive row selection to immediately transition to any model's Deep Profile.

### 4. Search Engine Optimization
* **Prefix Ranking & Instant Filtering**:
  - Normalized multi-term search matching across model name, laboratory, and family.
  - Prioritizes prefix matches first (e.g. searching "c" places Claude, Command, and Cohere at the top), followed by substring contains.
  - Connected `on_change` and key versioning to ensure immediate reactivity upon typing or pressing Enter.
  - Dynamic empty state reporting `No models match "<query>"` with a single-click reset.

### 5. Colorblind-Safe Chart Design System
* **Consistent Series Palette**:
  - Standardized on `#C8F169` (Acid Lime), `#5BC0EB` (Sky), `#F5B94A` (Amber), `#FF7A7A` (Coral), `#A78BFA` (Violet), and `#2DD4BF` (Teal).
  - Dark-first transparent chart backgrounds, low-opacity subtle gridlines (`rgba(36, 39, 34, 0.45)`), 12px+ typography, and formatted tooltips.

---

## [Verification & Validation]
* 11 comprehensive automated data layer test suites passing with 100% assertions met:
  - Currency conversion across 55+ operational currencies
  - Live relational KPI telemetry
  - Multi-param model directory filtering & prefix ranking
  - Deep profile specifications & circular queue recent views
  - Side-by-side model comparison & spend simulation
  - Leaderboard evaluations across 4 standard metrics + All Benchmarks matrix
  - Stored procedure constraint-based matching
  - Incident tracking & community review moderation
  - Relational schema counts across all 17 tables
  - Search prefix logic for 'c' and empty queries
  - 10-suite analytical intelligence engine
