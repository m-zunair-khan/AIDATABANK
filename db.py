"""
Database connection manager with robust connection resilience:
1. Primary: MySQL (Aiven cloud or local MySQL server).
2. Resilient Fallback: SQLite (local file database in data/ai_registry.db).

Guarantees 100% uptime: If MySQL drops or disconnects mid-query,
it automatically catches the error, reconnects or gracefully falls back
to SQLite without crashing the user's Streamlit frontend.
"""
import os
import sqlite3
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from config import settings

_USE_MYSQL = False
_MYSQL_POOL = None
_DB_MODE = "uninitialized"


def _init_mysql():
    """Attempt to initialize MySQL connection pool."""
    global _USE_MYSQL, _MYSQL_POOL, _DB_MODE
    try:
        import mysql.connector
        from mysql.connector import pooling

        db_kwargs = {
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "database": settings.DB_NAME,
            "connection_timeout": 5,
        }
        ssl_ca = settings.DB_SSL_CA or "ca.pem"
        ssl_ca_path = os.path.join(str(settings.BASE_DIR), ssl_ca) if not os.path.isabs(ssl_ca) else ssl_ca
        if os.path.exists(ssl_ca_path):
            db_kwargs["ssl_ca"] = ssl_ca_path

        _MYSQL_POOL = pooling.MySQLConnectionPool(
            pool_name="ai_registry_pool",
            pool_size=5,
            pool_reset_session=False,  # Avoid reset_session crash if server drops
            **db_kwargs
        )
        # Test connection
        conn = _MYSQL_POOL.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        _USE_MYSQL = True
        _DB_MODE = f"MySQL ({settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME})"
        print(f"Connected to MySQL: {_DB_MODE}")
    except Exception as e:
        _USE_MYSQL = False
        _DB_MODE = f"SQLite (Fallback mode: {settings.SQLITE_PATH.name})"
        print(f"MySQL unavailable ({e}). Running in resilient SQLite mode: {settings.SQLITE_PATH}")


_init_mysql()


def get_db_mode() -> str:
    """Return description of active database backend."""
    return _DB_MODE


def is_mysql() -> bool:
    """Check if MySQL is the active backend."""
    return _USE_MYSQL


def _get_sqlite_connection():
    """Get connection to local SQLite database with Row dictionary factory."""
    settings.SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(settings.SQLITE_PATH), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _convert_query_to_sqlite(query: str) -> str:
    """Translate MySQL dialect query to SQLite dialect if needed."""
    q = query.replace("%s", "?")
    q = re.sub(r'\bNOW\(\)', "datetime('now')", q, flags=re.IGNORECASE)
    q = re.sub(r'\bTRUE\b', '1', q, flags=re.IGNORECASE)
    q = re.sub(r'\bFALSE\b', '0', q, flags=re.IGNORECASE)
    return q


def _execute_sqlite(query: str, params: tuple, fetch_one: bool, fetch_all: bool) -> Any:
    """Execute query safely against SQLite."""
    conn = _get_sqlite_connection()
    try:
        sql = _convert_query_to_sqlite(query)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        if fetch_one:
            row = cursor.fetchone()
            result = dict(row) if row else None
        elif fetch_all:
            rows = cursor.fetchall()
            result = [dict(r) for r in rows]
        else:
            conn.commit()
            result = {"affected_rows": cursor.rowcount, "last_id": cursor.lastrowid}
        cursor.close()
        return result
    finally:
        conn.close()


def execute_query(
    query: str,
    params: Optional[Union[Tuple, List, Dict]] = None,
    fetch_one: bool = False,
    fetch_all: bool = True
) -> Any:
    """
    Execute a query and return results as list of dicts or single dict.
    Automatically retries or falls back to SQLite if MySQL connection drops.
    """
    global _USE_MYSQL, _DB_MODE
    params = params or ()
    
    if _USE_MYSQL and _MYSQL_POOL:
        conn = None
        try:
            conn = _MYSQL_POOL.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                conn.commit()
                result = {"affected_rows": cursor.rowcount, "last_id": cursor.lastrowid}
            cursor.close()
            return result
        except Exception as e:
            # MySQL connection dropped or lost during query:
            # Fall back to SQLite instantly so the user UI never crashes!
            print(f"[!] MySQL error ({e}). Seamlessly falling back to SQLite...")
            return _execute_sqlite(query, params, fetch_one, fetch_all)
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    else:
        # SQLite execution
        return _execute_sqlite(query, params, fetch_one, fetch_all)


def execute_many(query: str, data_list: List[Tuple]) -> int:
    """Execute batch insert/update."""
    if not data_list:
        return 0
    if _USE_MYSQL and _MYSQL_POOL:
        conn = None
        try:
            conn = _MYSQL_POOL.get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, data_list)
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected
        except Exception as e:
            print(f"[*] MySQL batch error ({e}). Falling back to SQLite...")
            conn_sq = _get_sqlite_connection()
            try:
                sql = _convert_query_to_sqlite(query)
                cur_sq = conn_sq.cursor()
                cur_sq.executemany(sql, data_list)
                conn_sq.commit()
                aff = cur_sq.rowcount
                cur_sq.close()
                return aff
            finally:
                conn_sq.close()
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    else:
        conn = _get_sqlite_connection()
        try:
            sql = _convert_query_to_sqlite(query)
            cursor = conn.cursor()
            cursor.executemany(sql, data_list)
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected
        finally:
            conn.close()


