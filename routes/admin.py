"""
Admin & Architectural Diagnostic Routes.

Provides:
- Complete database metrics (17 table row counts)
- In-memory DSA metrics (Trie size, Cache entries, Heap/Queue depths)
- Rebuilding in-memory data structures from live database
- Formal educational summaries of all DBMS & DSA implementations
"""
from fastapi import APIRouter
from db import execute_query, get_db_mode
from services.dsa_manager import dsa_manager

router = APIRouter(prefix="/api/admin", tags=["Admin & Diagnostics"])


@router.get("/stats")
def database_statistics():
    """Count records across all 17 database tables."""
    tables = [
        "providers", "model_families", "model_versions", "pricing_history",
        "capabilities", "model_capabilities", "benchmarks", "benchmark_scores",
        "use_cases", "model_use_cases", "tags", "model_tags",
        "user_reviews", "error_reports", "comparison_logs", "search_logs", "api_endpoints"
    ]
    counts = {}
    for table in tables:
        try:
            res = execute_query(f"SELECT COUNT(*) AS count FROM {table}", fetch_one=True)
            counts[table] = res.get("count", 0) if res else 0
        except Exception:
            counts[table] = 0

    return {
        "database_backend": get_db_mode(),
        "total_tables": len(tables),
        "table_row_counts": counts,
        "grand_total_rows": sum(counts.values()),
    }


@router.get("/cache/stats")
def cache_statistics():
    """Inspect state of all in-memory DSA data structures."""
    return {
        "hash_table_cache": {
            "active_cached_queries": dsa_manager.query_cache.size(),
            "bucket_capacity": dsa_manager.query_cache.capacity,
            "active_keys": dsa_manager.query_cache.keys()[:10],
        },
        "trie_prefix_tree": {
            "total_words_indexed": len(dsa_manager.autocomplete_trie),
        },
        "moderation_queue": {
            "pending_reviews_fifo": dsa_manager.pending_reviews_count(),
        },
        "sorted_models_index": {
            "models_available_for_binary_search": len(dsa_manager._sorted_models),
        },
    }


@router.post("/cache/clear")
def clear_cache():
    """Flush the HashTable cache."""
    dsa_manager.cache_clear()
    return {"message": "In-memory Hash Table cache flushed successfully"}


@router.post("/rebuild-indexes")
def rebuild_in_memory_indexes():
    """Reload all models from database into Trie and Binary Search sorted index."""
    models = execute_query("""
        SELECT mv.version_id, mv.version_name, mv.context_length, mv.is_free,
               mf.name AS family_name, p.name AS provider_name,
               ph.input_price_per_1m_tokens
        FROM model_versions mv
        JOIN model_families mf ON mv.family_id = mf.family_id
        JOIN providers p ON mf.provider_id = p.provider_id
        LEFT JOIN pricing_history ph ON mv.version_id = ph.version_id
    """)

    dsa_manager.build_autocomplete(models)
    dsa_manager.build_sorted_index(models)

    return {
        "message": "DSA structures rebuilt from database successfully",
        "trie_entries": len(dsa_manager.autocomplete_trie),
        "sorted_models": len(dsa_manager._sorted_models),
    }


