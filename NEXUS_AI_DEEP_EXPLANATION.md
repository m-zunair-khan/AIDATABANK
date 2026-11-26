# NEXUS AI — Full Logic Flow & Complete Project Explanation

> **Audience**: Someone who needs to understand every file, every function, every call stack, and every design decision — from user click to database and back.

---

## 🗺️ BIG PICTURE: What is NEXUS AI?

NEXUS AI is a full-stack **AI Model Registry and Evaluation Platform**. It lets users:
- Browse 100 real AI models (GPT-4o, Claude 3.5, Gemini, DeepSeek, Llama, etc.)
- Filter, search, and sort them in real-time
- Compare 2–4 models side-by-side
- See benchmark leaderboards
- Get smart cost-based recommendations
- Review incidents and community ratings

It is built on **three layers** that work together:

```
[ Layer 1 ]  Streamlit Frontend (app.py)      ← What the user sees
[ Layer 2 ]  Python Business Logic             ← data.py, services/, dsa/
[ Layer 3 ]  Relational Database               ← MySQL (Aiven Cloud) + SQLite fallback
```

---

## 🌳 FULL PROJECT FILE TREE (excluding venv)

```
D:\dbms proejcct\
│
├── app.py                    ← Streamlit UI (7 pages, all user interactions)
├── data.py                   ← Data access layer (only file app.py talks to for data)
├── main.py                   ← FastAPI REST API server entry point
├── db.py                     ← Database connection manager (MySQL + SQLite fallback)
├── config.py                 ← Loads .env credentials into a Settings object
├── seed_database.py          ← One-time script: reads model_catalog.json → inserts 2235+ rows
├── test_data.py              ← 11-test verification suite for data.py
├── test_api.py               ← Automated tests for FastAPI REST endpoints
│
├── .env                      ← Secret credentials (DB host, user, password, SSL cert path)
├── ca.pem                    ← SSL certificate for encrypted MySQL connection
├── requirements.txt          ← Python package dependencies
├── run.bat / run_frontend.bat← Windows launchers (double-click to start)
│
├── dsa/                      ← 12 pure-Python data structures (no external libraries)
│   ├── trie.py
│   ├── hash_table.py
│   ├── stack.py
│   ├── queue_ds.py
│   ├── circular_queue.py
│   ├── linked_list.py
│   ├── doubly_linked_list.py
│   ├── priority_queue.py
│   ├── sorting.py
│   ├── searching.py
│   └── __init__.py
│
├── services/
│   ├── dsa_manager.py        ← Singleton that owns all DSA instances
│   └── backend_service.py    ← SQL query functions for data.py to call
│
├── routes/                   ← FastAPI route modules (REST API endpoints)
│   ├── models.py
│   ├── providers.py
│   ├── benchmarks.py
│   ├── reviews.py
│   ├── compare.py
│   ├── search.py
│   └── admin.py
│
├── sql/                      ← Raw SQL scripts (run once to set up MySQL)
│   ├── schema.sql            ← 17 tables (3NF normalized)
│   ├── views.sql             ← 6 analytical views
│   ├── triggers.sql          ← 3 triggers (auto-validation)
│   ├── procedures.sql        ← 5 stored procedures
│   └── indexes.sql           ← 16 B-Tree indexes
│
├── ui/
│   └── styles.py             ← CSS theme, color constants, format helpers
│
├── data/
│   └── ai_registry.db        ← Local SQLite database (offline fallback)
│
└── .streamlit/
    └── config.toml           ← Streamlit theme and server config
```

---

## ⚙️ HOW DATA GOT FROM API INTO THE DATABASE

This is one of the most important questions. Here is exactly what happened, step by step:

### Step 1 — External API Data Was Fetched

A **data collection script** (referenced in seed_database.py as `model_catalog.json`) pulled real model data from two public APIs:
- **OpenRouter API** (`https://openrouter.ai/api/v1/models`) — Provides model names, pricing, context windows, tool support, reasoning flags, and OpenRouter model IDs.
- **Hugging Face Open LLM Leaderboard** — Provides benchmark scores (MMLU, HumanEval, GSM8K, etc.).

The raw API responses were cleaned and saved as `data/model_catalog.json` — a JSON file containing 100 model objects, each with fields like:
```json
{
  "model_name": "Claude 3.5 Sonnet",
  "provider": "Anthropic",
  "group_name": "Claude",
  "openrouter_id": "anthropic/claude-3-5-sonnet",
  "context_length_tokens": 200000,
  "price_input_per_1m_tokens_usd": 3.00,
  "price_output_per_1m_tokens_usd": 15.00,
  "supports_tools": "Yes",
  "supports_reasoning": "No",
  "free_or_paid": "Paid",
  "released_date": "2024-06-20"
}
```

### Step 2 — seed_database.py Reads the JSON and Populates All 17 Tables

You run `python seed_database.py` **once**. It performs 10 ordered steps:

```
Step 1  → Connects to DB (MySQL or SQLite)
Step 2  → Creates all 17 tables (via schema DDL)
Step 3  → Inserts 9 providers (OpenAI, Anthropic, Google, Meta, etc.)
Step 4  → Inserts 6 benchmark definitions (MMLU, HumanEval, GSM8K, GPQA, Chatbot Arena, LiveCodeBench)
Step 5  → Inserts 9 capabilities (Coding, Vision, Tool Calling, Reasoning, Structured Output, Math, etc.)
Step 6  → Reads model_catalog.json → inserts model_families + model_versions + pricing_history + api_endpoints
Step 7  → Links capabilities to each model in model_capabilities table
Step 8  → Inserts benchmark scores for each model in benchmark_scores table
Step 9  → Inserts 123 user reviews + 23 error/incident reports
Step 10 → Inserts use_case + model_use_cases suitability ratings + tags + model_tags
```

**The exact call stack for inserting one model (e.g., Claude 3.5 Sonnet):**
```
seed_database.py::main()
  → reads catalog JSON
  → for each model in catalog:
      → execute_query("INSERT INTO model_families ...")     [creates "Claude" family under Anthropic]
      → execute_query("INSERT INTO model_versions ...")     [inserts Claude 3.5 Sonnet row]
      → execute_query("INSERT INTO pricing_history ...")    [inserts $3.00 input / $15.00 output]
      → execute_query("INSERT INTO api_endpoints ...")      [inserts API base URL + rate limit]
  → for each model_version inserted:
      → execute_many("INSERT INTO model_capabilities ...")  [links Tool Calling, Coding caps]
      → execute_many("INSERT INTO benchmark_scores ...")    [inserts 6 benchmark scores]
      → execute_many("INSERT INTO model_use_cases ...")     [suitability: 0.95 for Coding, etc.]
  → for each review in hardcoded list:
      → execute_query("INSERT INTO user_reviews ...")       [123 community reviews, some approved]
  → for each incident:
      → execute_query("INSERT INTO error_reports ...")      [23 incidents, mixed severity]
```

