# 🚀 AI Model Registry — Unified DBMS & DSA Backend Engine

An enterprise-grade **Database Management System (DBMS)** and **Data Structures & Algorithms (DSA)** backend project for registering, benchmarking, evaluating, and comparing frontier Artificial Intelligence models.

Designed for dual academic evaluation in both **DBMS Course** and **DSA Course**.

---

## 📑 Table of Contents
1. [System Architecture](#-system-architecture)
2. [DBMS Engineering Showcase](#-dbms-engineering-showcase)
   - [17 Normalized Relational Tables](#17-normalized-relational-tables-3nf)
   - [6 SQL Views](#6-pre-computed-views)
   - [3 Database Triggers](#3-active-database-triggers)
   - [5 Stored Procedures](#5-stored-procedures)
   - [16+ Performance Indexes](#16-performance-indexes)
3. [DSA Engineering Showcase](#-dsa-engineering-showcase)
   - [12 Implemented Data Structures & Algorithms](#12-implemented-data-structures--algorithms)
4. [Quick Start & Setup](#-quick-start--setup)
5. [Frontend Integration Guide (API Reference)](#-frontend-integration-guide-api-reference)

---

## 🏛️ System Architecture

```
                               ┌──────────────────────────────────────────────┐
                               │       Frontend Web Application (React)        │
                               │  Built by Team Member / Consumes REST API    │
                               └──────────────────────┬───────────────────────┘
                                                      │ HTTP / JSON
                                                      ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FASTAPI BACKEND ENGINE (main.py)                                    │
│                                                                                                        │
│  ┌────────────────────────────────────────┐     ┌──────────────────────────────────────────────────┐  │
│  │          REST ROUTE CONTROLLERS         │     │            IN-MEMORY DSA CACHE & STATE           │  │
│  │  - /api/models     (CRUD & Sorting)    │     │  - Trie               : Prefix Autocomplete      │  │
│  │  - /api/providers  (Vendors & Reports) │     │  - HashTable (TTL)    : Query Result Caching     │  │
│  │  - /api/benchmarks (Arena & Leaderboard│     │  - Stack              : Filter Undo History      │  │
│  │  - /api/reviews    (Ratings & Errors)  │     │  - Queue (FIFO)       : Review Moderation        │  │
│  │  - /api/compare    (Matrix & Recommends│     │  - CircularQueue      : Recently Viewed (10)     │  │
│  │  - /api/search     (Multi-param Search)│     │  - DoublyLinkedList   : Model Browsing Cursor    │  │
│  │  - /api/admin      (Metrics & Rebuild) │     │  - SinglyLinkedList   : Search Query History     │  │
│  └───────────────────┬────────────────────┘     │  - Min/Max Heap       : Top-K Model Priority Q   │  │
│                      │                          │  - Merge & Quick Sort : Custom Model Ranking     │  │
│                      │                          │  - Binary Search      : Fast Lookup in O(log n)  │  │
│                      │                          └──────────────────────────────────────────────────┘  │
└──────────────────────┼─────────────────────────────────────────────────────────────────────────────────┘
                       │ SQL Queries & Stored Procedures
                       ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              RELATIONAL DATABASE ENGINE (MySQL 8.x / SQLite)                           │
│                                                                                                        │
│   17 Tables (3NF)  │  6 SQL Views  │  3 Triggers  │  5 Stored Procedures  │  16 Performance Indexes     │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ DBMS Engineering Showcase

### 17 Normalized Relational Tables (3NF)
Every table is normalized into Third Normal Form (3NF) with referential integrity, domain constraints, and appropriate cascade actions:

| # | Table Name | Description | Key Relationships |
|---|---|---|---|
| 1 | `providers` | AI Labs & Organizations (OpenAI, Anthropic, Google, Meta, etc.) | PK: `provider_id` |
| 2 | `model_families` | Model lineage groups (GPT, Claude, Gemini, Llama) | FK → `providers` (CASCADE) |
| 3 | `model_versions` | Specific releases (GPT-4o, Claude 3.5 Sonnet, etc.) | FK → `model_families`, Recursive FK → `model_versions` |
| 4 | `pricing_history` | Historic & current pricing per 1M input/output tokens | FK → `model_versions` (CASCADE) |
| 5 | `capabilities` | Master catalog of AI features (Vision, Coding, Reasoning) | PK: `capability_id` |
| 6 | `model_capabilities` | M:N Junction: model version capability matrix with proficiency | FK → `model_versions`, FK → `capabilities` |
| 7 | `benchmarks` | Standard evaluations (MMLU, HumanEval, GSM8K, Arena Elo) | PK: `benchmark_id` |
| 8 | `benchmark_scores` | Exact quantitative evaluations per model | FK → `model_versions`, FK → `benchmarks` |
| 9 | `use_cases` | Target applications (Software Engineering, Finance, Creative) | PK: `use_case_id` |
| 10 | `model_use_cases` | M:N Junction: suitability rating (0.00 to 1.00) & notes | FK → `model_versions`, FK → `use_cases` |
| 11 | `tags` | Classification labels (Open-Source, Budget, Agentic) | PK: `tag_id` |
| 12 | `model_tags` | M:N Junction: tag assignments | FK → `model_versions`, FK → `tags` |
| 13 | `user_reviews` | Community reviews with 1-5 star ratings & verification | FK → `model_versions` |
| 14 | `error_reports` | Tracking hallucinations, refusals, timeouts, and bugs | FK → `model_versions` |
| 15 | `comparison_logs` | Audit trail of side-by-side model evaluations | FK → `model_versions` |
| 16 | `search_logs` | Search query analytics and performance tracking | Session logging |
| 17 | `api_endpoints` | API gateway specs, authentication modes, and rate limits | FK → `model_versions` (UNIQUE) |

---

### 6 Pre-Computed Views
1. `v_model_full_details`: Multi-table join across `model_versions`, `model_families`, `providers`, and `pricing_history`.
2. `v_top_rated_models`: Dynamic calculation of average ratings and approved review counts.
3. `v_free_models`: Filtered view of models offering free tiers or $0.00 pricing.
4. `v_model_benchmark_summary`: PIVOT-style matrix displaying scores across MMLU, HumanEval, GSM8K, Arena Elo, and GPQA.
5. `v_provider_statistics`: Aggregate vendor statistics (total families, total releases, average prices, price ranges).
6. `v_model_comparison_ready`: Flattened comparison payload optimized for client side-by-side rendering.

---

### 3 Active Database Triggers
1. `trg_validate_pricing`: **BEFORE INSERT** on `pricing_history` — prevents negative pricing.
2. `trg_review_rating_check`: **BEFORE INSERT** on `user_reviews` — validates ratings (1-5) and auto-trims whitespace.
3. `trg_error_resolve_timestamp`: **BEFORE UPDATE** on `error_reports` — automatically populates `resolved_at = NOW()` when status changes to 'resolved'.

---

### 5 Stored Procedures
1. `sp_search_models(query, free_only, min_context, max_price, capability)`: Multi-table parameterized search.
2. `sp_compare_models(version_id_1, version_id_2)`: Generates dual-result sets comparing specs and benchmark scores.
3. `sp_get_top_models(criteria, limit)`: Dynamic ordering query for top performers.
4. `sp_recommend_model(use_case, max_budget, min_context)`: Recommender system matching models to budget and use-case suitability.
5. `sp_provider_report(provider_name)`: Enterprise vendor report returning model catalog and aggregate statistics.

---

## ⚡ DSA Engineering Showcase

### 12 Implemented Data Structures & Algorithms

Every algorithm and data structure is custom-built in pure Python inside the `dsa/` directory:

| Data Structure / Algorithm | Source Module | Real Project Application | Time Complexity | API Route |
|---|---|---|---|---|
| **Trie (Prefix Tree)** | `dsa/trie.py` | Model name instant autocomplete search | $O(L)$ insert, $O(P + K)$ prefix lookup | `GET /api/models/autocomplete` |
| **Hash Table (Separate Chaining)** | `dsa/hash_table.py` | In-memory query result caching with TTL | $O(1)$ average get/put | `GET /api/admin/cache/stats` |
| **Stack (LIFO)** | `dsa/stack.py` | Multi-level filter undo system | $O(1)$ push & pop | `POST /api/search/filters/undo` |
| **Queue (FIFO)** | `dsa/queue_ds.py` | Review moderation workflow queue | $O(1)$ enqueue & dequeue | `GET /api/reviews/moderation/next` |
| **Circular Queue (Ring Buffer)** | `dsa/circular_queue.py` | Fixed buffer of 10 recently viewed models | $O(1)$ rollover enqueue | `GET /api/search/recently-viewed` |
| **Singly Linked List** | `dsa/linked_list.py` | Sequential search query history | $O(1)$ append, $O(n)$ traversal | `GET /api/search/history` |
| **Doubly Linked List** | `dsa/doubly_linked_list.py` | Browser-style back/forward model browsing | $O(1)$ cursor navigation | `POST /api/search/browse/forward` |
| **Min-Heap & Max-Heap** | `dsa/priority_queue.py` | Top-K model extraction (cheapest / highest rated) | $O(n \log k)$ build & extract | `GET /api/models/top` |
| **Merge Sort** | `dsa/sorting.py` | Stable multi-criteria model sorting | $O(n \log n)$ guaranteed | `GET /api/models/?algorithm=merge` |
| **Quick Sort** | `dsa/sorting.py` | High-speed in-memory partitioning sort | $O(n \log n)$ average | `GET /api/models/?algorithm=quick` |
| **Binary Search** | `dsa/searching.py` | Exact model name lookup on sorted array | $O(\log n)$ | `GET /api/models/search?method=binary` |
| **Binary Search Range** | `dsa/searching.py` | Continuous price & context interval filtering | $O(\log n + k)$ | `GET /api/models/price-range` |

---

## 🚀 Quick Start & Setup

### 1. Environment & Database Configuration
Settings are configured in `.env`:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=ai_registry
```
*(Note: If cloud MySQL is offline, the backend automatically and seamlessly switches to the included SQLite database in `data/ai_registry.db` without crashing!)*

### 2. Populate Database (100+ Models)
```bash
.\venv\Scripts\python.exe seed_database.py
```

### 3. Run Automated Test Suite
```bash
.\venv\Scripts\python.exe test_api.py
```

### 4. Start the Backend API Server
```bash
# Option A: Double click run.bat
# Option B: Run via terminal
.\venv\Scripts\uvicorn.exe main:app --reload --port 8000
```
Interactive Swagger API documentation will be available at:
👉 **`http://localhost:8000/docs`**

---

## 🌐 Frontend Integration Guide (API Reference)

For your frontend teammate:

### Base URL
`http://localhost:8000`

### Session Tracking Header
Send this header in all requests to enable user-specific DSA features (History, Filter Undo, Recently Viewed):
```http
X-Session-ID: <unique_user_or_browser_session_string>
```

### Key Endpoints

#### 1. Models & Catalog
- `GET /api/models?page=1&limit=20&sort_by=price&order=asc&algorithm=merge` — Paginated catalog with DSA sorting.
- `GET /api/models/autocomplete?q=gpt` — Autocomplete suggestions using Trie.
- `GET /api/models/top?k=5&criteria=price` — Top 5 cheapest models using MinHeap.
- `GET /api/models/price-range?min_price=0&max_price=5` — Range filter using Binary Search.
- `GET /api/models/{version_id}` — Full specifications joined across 7 tables.

#### 2. Model Comparison & Recommender
- `GET /api/compare?ids=1,2,3` — Side-by-side comparison matrix.
- `GET /api/compare/recommend?use_case=Coding&max_budget=5` — Recommender procedure.

#### 3. Search & Filter Undo (DSA Stack & LinkedList)
- `GET /api/search/advanced?q=claude&free_only=true` — Multi-filter search (pushes state to Stack).
- `POST /api/search/filters/undo` — Revert previous filter (pops state from Stack).
- `GET /api/search/history` — Get search query history (LinkedList).
- `GET /api/search/recently-viewed` — Get 10 recently viewed models (CircularQueue).
- `POST /api/search/browse/backward` — Navigate back in browsing history (DoublyLinkedList).
- `POST /api/search/browse/forward` — Navigate forward in browsing history (DoublyLinkedList).

#### 4. Reviews & Moderation (DSA Queue)
- `POST /api/reviews/` — Submit review (enqueues into FIFO moderation queue).
- `GET /api/reviews/moderation/next` — Dequeue next pending review for admin.
- `PUT /api/reviews/moderation/{review_id}/approve` — Approve review.
- `POST /api/reviews/errors` — Submit model hallucination or bug report.

#### 5. Academic Diagnostics & Summaries
- `GET /api/admin/stats` — Row counts for all 17 tables.
- `GET /api/admin/dsa-summary` — Complete reference guide of all 12 DSA algorithms.
- `GET /api/admin/dbms-summary` — Complete reference guide of all DBMS concepts.

---

## 🖥️ Streamlit Enterprise Intelligence Application (`app.py`)

The project includes an enterprise-grade Streamlit web intelligence dashboard designed following the **"Ink + Acid Lime"** aesthetic:

### Workspaces
1. **Model Directory**: Dense, sortable model catalog with OpenRouter-style ergonomics, instant prefix search, capability filters, and multi-row comparison selection.
2. **Head-to-Head Comparison**: Card-per-model layout (2 to 4 models) with winner strip, parameter diff toggle, horizontal grouped benchmark chart, and executive recommendations.
3. **Performance Leaderboards**: Artificial Analysis-style ranked tables across 4 core metrics plus a comprehensive **All Benchmarks Matrix** view.
4. **Deep Model Profile**: Key-value spec grids for operational capabilities, pricing ledgers, and slimmed benchmark evaluation charts with `#X of Y` catalog rankings.
5. **Smart Cost Matcher**: Workload alignment cards with unit pricing, monthly spend calculations, savings badges, and suitability progress bars.
6. **Developer Reviews & Incident Ledger**: Audited production failure tracking (status-free) and crowdsourced reviews.
7. **Enterprise Analytics & Report Builder**: 10 dynamic intelligence suites, live KPI insight cards, accessible chart themes (`CHART_PALETTE`), and multi-format exports (CSV, JSON, Markdown).

### Running the Streamlit App
```bash
streamlit run app.py
```