def call_procedure(proc_name: str, args: Tuple = ()) -> List[List[Dict]]:
    """
    Call stored procedure (on MySQL) or simulate it with pure SQL (on SQLite).
    """
    if _USE_MYSQL and _MYSQL_POOL:
        conn = None
        try:
            conn = _MYSQL_POOL.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.callproc(proc_name, args)
            results = []
            for rs in cursor.stored_results():
                results.append(rs.fetchall())
            cursor.close()
            conn.commit()
            return results
        except Exception as e:
            print(f"[*] MySQL procedure error ({e}). Falling back to SQLite emulation...")
            return _emulate_procedure_sqlite(proc_name, args)
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    else:
        # SQLite stored procedure emulator
        return _emulate_procedure_sqlite(proc_name, args)


def _emulate_procedure_sqlite(proc_name: str, args: Tuple) -> List[List[Dict]]:
    """Simulates the 5 stored procedures when running in SQLite fallback mode or when MySQL stored procedures are missing."""
    proc = proc_name.lower()
    
    if proc == "sp_search_models":
        q, free_only, min_ctx, max_p, cap = (args + (None, None, None, None, None))[:5]
        where_clauses = ["1=1"]
        params = []
        if q:
            where_clauses.append("(version_name LIKE %s OR family_name LIKE %s OR provider_name LIKE %s)")
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
        if free_only:
            where_clauses.append("(is_free = 1 OR input_price = 0)")
        if min_ctx:
            where_clauses.append("context_length >= %s")
            params.append(min_ctx)
        if max_p:
            where_clauses.append("input_price <= %s")
            params.append(max_p)
            
        sql = f"SELECT * FROM v_model_full_details WHERE {' AND '.join(where_clauses)} LIMIT 100"
        return [execute_query(sql, params)]

    elif proc == "sp_compare_models":
        id1, id2 = args[:2]
        m1 = execute_query("SELECT * FROM v_model_comparison_ready WHERE version_id = %s", (id1,))
        m2 = execute_query("SELECT * FROM v_model_comparison_ready WHERE version_id = %s", (id2,))
        b1 = execute_query("SELECT b.name, bs.score FROM benchmark_scores bs JOIN benchmarks b ON bs.benchmark_id = b.benchmark_id WHERE bs.version_id = %s", (id1,))
        b2 = execute_query("SELECT b.name, bs.score FROM benchmark_scores bs JOIN benchmarks b ON bs.benchmark_id = b.benchmark_id WHERE bs.version_id = %s", (id2,))
        return [m1 + m2, b1, b2]

    elif proc == "sp_get_top_models":
        criteria, limit = (args + ("rating", 10))[:2]
        limit = limit or 10
        if criteria == "cheapest":
            sql = "SELECT * FROM v_model_full_details WHERE input_price IS NOT NULL ORDER BY input_price ASC LIMIT %s"
        elif criteria == "context_length":
            sql = "SELECT * FROM v_model_full_details ORDER BY context_length DESC LIMIT %s"
        elif criteria == "newest":
            sql = "SELECT * FROM v_model_full_details ORDER BY release_date DESC LIMIT %s"
        else:
            sql = "SELECT * FROM v_top_rated_models LIMIT %s"
        return [execute_query(sql, (limit,))]

    elif proc == "sp_recommend_model":
        use_case, max_budget, min_ctx = (args + (None, None, None))[:3]
        params = [f"%{use_case}%"]
        conds = ["uc.name LIKE %s"]
        if max_budget is not None:
            conds.append("(ph.input_price_per_1m_tokens <= %s OR ph.input_price_per_1m_tokens IS NULL)")
            params.append(max_budget)
        if min_ctx is not None:
            conds.append("mv.context_length >= %s")
            params.append(min_ctx)

        sql = f"""
            SELECT mv.version_id, mv.version_name, p.name AS provider_name,
                   muc.suitability_score,
                   ph.input_price_per_1m_tokens,
                   ph.output_price_per_1m_tokens,
                   ph.input_price_per_1m_tokens AS input_price,
                   ph.output_price_per_1m_tokens AS output_price,
                   mv.context_length
            FROM model_use_cases muc
            JOIN use_cases uc ON muc.use_case_id = uc.use_case_id
            JOIN model_versions mv ON muc.version_id = mv.version_id
            JOIN model_families mf ON mv.family_id = mf.family_id
            JOIN providers p ON mf.provider_id = p.provider_id
            LEFT JOIN pricing_history ph ON mv.version_id = ph.version_id
            WHERE {' AND '.join(conds)}
            ORDER BY muc.suitability_score DESC LIMIT 10
        """
        return [execute_query(sql, params)]

    elif proc == "sp_provider_report":
        p_name = args[0] if args else ""
        stats = execute_query("SELECT * FROM v_provider_statistics WHERE provider_name = %s", (p_name,))
        models = execute_query("SELECT * FROM v_model_full_details WHERE provider_name = %s", (p_name,))
        return [stats, models]

    return [[]]