### Step 3 — The Database Now Has 2,235+ Rows Across 17 Tables

After `seed_database.py` finishes, MySQL contains all data. From this point on, `app.py` only **reads** from the database — it never re-runs the seed script.

---

## ⭐ WHERE DO REVIEWS AND RATINGS COME FROM?

### Source of the Initial 123 Reviews

They were **hardcoded inside `seed_database.py`** as realistic synthetic data. The script generates them like this:

```python
reviews = [
  ("Claude 3.5 Sonnet", "developer_alice", 5, "Best coding assistant", "Handles complex multi-file refactors perfectly."),
  ("GPT-4o", "researcher_bob", 4, "Great vision model", "Image understanding is excellent but pricey."),
  ...
]
for version_name, reviewer, rating, title, text in reviews:
    execute_query("""
        INSERT INTO user_reviews (version_id, reviewer_name, rating, title, review_text, is_approved)
        VALUES (%s, %s, %s, %s, %s, 1)
    """, (version_id_map[version_name], reviewer, rating, title, text))
```

Some are inserted with `is_approved = 1` (visible), some with `is_approved = 0` (pending moderation queue).

### How New Reviews Are Submitted (Live Flow)

When a user submits a review through the **Audit & Incidents** tab in the app, or via the FastAPI endpoint `POST /api/reviews/`:

```
User clicks "Submit Review" in app.py
  → app.py calls data.py::submit_review(payload)
  → data.py calls BackendService.submit_review(payload)
  → BackendService calls db.execute_query("""
        INSERT INTO user_reviews
        (version_id, reviewer_name, rating, title, review_text, is_approved)
        VALUES (%s, %s, %s, %s, %s, 0)       ← always starts unapproved
    """)
  → MySQL trigger trg_review_rating_check fires BEFORE INSERT:
        * Auto-trims reviewer_name whitespace
        * Validates rating is between 1 and 5 (raises SQL error if not)
  → Row is committed to user_reviews table
  → dsa_manager.submit_review_for_moderation(review_data) is called
        * Calls Queue.enqueue(review_data)   ← O(1), FIFO DSA
  → Returns {"message": "Review submitted", "queue_position": N}
```

### Where Ratings Are Used in the UI

The Rating column in the Models table is computed at query time:

```sql
COALESCE(
    (SELECT AVG(rating) FROM user_reviews
     WHERE version_id = mv.version_id AND is_approved = 1),
    0
) AS avg_rating
```

This means:
- Only **approved** reviews count toward the visible rating.
- If a model has zero approved reviews, rating shows as `0.00`.
- When admin approves a review via `PUT /api/reviews/moderation/{id}/approve`, the rating recalculates automatically on next page load.

---

## 🗄️ WHERE CAN YOU SEE THE DATABASE VISUALLY?

You have **three options**, from easiest to most powerful:

### Option 1 — MySQL Workbench (Best for MySQL)
1. Download: https://dev.mysql.com/downloads/workbench/
2. Open MySQL Workbench → New Connection
3. Enter your Aiven Cloud credentials from your `.env` file:
   - **Host**: `dbmsproject99-mzunairkhaan-84e0.j.aivencloud.com`
   - **Port**: `26703`
   - **User**: value of `DB_USER` from `.env`
   - **Password**: value of `DB_PASSWORD` from `.env`
   - **SSL CA File**: point to `ca.pem` in your project folder
4. Click Connect → you can browse all 17 tables, run SQL, see row counts, build ER diagrams.

### Option 2 — DBeaver (Best Universal Tool, Free)
1. Download: https://dbeaver.io/download/
2. New Connection → MySQL → Enter Aiven credentials
3. Enable SSL → set CA certificate to `ca.pem`
4. Features: table browser, SQL editor, visual ER diagram (Database → Tools → ER Diagram), data export.

### Option 3 — SQLite Browser (For the Local Fallback DB)
1. Download: https://sqlitebrowser.org/
2. Open File → `D:\dbms proejcct\data\ai_registry.db`
3. Browse all tables, run queries, export CSV — no login needed.

### Option 4 — FastAPI Admin Endpoints (Already Built In!)
Navigate to `http://localhost:8000/docs` while the API server is running:
- `GET /api/admin/schema-counts` — shows row counts for all 17 tables
- `GET /api/admin/dsa-summary` — shows all 12 DSA structures and their usage
- `GET /api/admin/dbms-summary` — shows tables, views, triggers, procedures

---

## 📄 EVERY FILE EXPLAINED: What It Does, Why It Exists, How It Connects

---

### `config.py` — Configuration & Secrets Manager

**What it does:**
Loads the `.env` file and exposes all configuration values as a single `settings` object.

**Why it exists:**
Keeps secrets (database password, host) OUT of the code. Any file that needs credentials imports `from config import settings` instead of hardcoding strings.

**How it connects:**
```
.env file → dotenv.load_dotenv() → config.Settings class → settings object
                                                              ↓
                                               db.py imports settings.DB_HOST etc.
```

**Key settings:**
| Setting | Default | Purpose |
|---|---|---|
| `DB_HOST` | `localhost` | Cloud MySQL hostname |
| `DB_PORT` | `3306` | MySQL port (Aiven uses 26703) |
| `SQLITE_PATH` | `data/ai_registry.db` | Offline fallback file |
| `CACHE_CAPACITY` | `128` | Hash table size (slots) |
| `CACHE_TTL` | `300` | Cache expiry in seconds (5 min) |
| `RECENT_VIEWS_CAPACITY` | `10` | Circular queue size |

---

### `db.py` — Database Connection Manager

**What it does:**
The single gateway to the database. Every SQL query in the entire project goes through `db.execute_query()`.

**Why it exists:**
Centralizes all database access so that:
1. MySQL and SQLite can be swapped transparently
2. Connection pooling is handled once
3. Any MySQL failure automatically falls back to SQLite — the UI never crashes

**How it connects:**
```
Every other file → db.execute_query(sql, params)
                        ↓ (tries MySQL first)
              MySQL Pool → Aiven Cloud MySQL (via SSL)
                        ↓ (if MySQL fails, automatically...)
              _execute_sqlite() → local ai_registry.db
```

**Detailed internal flow of `execute_query()`:**
```python
execute_query(query, params, fetch_one=False, fetch_all=True):

  1. If MySQL is active:
       a. Get a connection from the pool (pool_size=5)
       b. Execute the SQL query with params
       c. Fetch result as list of dicts (cursor(dictionary=True))
       d. Return result
       e. If MySQL raises ANY exception → fall through to SQLite
  
  2. If SQLite mode:
       a. _convert_query_to_sqlite(query):
            - Replace %s → ? (SQLite uses ? as placeholder)
            - Replace NOW() → datetime('now')
            - Replace TRUE/FALSE → 1/0
       b. Execute on local ai_registry.db
       c. Return rows as list of dicts
```