@router.get("/dsa-summary")
def dsa_architecture_summary():
    """Complete academic reference of all DSA structures implemented in this backend."""
    return {
        "title": "Data Structures & Algorithms Applied in AI Model Registry",
        "total_dsa_implementations": 12,
        "implementations": [
            {
                "data_structure": "Trie (Prefix Tree)",
                "module": "dsa/trie.py",
                "usage": "Instant model name autocomplete",
                "time_complexity": "Insert O(L), Prefix Search O(P + K)",
                "live_endpoint": "GET /api/models/autocomplete?q=gpt"
            },
            {
                "data_structure": "Hash Table (Separate Chaining)",
                "module": "dsa/hash_table.py",
                "usage": "Query result caching with TTL expiration",
                "time_complexity": "Average O(1) Get/Put",
                "live_endpoint": "GET /api/admin/cache/stats"
            },
            {
                "data_structure": "Stack (LIFO)",
                "module": "dsa/stack.py",
                "usage": "Multi-level search filter undo system",
                "time_complexity": "O(1) Push/Pop",
                "live_endpoint": "POST /api/search/filters/undo"
            },
            {
                "data_structure": "Queue (FIFO)",
                "module": "dsa/queue_ds.py",
                "usage": "User review moderation workflow",
                "time_complexity": "O(1) Enqueue/Dequeue",
                "live_endpoint": "GET /api/reviews/moderation/next"
            },
            {
                "data_structure": "Circular Queue (Ring Buffer)",
                "module": "dsa/circular_queue.py",
                "usage": "Fixed-capacity buffer of 10 recently viewed models",
                "time_complexity": "O(1) Enqueue with oldest overwrite",
                "live_endpoint": "GET /api/search/recently-viewed"
            },
            {
                "data_structure": "Singly Linked List",
                "module": "dsa/linked_list.py",
                "usage": "Sequential search query history tracking",
                "time_complexity": "O(1) Append, O(n) Traversal",
                "live_endpoint": "GET /api/search/history"
            },
            {
                "data_structure": "Doubly Linked List",
                "module": "dsa/doubly_linked_list.py",
                "usage": "Browser-style forward/backward model navigation",
                "time_complexity": "O(1) Move Forward/Backward",
                "live_endpoint": "POST /api/search/browse/forward"
            },
            {
                "data_structure": "Min-Heap / Max-Heap",
                "module": "dsa/priority_queue.py",
                "usage": "Top-K model extraction (cheapest / highest rated)",
                "time_complexity": "O(n log k) build & extract",
                "live_endpoint": "GET /api/models/top?k=5&criteria=price"
            },
            {
                "data_structure": "Merge Sort",
                "module": "dsa/sorting.py",
                "usage": "Stable multi-criteria model sorting",
                "time_complexity": "O(n log n) Guaranteed Time, O(n) Space",
                "live_endpoint": "GET /api/models/?algorithm=merge"
            },
            {
                "data_structure": "Quick Sort",
                "module": "dsa/sorting.py",
                "usage": "Fast partitioning-based sorting",
                "time_complexity": "O(n log n) Average Time",
                "live_endpoint": "GET /api/models/?algorithm=quick"
            },
            {
                "data_structure": "Binary Search",
                "module": "dsa/searching.py",
                "usage": "Exact model name lookup on sorted array",
                "time_complexity": "O(log n)",
                "live_endpoint": "GET /api/models/search?method=binary&q=claude"
            },
            {
                "data_structure": "Binary Search Range",
                "module": "dsa/searching.py",
                "usage": "Filtering models in continuous pricing intervals",
                "time_complexity": "O(log n + k)",
                "live_endpoint": "GET /api/models/price-range?min_price=1&max_price=10"
            }
        ]
    }


@router.get("/dbms-summary")
def dbms_architecture_summary():
    """Complete academic reference of all DBMS concepts implemented in this project."""
    return {
        "title": "Database Management System (DBMS) Concepts Implemented",
        "concepts": [
            {
                "concept": "17 Relational Tables (3NF)",
                "description": "Normalized relational schema eliminating data redundancy and update anomalies"
            },
            {
                "concept": "Referential Integrity & Foreign Keys",
                "description": "ON DELETE CASCADE on junction tables, ON DELETE SET NULL on recursive parent_version_id"
            },
            {
                "concept": "Domain Constraints",
                "description": "CHECK constraints on rating (1-5), years (1900-2100), suitability (0.00-1.00), ENUM statuses"
            },
            {
                "concept": "6 Pre-computed Views",
                "description": "v_model_full_details, v_top_rated_models, v_free_models, v_model_benchmark_summary, v_provider_statistics, v_model_comparison_ready"
            },
            {
                "concept": "3 Active Database Triggers",
                "description": "trg_validate_pricing, trg_review_rating_check, trg_error_resolve_timestamp"
            },
            {
                "concept": "5 Stored Procedures",
                "description": "sp_search_models, sp_compare_models, sp_get_top_models, sp_recommend_model, sp_provider_report"
            },
            {
                "concept": "16+ Performance Indexes",
                "description": "B-Tree indexes on search keys, foreign keys, and dates; FULLTEXT index on name and description"
            },
            {
                "concept": "ACID Compliance & Connection Pooling",
                "description": "Connection pool management with automatic session recycling and transaction rollbacks"
            }
        ]
    }
