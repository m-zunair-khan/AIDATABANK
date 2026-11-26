"""
AI Model Registry — Enterprise Backend API
==========================================
Unified DBMS + DSA Engine for evaluating, benchmarking, searching,
and managing frontier Artificial Intelligence models.

Features:
- Full Database Management System: 17 Normalized Tables, 6 Views, 3 Triggers, 5 Stored Procedures, 16+ Indexes.
- 12 Custom Data Structures & Algorithms: Trie, Separate-Chaining HashTable, Stack, Queue, CircularQueue,
  Singly & Doubly LinkedLists, Min/Max Heap Priority Queues, Merge/Quick Sorts, Binary/Fuzzy Searches.
- Complete OpenAPI (Swagger) Documentation for frontend integration.

Run server:
    uvicorn main:app --reload --port 8000
Interactive Docs:
    http://localhost:8000/docs
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from db import execute_query, get_db_mode
from services.dsa_manager import dsa_manager
from routes import models, providers, benchmarks, reviews, compare, search, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup: Pre-load models into in-memory Trie and sorted array."""
    print("=" * 65)
    print("[*] Initializing AI Model Registry Backend & DSA Engine...")
    print(f"[*] Active Database: {get_db_mode()}")
    try:
        all_models = execute_query("""
            SELECT mv.version_id, mv.version_name, mv.context_length, mv.is_free,
                   mf.name AS family_name, p.name AS provider_name,
                   ph.input_price_per_1m_tokens
            FROM model_versions mv
            JOIN model_families mf ON mv.family_id = mf.family_id
            JOIN providers p ON mf.provider_id = p.provider_id
            LEFT JOIN pricing_history ph ON mv.version_id = ph.version_id
        """)
        dsa_manager.build_autocomplete(all_models)
        dsa_manager.build_sorted_index(all_models)
        print(f"[+] Loaded {len(all_models)} models into Prefix Trie & Sorted Index")
        print(f"[+] Interactive Swagger API Docs ready at: http://localhost:8000/docs")
    except Exception as e:
        print(f"[!] Notice: DB data not yet seeded or reachable: {e}")
        print("[!] Run 'python seed_database.py' to populate tables with 100+ models.")
    print("=" * 65)

    yield

    print("[*] AI Model Registry API shutting down gracefully.")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable Cross-Origin Resource Sharing (CORS) for your friend's frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(models.router)
app.include_router(providers.router)
app.include_router(benchmarks.router)
app.include_router(reviews.router)
app.include_router(compare.router)
app.include_router(search.router)
app.include_router(admin.router)


@app.get("/", tags=["Overview"])
def root():
    """System Overview & Architecture Directory."""
    return {
        "project": "AI Model Registry — DBMS + DSA Backend",
        "version": settings.API_VERSION,
        "database_backend": get_db_mode(),
        "api_documentation": "/docs",
        "redoc_documentation": "/redoc",
        "endpoints": {
            "models_catalog": "/api/models",
            "models_autocomplete": "/api/models/autocomplete?q=gpt",
            "models_top_k": "/api/models/top?k=5&criteria=price",
            "models_price_range": "/api/models/price-range?min_price=0&max_price=5",
            "providers_directory": "/api/providers",
            "benchmarks_leaderboard": "/api/benchmarks/leaderboard",
            "model_comparison": "/api/compare?ids=1,2,3",
            "model_recommendation": "/api/compare/recommend?use_case=Coding",
            "advanced_search": "/api/search/advanced?q=claude",
            "filter_undo_stack": "/api/search/filters/undo",
            "moderation_queue": "/api/reviews/moderation/next",
            "recently_viewed_ring_buffer": "/api/search/recently-viewed",
            "dsa_academic_summary": "/api/admin/dsa-summary",
            "dbms_academic_summary": "/api/admin/dbms-summary",
            "system_health": "/health",
        },
        "dbms_specification": {
            "tables": 17,
            "views": 6,
            "triggers": 3,
            "stored_procedures": 5,
            "indexes": 16,
            "normal_form": "3NF"
        },
        "dsa_specification": {
            "implemented_structures": [
                "Trie (Prefix Tree)",
                "Hash Table (Separate Chaining)",
                "Stack (Filter Undo)",
                "Queue (FIFO Moderation)",
                "Circular Queue (Recently Viewed Ring Buffer)",
                "Singly Linked List (Search History)",
                "Doubly Linked List (Browse History)",
                "Min-Heap / Max-Heap (Top-K Models)",
                "Merge Sort (Stable Multi-criteria)",
                "Quick Sort (Partitioning)",
                "Binary Search (Exact Lookup)",
                "Binary Search Range (Interval Lookup)"
            ]
        }
    }


@app.get("/health", tags=["Overview"])
def health_check():
    """Verify backend and database connectivity."""
    try:
        execute_query("SELECT 1 AS status", fetch_one=True)
        return {
            "status": "healthy",
            "database_backend": get_db_mode(),
            "in_memory_dsa": "active"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "database_error": str(e),
            "database_backend": get_db_mode()
        }