**`execute_many()`**: Batch inserts (used by seed_database.py for bulk capability/benchmark/tag linking). Same MySQL → SQLite fallback logic.

**`call_procedure()`**: Calls MySQL stored procedures. If the stored procedure doesn't exist in MySQL (or we're in SQLite mode), it calls `_emulate_procedure_sqlite()` which re-implements the same logic in pure Python + SQL — **this is why the app never crashes even when MySQL stored procedures aren't deployed**.

---

### `main.py` — FastAPI REST API Server

**What it does:**
Sets up and runs the FastAPI web server that exposes a full REST API at `http://localhost:8000`.

**Why it exists:**
Provides a machine-readable JSON interface to the same database, so any other frontend (mobile app, another team member's project, Postman testing) can consume NEXUS AI data without touching the Streamlit UI.

**How it connects:**
```
main.py startup → lifespan() runs:
  1. execute_query(SELECT all models with JOINs)    ← DB query
  2. dsa_manager.build_autocomplete(all_models)     ← loads 100 model names into Trie
  3. dsa_manager.build_sorted_index(all_models)     ← builds sorted array for binary search

main.py registers routers:
  app.include_router(models.router)       → /api/models/*
  app.include_router(providers.router)    → /api/providers/*
  app.include_router(benchmarks.router)   → /api/benchmarks/*
  app.include_router(reviews.router)      → /api/reviews/*
  app.include_router(compare.router)      → /api/compare/*
  app.include_router(search.router)       → /api/search/*
  app.include_router(admin.router)        → /api/admin/*
```

**Swagger UI** at `/docs` auto-generates interactive documentation from the FastAPI route definitions — you can test every endpoint from the browser.

---

### `services/dsa_manager.py` — DSA Singleton Manager

**What it does:**
Owns and manages exactly **one instance** of each DSA data structure (the "singleton" pattern — created once at import time, shared by every request).

**Why it exists:**
DSA structures need to persist in memory across requests. For example, the Trie is loaded once at startup with 100 model names — if each request re-built it, it would waste time. The singleton keeps it alive.

**Key design:**
```python
class DSAManager:
    def __init__(self):
        # GLOBAL structures (shared by all users):
        self.autocomplete_trie = Trie()         # All 100 model names, loaded at startup
        self.query_cache = HashTable(128)        # Request result cache with TTL
        self.review_queue = Queue()              # FIFO moderation queue
        self._sorted_models = []                 # Sorted array for binary search

        # PER-SESSION structures (keyed by session_id string):
        self._filter_stacks = {}                 # session_id → Stack
        self._browse_history = {}                # session_id → DoublyLinkedList
        self._search_history = {}                # session_id → LinkedList
        self._recently_viewed = {}               # session_id → CircularQueue

dsa_manager = DSAManager()   # ← SINGLETON, created once when Python imports this module
```

**How it connects:**
```
main.py     → imports dsa_manager → calls build_autocomplete() at startup
routes/*.py → imports dsa_manager → calls autocomplete(), sort_models(), cache_get() etc.
data.py     → imports dsa_manager → calls push_filter(), undo_filter(), sort_models(), etc.
```

---

### `services/backend_service.py` — SQL Query Functions

**What it does:**
Contains all the complex SQL queries for `data.py` to call. It's the SQL-writing layer.

**Why it exists:**
Separation of concerns: `data.py` knows **what** to ask for; `backend_service.py` knows **how** to ask the database.

**Key functions:**
| Function | SQL it runs | Returns |
|---|---|---|
| `get_all_models_for_catalog()` | 7-table JOIN joining versions + families + providers + pricing + ratings + tools | List of 100 model dicts |
| `get_kpi_metrics()` | COUNT, AVG, MAX aggregations | 6 platform KPI numbers |
| `get_all_benchmarks_for_leaderboard()` | Pivots benchmark_scores + benchmark names | Leaderboard rows |
| `get_model_full_profile(id)` | 7 separate queries for one model | Full profile dict |
| `get_providers_and_countries()` | SELECT DISTINCT from providers | Lists for filter dropdowns |
| `submit_review(payload)` | INSERT INTO user_reviews | Insert result |

---

### `data.py` — The Central Data Layer (Most Important Bridge)

**What it does:**
The **only** file that `app.py` calls for data. It acts as a translator between what the UI needs and what the database/DSA provides.

**Why it exists:**
Complete separation between presentation (app.py) and data retrieval (services + db). If you ever switch databases or change schema, you only change `data.py` and `backend_service.py` — `app.py` never needs to know.

**Complete call trace for the Models Directory page:**

```
USER clicks "Models" tab in browser
  ↓
app.py::page_directory() runs
  ↓
app.py calls data.get_models(filters, sort="Cost: Low to High", currency="PKR (Rs)")
  ↓
data.get_models():
  1. Calls BackendService.get_all_models_for_catalog()
       ↓
     backend_service runs SQL:
       SELECT mv.version_id, mv.version_name, mv.context_length,
              mv.supports_tool_use, mv.supports_reasoning,
              mf.name AS family_name,
              p.name AS provider_name, p.headquarters_country,
              ph.input_price_per_1m_tokens, ph.output_price_per_1m_tokens,
              COALESCE((SELECT AVG(rating) FROM user_reviews
                        WHERE version_id = mv.version_id AND is_approved = 1), 0) AS avg_rating
       FROM model_versions mv
       JOIN model_families mf ON mv.family_id = mf.family_id
       JOIN providers p ON mf.provider_id = p.provider_id
       LEFT JOIN pricing_history ph ON mv.version_id = ph.version_id
       ↓
     db.execute_query() sends this to MySQL (or SQLite)
       ↓
     Returns: Python list of 100 raw dicts (prices in USD)

  2. Applies Python-side filtering:
     - If filters["q"] = "claude" → keeps only rows where name/family/provider contains "claude"
       Also assigns search_rank=0 for prefix match, 1-3 for contains match
     - If filters["providers"] = ["Anthropic"] → keeps only Anthropic rows
     - If filters["max_budget"] = 5.0 PKR → converts to USD (5.0 / 278.5 = $0.018) → filters
     - If filters["min_ctx"] = 128000 → drops models with context_length < 128000
     - If filters["capabilities"] has "Tool Calling" → drops models without supports_tool_use

  3. Sorts using DSA:
     dsa_manager.sort_models(filtered_list, sort_by="price", order="asc", algorithm="merge")
       ↓
     dsa/sorting.py::merge_sort(arr, key=lambda m: m["input_price_per_1m_tokens"])
       ↓
     Returns sorted Python list (original data untouched — returns a new list)

  4. Formats each model dict:
     - Converts USD prices → PKR (multiply by 278.5)
     - Builds "Capabilities" string: "Tools · Reasoning"
     - Formats context: 128000 → "128K"
     ↓
  Returns: List of formatted dicts ready for Streamlit's st.dataframe()
  ↓
app.py renders table with st.dataframe(catalog_models)
```

---

## 🧠 EVERY DSA STRUCTURE — WITH REAL USAGE EXAMPLES

---

### 1. Trie (Prefix Tree) — `dsa/trie.py`

**What it is:** A tree where each letter of a word is one node. Words share common prefixes.

**How it's built:**
```
Insert "claude":    root → c → l → a → u → d → e* (data: Claude model dict)
Insert "claude 3":  root → c → l → a → u → d → e → (space) → 3* (data: Claude 3 dict)
Insert "command":   root → c → o → m → m → a → n → d*
```

**Real usage example:**
User types `"cl"` in the search box → `dsa_manager.autocomplete("cl")`:
1. Navigate Trie: root → c → l (found node)
2. DFS from that node, collect all complete words: "claude", "claude 3", "claude 3.5 sonnet"...
3. Returns in O(2 + K) time where K is number of matches

**Call stack:**
```
User types "cl" in search box
  → app.py search_input widget triggers rerun
  → data.search_trie("cl") → dsa_manager.autocomplete("cl")
  → Trie.starts_with("cl")
      → navigate to node at 'c' → 'l'
      → DFS all branches from that node
      → returns [("claude", {model data}), ("claude 3.5", {data}), ...]
  → Returns top 10 matches as dropdown suggestions
```

---

### 2. Hash Table (Separate Chaining) — `dsa/hash_table.py`

**What it is:** Stores key-value pairs using a hash function. When two keys hash to the same slot, it uses a linked list at that slot (separate chaining).

**How it works internally:**
```python
# Slot = hash("models:list:1:20:name:asc:merge") % 128
# If slot 47 is free → store there
# If slot 47 is taken → add new node to linked list at slot 47
```

**Real usage example:**
User refreshes the leaderboard 3 times in 5 seconds:
- **1st request**: cache miss → runs full 7-table SQL query (200ms) → stores result in hash table with TTL=180s
- **2nd request**: `cache_get("leaderboard:...")` → hash lookup → O(1) → returns cached result instantly
- **3rd request**: Same O(1) retrieval

**Call stack:**
```
routes/models.py::list_models(page=1, limit=20, sort_by="name")
  → cache_key = "models:list:1:20:name:asc:merge"
  → dsa_manager.cache_get(cache_key)
      → HashTable.get(cache_key)
          → slot = hash(cache_key) % 128  = 47
          → scan linked list at slot 47 for key match
          → check TTL: if time.time() - stored_time < 180 → return value
          → else: return None (expired)
  → If cache hit: return instantly, skip SQL entirely
  → If cache miss: run SQL, then cache_put(key, result, ttl=180)
```

---

### 3. Stack (LIFO) — `dsa/stack.py`

**What it is:** A list where you can only add or remove from the top. Last in = first out.

**Real usage example:**
User applies 3 filters in sequence:
1. Filters by "Anthropic" → Stack: `[filter_A]`
2. Filters by context ≥ 128K → Stack: `[filter_A, filter_B]`
3. Sets price ≤ $3 → Stack: `[filter_A, filter_B, filter_C]`
4. Clicks **Undo Filter** → Stack.pop() → `[filter_A, filter_B]` → Catalog shows 128K+ Anthropic models again

**Call stack:**
```
User clicks "Undo Filter (Stack)" button in app.py
  → app.py calls data.undo_filter_state(session_id)
  → data.py calls dsa_manager.undo_filter(session_id)
  → Stack.pop()  ← O(1)
  → returns previous filter dict
  → app.py sets st.session_state.active_filters = returned_dict
  → st.rerun() → catalog re-renders with restored filters
```

---

### 4. Queue (FIFO) — `dsa/queue_ds.py`

**What it is:** Items enter at the back and exit from the front. First in = first out. Like a queue at a service counter.

**Real usage example:**
3 users submit reviews:
1. Alice reviews GPT-4o → `queue.enqueue(alice_review)`  → Queue: [alice]
2. Bob reviews Claude → `queue.enqueue(bob_review)` → Queue: [alice, bob]
3. Admin clicks "Review Next" → `queue.dequeue()` → returns alice_review (oldest first) → Queue: [bob]

**Call stack:**
```
POST /api/reviews/ with {version_id: 5, reviewer_name: "Alice", rating: 4}
  → routes/reviews.py::submit_review()
  → db.execute_query("INSERT INTO user_reviews ... is_approved=0")
  → MySQL trigger trg_review_rating_check fires → trims name, validates rating
  → review_id = last inserted row id
  → dsa_manager.submit_review_for_moderation({review_id, ...})
      → Queue.enqueue(review_data)   ← O(1) append to back

GET /api/reviews/moderation/next
  → dsa_manager.get_next_review_to_moderate()
      → Queue.dequeue()   ← O(1) remove from front
  → Returns alice's review for admin to approve/reject
```

---

### 5. Circular Queue (Ring Buffer) — `dsa/circular_queue.py`

**What it is:** A fixed-size queue where the rear "wraps around" to the front when full, overwriting the oldest entry.

**How it works:**
```
Capacity = 10 slots. Indices 0-9 form a ring.
Buffer: [None, None, None, None, None, None, None, None, None, None]
                           ↑ front=0, rear=0

Add model 1:  front=0, rear=1
Add model 2:  front=0, rear=2
...
Add model 10: front=0, rear=0  ← FULL (rear wrapped to 0)

Add model 11 (overflow):
  - Overwrite slot at front (slot 0, oldest model)
  - front = 1 (oldest is now slot 1)
  - rear = 1
  - Now contains models 2 through 11 (10 most recent)
```

**Real usage example:**
User views 12 different model profiles. Sidebar shows "Recently Viewed":
- After 10 views: Models 1-10 are in the ring buffer
- After 11th view: Model 1 is overwritten; ring shows Models 2-11
- After 12th view: Model 2 is overwritten; ring shows Models 3-12

**Call stack:**
```
User clicks on "Claude 3.5 Sonnet" profile
  → app.py::page_profile() → data.track_view(session_id, model_data)
  → dsa_manager.add_recent_view(session_id, model_summary)
      → CircularQueue.enqueue(model_summary)   ← O(1)
          → if full: overwrite front, advance front pointer
          → else: write at rear, advance rear pointer

Sidebar renders:
  → data.get_recently_viewed(session_id)
  → dsa_manager.get_recently_viewed(session_id)
      → CircularQueue.to_list()   ← O(10) = O(capacity)
  → Returns up to 10 most recently viewed models
```

---

### 6. Singly Linked List — `dsa/linked_list.py`

**What it is:** A chain of nodes where each node holds a value and a pointer to the next node.

**Real usage:**
Stores search query history chronologically. Each new search appends a node to the end of the chain.

```
HEAD → ["claude"] → ["gpt-4"] → ["gemini"] → None
```

**Call stack:**
```
User types "gemini" in search and presses Enter
  → data.py::search_models("gemini", session_id)
  → dsa_manager.add_search(session_id, "gemini")
      → LinkedList.append("gemini")
          → create Node("gemini")
          → traverse to tail → tail.next = new_node   ← O(n) for append
```

---

### 7. Doubly Linked List — `dsa/doubly_linked_list.py`

**What it is:** Like singly linked list but each node has pointers to BOTH next AND previous nodes. Enables bidirectional traversal.

**Real usage:**
Acts as a **browse cursor** — like a browser's back/forward buttons when clicking through model profiles.

```
← prev | GPT-4o | next → ↔ ← prev | Claude 3.5 | next → ↔ ← prev | Gemini | next →
                                              ↑ current cursor
```

**Call stack:**
```
User clicks "< Previous Model" button
  → data.browse_backward(session_id)
  → dsa_manager.browse_backward(session_id)
      → DoublyLinkedList.move_backward()
          → current = current.prev   ← O(1)
      → Returns GPT-4o model data
  → app.py re-renders profile page with GPT-4o
```

---

### 8. Min-Heap & Max-Heap — `dsa/priority_queue.py`

**What it is:** A complete binary tree where the smallest (Min-Heap) or largest (Max-Heap) value is always at the root.

**How it works:**
- Insert: add at bottom, bubble up → O(log n)
- Extract top: remove root, replace with last element, sink down → O(log n)
- Top-K extraction: insert all n items, extract K times → O(n log k)

**Real usage example:**
Get the 5 cheapest models using Min-Heap:
```
Insert all 100 model prices into Min-Heap.
Extract 5 times → pops the 5 smallest values in order.
Result: [Free model, $0.027/M, $0.030/M, $0.037/M, $0.045/M]
```

**Call stack:**
```
GET /api/models/top?k=5&criteria=price
  → routes/models.py::get_top_models(k=5, criteria="price")
  → models = execute_query(full JOIN query)   ← 100 model rows from DB
  → dsa_manager.get_top_k_models(models, k=5, criteria="price", reverse=True)
      → top_k(models, 5, key=lambda m: m["input_price"], reverse=True)
          → Uses MinHeap since reverse=True (cheaper = better)
          → Heapify all 100 items
          → Extract 5 times → 5 cheapest models
      → Returns sorted list of 5 cheapest models
  → Returns JSON with 5 cheapest models
```

---

### 9. Merge Sort — `dsa/sorting.py`

**What it is:** Divide-and-conquer sorting. Splits the list in half recursively, sorts each half, then merges them back in sorted order. Always O(n log n), **stable** (equal items keep their original order).

**Why stable matters:**
If you sort by price and two models have the same price ($1.00), their original database order is preserved — this matters for multi-criteria sorting.

**Real usage example:**
User clicks "Cost ⬇ Top" button (most expensive first):
```
100 models → merge_sort(models, key=lambda m: m["input_price"], reverse=True)

Recursion trace for 4 models [$0.03, $3.00, $0.05, $15.00]:
  split → [$0.03, $3.00] and [$0.05, $15.00]
    split → [$0.03] and [$3.00] → merge → [$0.03, $3.00]
    split → [$0.05] and [$15.00] → merge → [$0.05, $15.00]
  merge (reverse=True) → [$15.00, $3.00, $0.05, $0.03]  ✓
```

**Call stack:**
```
User clicks "Input ⬇ Top" button
  → app.py sets active_filters["sort_by"] = "Cost: High to Low"
  → st.rerun()
  → data.get_models(filters, sort="Cost: High to Low")
  → dsa_manager.sort_models(filtered, sort_by="price", order="desc", algorithm="merge")
      → merge_sort(filtered, key=lambda m: m["input_price_per_1m_tokens"], reverse=True)
      → Returns new sorted list (100 models, expensive first)
  → app.py re-renders table with new order
```

---

### 10. Quick Sort — `dsa/sorting.py`

**What it is:** Picks a pivot element, partitions all items into less/equal/greater groups, recurses on each group. O(n log n) average, faster in practice than merge sort due to cache efficiency.

**Key difference from merge sort:**
Quick Sort is NOT stable (equal elements may reorder). Best for single-criterion sorting where speed matters.

**Real usage:**
User switches "DSA Algorithm" dropdown to "Quick Sort (Fast)":
```
same 100 models → quick_sort(models, key=lambda m: m["input_price"], reverse=False)

pivot = model at index 50 (price: $1.00)
less    = [all models with price < $1.00]
equal   = [models with price exactly $1.00]
greater = [all models with price > $1.00]
recurse on less + recurse on greater → merge results
```

---

### 11. Binary Search — `dsa/searching.py`

**What it is:** On a sorted list, jumps to the middle. If target is smaller, search left half; if larger, search right half. Repeat until found. O(log n).

**Real usage example:**
Exact model lookup by name. User types "GPT-4o" in search with `method=binary`:
```
sorted_models (alphabetical): [Claude 3.5, DeepSeek V3, Gemini 1.5, GPT-4o, ...]
                                                            ↑ mid = 50
Compare "gpt-4o" vs "gemini 1.5": gpt > gem → search right half
  right half mid = 75: "llama 3"
Compare "gpt-4o" vs "llama 3": gpt < lla → search left half of right
  ...
Found at index 68 in O(log 100) ≈ 7 comparisons (vs linear scan: up to 100)
```

---

### 12. Binary Search Range — `dsa/searching.py`

**What it is:** Uses binary search twice — once to find the leftmost index where price ≥ min, once for rightmost where price ≤ max. Returns everything in between in O(log n + k) time.

**Real usage example:**
User moves price slider to "$0.50 - $3.00":
```
price-sorted models: [$0.00, $0.03, $0.05, ..., $0.50, $1.00, $2.00, $3.00, $5.00, $15.00]

Binary search for leftmost price ≥ 0.50 → index 23
Binary search for rightmost price ≤ 3.00 → index 67
Return models[23:68]  ← all models in that price range, O(log n + k)
```

---

## 🔄 COMPLETE CALL STACKS FOR EACH PAGE

---

### Page 1: Models Directory (Full Call Stack)

```
1. Browser loads localhost:8501
2. app.py runs (Streamlit executes top-to-bottom on each interaction)
3. app.py::page_directory() is called

4. FILTER BAR renders:
   - st.multiselect("AI Lab/Vendor") with provider list from data.get_filter_options()
   - st.slider("Max Price") with currency-converted max value
   - st.selectbox("Min Context") with context tier options

5. SEARCH bar: st.text_input() with key bound to filter_counter

6. QUICK FILTERS: "Cheapest", "Best rated", "Tool calling", etc.
   Each button sets active_filters["preset"] and triggers rerun

7. data.get_models(active_filters, sort, currency) is called:
   → BackendService.get_all_models_for_catalog()
       → db.execute_query(7-table JOIN SQL)  ← MySQL or SQLite
       → returns 100 raw model dicts
   → Python-side filtering loop (12 conditions checked per model)
   → dsa_manager.sort_models() → merge_sort() or quick_sort()
   → Currency conversion loop (multiply all prices by exchange rate)
   → returns formatted list

8. Result count row: "Showing 85 of 100 models"

9. DIRECT COLUMN DSA SORTING toolbar: 6 sort buttons + DSA algorithm selector

10. VIEW: st.dataframe() (Visual Table) or card grid (Cards mode)

11. SIDEBAR: data.get_recently_viewed(session_id) → CircularQueue.to_list()
    Shows up to 10 recently clicked models as buttons
```

---

### Page 2: Compare (Full Call Stack)

```
1. User selects 2-4 models from multiselect dropdown
2. app.py calls data.compare_models([id1, id2, id3], currency)
3. data.py calls BackendService.compare_models(ids)
4. BackendService calls db.call_procedure("sp_compare_models", ids)
5. db.py tries MySQL stored procedure:
   → If MySQL has sp_compare_models: executes it, gets result sets
   → If not: _emulate_procedure_sqlite() runs equivalent Python+SQL
6. Returns for each model:
   - Full specs (context, price, modalities)
   - Benchmark scores (all 6 suites)
   - Capabilities list
   - Average rating
7. data.py runs Winner Detection:
   - Score composite = weighted_avg(benchmarks, price_efficiency, context)
   - model with highest score = winner
8. app.py renders:
   - Side-by-side metric cards (green = better, red = worse)
   - Radar chart (Plotly) showing benchmark profile
   - Price comparison bar chart
   - Monthly cost estimator with token count input
```

---

### Page 3: Leaderboard (Full Call Stack)

```
1. app.py::page_leaderboard()
2. data.get_leaderboard(metric="Chatbot Arena Elo", filters={})
3. BackendService.get_all_benchmarks_for_leaderboard()
4. db.execute_query("""
     SELECT mv.version_id, mv.version_name, p.name AS provider_name,
            ph.input_price_per_1m_tokens AS input_price,
            AVG(ur.rating) AS avg_rating,
            MAX(CASE WHEN b.name = 'AIME 2024' THEN bs.score END) AS aime_2024,
            MAX(CASE WHEN b.name = 'Chatbot Arena Elo' THEN bs.score END) AS chatbot_arena_elo,
            ...
     FROM model_versions mv
     JOIN ... 
     GROUP BY mv.version_id
     ORDER BY chatbot_arena_elo DESC
   """)
5. Returns leaderboard rows (25 models with all benchmark columns)
6. app.py renders:
   - Filter bar (Lab filter + Reasoning-only checkbox)
   - st.dataframe() with column_config for each benchmark
     (each benchmark column has a tooltip explaining what it measures)
```

---

### Page 4: Profile (Full Call Stack)

```
1. User clicks a model name → app.py::page_profile(version_id)
2. data.get_model(version_id, currency)
3. BackendService.get_model_full_profile(version_id):
   7 separate SQL queries run:
   Q1: SELECT mv.*, mf.*, p.* ... WHERE mv.version_id = ?       ← core info
   Q2: SELECT * FROM pricing_history WHERE version_id = ?        ← price history
   Q3: SELECT c.name, mc.proficiency FROM model_capabilities mc  ← capabilities
   Q4: SELECT b.name, bs.score FROM benchmark_scores bs ...      ← benchmarks
   Q5: SELECT t.name FROM model_tags mt JOIN tags t ...          ← tags
   Q6: SELECT uc.name, muc.suitability_score FROM model_use_cases ← use cases
   Q7: SELECT AVG(rating), COUNT(*) FROM user_reviews ...        ← review stats
4. dsa_manager.add_recent_view(session_id, model_summary) → CircularQueue.enqueue()
5. dsa_manager.add_to_browse_history(session_id, model_summary) → DoublyLinkedList.append()
6. app.py renders profile cards:
   - Header: Model name, provider, release date, context window
   - Pricing cards with multi-currency conversion
   - Benchmark radar chart
   - Capability pills
   - Use case suitability cards (score out of 1.00)
   - Incident log (error_reports)
   - Community reviews
```

---

### Page 5: Cost Matcher / Smart Advisor (Full Call Stack)

```
1. User sets: monthly budget = $50, context need = 128K, capabilities = ["Tool Calling"]
2. app.py calls data.get_recommendations(use_case, budget, context, currency)
3. data.py calls db.call_procedure("sp_recommend_model", (use_case, budget_usd, context))
4. MySQL stored proc (or SQLite emulation) runs:
   SELECT mv.version_id, mv.version_name, p.name, muc.suitability_score ...
   FROM model_use_cases muc
   JOIN use_cases uc ON muc.use_case_id = uc.use_case_id
   JOIN model_versions mv ON muc.version_id = mv.version_id
   LEFT JOIN pricing_history ph ON mv.version_id = ph.version_id
   WHERE uc.name LIKE '%Coding%'
     AND ph.input_price_per_1m_tokens <= 0.18   ← budget converted to per-1M
     AND mv.context_length >= 128000
   ORDER BY muc.suitability_score DESC
   LIMIT 10
5. Returns 10 recommended models sorted by suitability
6. dsa_manager.get_top_k_models(candidates, k=5, criteria="rating") 
   → MaxHeap extracts top 5 rated from the 10 candidates → O(10 log 5)
7. app.py renders:
   - Top recommendation card (highlighted)
   - Ranked list of alternatives
   - Monthly cost calculation widget
   - Suitability score displayed as /1.00 (not /5)
```

---

### Page 6: Audit & Incidents (Full Call Stack)

```
1. app.py::page_audit()
2. data.get_incidents(filters)
3. BackendService.get_all_incidents():
   db.execute_query("""
     SELECT er.*, mv.version_name, p.name AS provider_name
     FROM error_reports er
     JOIN model_versions mv ON er.version_id = mv.version_id
     JOIN model_families mf ON mv.family_id = mf.family_id
     JOIN providers p ON mf.provider_id = p.provider_id
     ORDER BY er.created_at DESC
   """)
4. Returns 23 incidents

5. User submits new review:
   data.submit_review(payload)
   → BackendService.submit_review()
   → db.execute_query("INSERT INTO user_reviews ... is_approved=0")
   → MySQL trigger trg_review_rating_check fires automatically
   → dsa_manager.submit_review_for_moderation() → Queue.enqueue()

6. app.py renders:
   - Incident table with severity color badges
   - Review submission form
   - Community reviews list (approved only)
```

---

### Page 7: Analytics (Full Call Stack)

```
1. app.py::page_analytics()
2. User selects report: "Lab Market Share"
3. data.get_analytics("Lab Market Share", filters, currency)
4. BackendService executes SQL:
   SELECT p.name AS provider_name,
          COUNT(mv.version_id) AS model_count,
          ROUND(COUNT(mv.version_id) * 100.0 / SUM(COUNT(mv.version_id)) OVER (), 1) AS share_pct,
          ROUND(AVG(ph.input_price_per_1m_tokens), 4) AS avg_price
   FROM providers p
   JOIN model_families mf ON mf.provider_id = p.provider_id
   JOIN model_versions mv ON mv.family_id = mf.family_id
   LEFT JOIN pricing_history ph ON ph.version_id = mv.version_id
   GROUP BY p.name
   ORDER BY model_count DESC

5. data.py converts avg_price to selected currency
6. app.py renders:
   - 4 KPI metric cards (66 models with 1M+ context, etc.)
   - Plotly horizontal bar chart (models per provider)
   - Plotly pie chart (market share %)
   - Scatter plot (price vs avg rating)
```

---

## 🗃️ DATABASE LAYER: EVERY TABLE AND ITS PURPOSE

### Why 3NF (Third Normal Form)?

**3NF means**: No redundancy. Every non-key column depends only on the primary key, nothing else.

**Bad (un-normalized):**
```
model_data: (model_name, provider_name, provider_country, price_input, price_output)
Problem: If OpenAI changes country, you update EVERY row that mentions OpenAI.
```

**Good (3NF):**
```
providers: (provider_id, name, country)   ← country stored ONCE
model_versions: (version_id, family_id, version_name, ...)  ← links to provider via family_id
pricing_history: (pricing_id, version_id, input_price, output_price, effective_date)
```

### The 17 Tables (Relationships)

```
providers (9 rows)
  └── model_families (11 rows) [provider_id FK]
        └── model_versions (100 rows) [family_id FK]
              ├── pricing_history (100 rows) [version_id FK]
              ├── api_endpoints (100 rows) [version_id FK]
              ├── model_capabilities (464 rows) [version_id + capability_id FK] ← many-to-many
              ├── benchmark_scores (600 rows) [version_id + benchmark_id FK] ← many-to-many
              ├── model_use_cases (373 rows) [version_id + use_case_id FK] ← many-to-many
              ├── model_tags (315 rows) [version_id + tag_id FK] ← many-to-many
              ├── user_reviews (123 rows) [version_id FK]
              ├── error_reports (23 rows) [version_id FK]
              ├── comparison_logs (dynamic) [version_id FK]
              └── search_logs (dynamic) [version_id FK]

capabilities (9 rows)        ← capability definitions
benchmarks (6 rows)          ← benchmark test suite definitions
use_cases (6 rows)           ← enterprise use case definitions
tags (7 rows)                ← classification tag definitions
```

### The 6 Views (Pre-Written JOINs)

| View Name | What It Joins | Used By |
|---|---|---|
| `v_model_full_details` | model_versions + families + providers + latest pricing | Main catalog query |
| `v_top_rated_models` | model_versions + user_reviews (approved only, AVG rating) | Leaderboard rating column |
| `v_free_models` | v_model_full_details WHERE is_free OR price=0 | Free filter preset |
| `v_model_benchmark_summary` | benchmark_scores pivoted by category | Benchmark radar charts |
| `v_provider_statistics` | Aggregates per-provider counts, avg price, avg rating | Analytics page |
| `v_model_comparison_ready` | Everything needed for side-by-side comparison | Compare page |

### The 3 Triggers (Auto-Automation)

| Trigger Name | When It Fires | What It Does |
|---|---|---|
| `trg_validate_pricing` | BEFORE INSERT on pricing_history | Raises SQL error if price < 0 |
| `trg_review_rating_check` | BEFORE INSERT on user_reviews | Trims name whitespace; validates 1 ≤ rating ≤ 5 |
| `trg_error_resolve_timestamp` | BEFORE UPDATE on error_reports | Auto-sets resolved_at = NOW() when status → 'resolved' |

**Trigger example trace:**
```
User submits review with rating=0
  → db.execute_query("INSERT INTO user_reviews ... rating=0")
  → MySQL fires trg_review_rating_check BEFORE the insert
  → trigger checks: IF NEW.rating < 1 OR > 5
  → SIGNAL SQLSTATE '45000' → raises SQL error
  → Python catches exception → returns HTTP 400 to frontend
  → Row is NEVER committed (transaction rolled back)
```

### The 5 Stored Procedures (Pre-compiled SQL Functions)

| Procedure | Arguments | What It Returns |
|---|---|---|
| `sp_recommend_model` | (use_case, max_budget, min_ctx) | Top 10 recommended models |
| `sp_compare_models` | (id1, id2) | Full comparison data for 2 models |
| `sp_get_top_models` | (criteria, limit) | Top N models by given metric |
| `sp_provider_report` | (provider_name) | Full stats + all models for a provider |
| `sp_search_models` | (query, free_only, min_ctx, max_p, capability) | Filtered model search |

### The 16 Indexes (Speed Boosts)

Indexes are like a book's index — they let MySQL jump directly to matching rows instead of scanning all 100 rows.

| Index | Column(s) | Why It Exists |
|---|---|---|
| `idx_mv_family_id` | model_versions.family_id | Every JOIN to model_families uses this |
| `idx_mv_status` | model_versions.status | Filter by active/deprecated models |
| `idx_ph_version_id` | pricing_history.version_id | Pricing lookups use version_id constantly |
| `idx_ph_input_price` | pricing_history.input_price | Price range queries and sorting |
| `idx_ur_version_id` | user_reviews.version_id | Reviews lookups per model |
| `idx_ur_is_approved` | user_reviews.is_approved | Only show approved reviews |
| `idx_bs_version_id` | benchmark_scores.version_id | Benchmark lookups per model |
| `idx_bs_benchmark_id` | benchmark_scores.benchmark_id | Join to benchmarks table |
| `idx_er_version_id` | error_reports.version_id | Incidents per model |
| `idx_er_severity` | error_reports.severity | Filter by high/medium/low severity |
| + 6 more | Various FK columns | Speed up all JOINs |

---

## 🎨 `ui/styles.py` — Visual Design System

**What it does:**
Defines:
1. `CURRENCIES` dict: exchange rates for USD, PKR, EUR, GBP with symbols
2. `format_context(n)`: converts raw number → readable string (131072 → "128K", 1000000 → "1M")
3. `format_country(name)`: "United States" → "US 🇺🇸"
4. `get_css()`: returns a large CSS string applied via `st.markdown(css, unsafe_allow_html=True)`

**The CSS defines:**
- Black background (`#0B0C0A`)
- Acid lime green accents (`#C8F169`)
- Dark card surfaces (`#131512`)
- Sharp borders (`#242722`)
- Font: system-ui stack

**Currency system:**
```python
CURRENCIES = {
    "USD ($)": {"symbol": "$",  "rate": 1.0,   "iso": "USD"},
    "PKR (Rs)": {"symbol": "Rs","rate": 278.5,  "iso": "PKR"},
    "EUR (€)": {"symbol": "€",  "rate": 0.92,  "iso": "EUR"},
    "GBP (£)": {"symbol": "£",  "rate": 0.79,  "iso": "GBP"},
}
# Usage: price_pkr = price_usd * 278.5
```

---

## 📡 `routes/` — REST API Endpoints

### `routes/models.py`
| Endpoint | Method | DSA Used | Purpose |
|---|---|---|---|
| `/api/models/` | GET | Merge/Quick Sort + HashTable cache | Paginated model list |
| `/api/models/autocomplete?q=cl` | GET | Trie | Prefix suggestions |
| `/api/models/search?q=gpt&method=binary` | GET | Binary/Linear/Fuzzy search | Model lookup |
| `/api/models/top?k=5&criteria=price` | GET | Min-Heap / Max-Heap | Top-K models |
| `/api/models/price-range?min=0&max=5` | GET | Binary Search Range | Price window filter |
| `/api/models/{id}` | GET | CircularQueue + DoublyLinkedList | Full model profile |
| `/api/models/` | POST | - | Register new model |
| `/api/models/{id}` | DELETE | Cache clear | Remove model |

### `routes/reviews.py`
| Endpoint | Method | DSA Used | Purpose |
|---|---|---|---|
| `/api/reviews/model/{id}` | GET | - | Get reviews for a model |
| `/api/reviews/` | POST | Queue (FIFO enqueue) | Submit review for moderation |
| `/api/reviews/moderation/next` | GET | Queue (FIFO dequeue) | Get next pending review |
| `/api/reviews/moderation/peek` | GET | Queue (peek) | View next without removing |
| `/api/reviews/moderation/{id}/approve` | PUT | - | Mark review approved |
| `/api/reviews/moderation/{id}/reject` | DELETE | - | Reject review |
| `/api/reviews/errors/model/{id}` | GET | - | Get incidents |
| `/api/reviews/errors` | POST | - | File error report |
| `/api/reviews/errors/{id}/status` | PUT | Trigger fires | Update incident status (triggers auto-timestamp) |

---

## 🔧 `seed_database.py` — Database Population Script

**Run once: `python seed_database.py`**

**Complete 10-step process:**

```
Step 1: Connect to DB (MySQL or SQLite)
Step 2: Create all 17 tables via DDL SQL
Step 3: INSERT 9 providers:
        - OpenAI (US, 2015), Anthropic (US, 2021), Google (US, 1998),
          Meta (US, 2004), Mistral AI (FR, 2023), DeepSeek (CN, 2023),
          Alibaba Qwen (CN, 2009), xAI (US, 2023), Cohere (CA, 2019)
Step 4: INSERT 6 benchmark definitions with max scores and descriptions
Step 5: INSERT 9 capability definitions
Step 6: READ model_catalog.json (100 models) →
        For each model:
          → INSERT model_families row (grouped by provider + family name)
          → INSERT model_versions row (name, context, flags, description)
          → INSERT pricing_history row (input + output price, effective_date)
          → INSERT api_endpoints row (base URL, auth type, rate limit)
Step 7: For each model version:
          → Link capabilities (Tool Calling, Reasoning, Vision, Coding based on flags)
Step 8: For each model version:
          → INSERT 6 benchmark_scores rows (realistic scores based on model family/size)
Step 9: INSERT 123 user_reviews (mix of approved + pending)
        INSERT 23 error_reports (open + resolved incidents)
Step 10: Link use_cases + tags to all models with suitability scores
```

---

## 🧪 `test_data.py` — Verification Test Suite

**Run with: `python -u test_data.py`**

11 tests that verify the entire data layer works correctly:

| Test # | What It Tests | Assertion |
|---|---|---|
| 1 | `convert_price()` | PKR > USD price, EUR < USD price |
| 2 | `get_kpis()` | Returns 100 models, 9 providers, avg price |
| 3 | `get_models()` | All=100, Claude=12, Anthropic=12, Tools=90, Cheap=55 |
| 4 | `get_model(1)` | Returns full profile with ≥1 capability |
| 5 | `compare_models([1,2,3,4])` | Returns winner, all 4 compared |
| 6 | `get_leaderboard(all metrics)` | Each metric returns exactly 25 models |
| 7 | `get_recommendations()` | Returns 10 candidates |
| 8 | `get_incidents() + get_reviews()` | 23 incidents, 122 reviews |
| 9 | `get_analytics_report()` | 20 rows returned, 17 tables verified |
| 10 | `search("")` → 100; `search("c")` → 25 | Trie search + prefix ranking |
| 11 | `get_all_benchmarks_matrix()` | 100 models × 10 benchmark suites verified |

---

## 🏁 STARTUP SEQUENCE (What Happens When You Run the App)

```
1. python seed_database.py      ← Run ONCE to populate database
2. uvicorn main:app --port 8000 ← Start FastAPI (optional, for API access)
3. streamlit run app.py         ← Start Streamlit frontend

On streamlit startup:
  → Python imports: app.py imports data.py imports services.dsa_manager
  → dsa_manager = DSAManager() is created: empty Trie, empty Hash Table, etc.
  → Streamlit renders initial UI

On FastAPI startup (main.py lifespan):
  → execute_query(SELECT all 100 models) → DB query
  → dsa_manager.build_autocomplete(100 models) → 200 words inserted into Trie
  → dsa_manager.build_sorted_index(100 models) → sorted array for binary search
  → Swagger docs available at localhost:8000/docs

On first user browser hit to localhost:8501:
  → st.session_state initialized with DEFAULT_FILTERS
  → session_id generated (UUID)
  → page_directory() renders with Showing 100 of 100 models (no filters active)
```

---

> **Summary**: The project is a layered system: Streamlit UI ↔ data.py ↔ services ↔ db.py ↔ MySQL. DSA structures live in memory via dsa_manager (a singleton). Data entered the DB from API JSON via seed_database.py. Reviews come from both the seed script (synthetic) and live user submissions. See the database visually via MySQL Workbench, DBeaver, or SQLite Browser.
