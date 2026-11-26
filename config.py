"""
Configuration management for AI Model Registry.
Loads settings from .env file or environment variables.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except Exception:
    pass


def _get_setting(key: str, default: str = "") -> str:
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default


class Settings:
    BASE_DIR: Path = BASE_DIR
    DB_HOST: str = _get_setting("DB_HOST", "localhost")
    DB_PORT: int = int(_get_setting("DB_PORT", "3306"))
    DB_USER: str = _get_setting("DB_USER", "root")
    DB_PASSWORD: str = _get_setting("DB_PASSWORD", "")
    DB_NAME: str = _get_setting("DB_NAME", "defaultdb")
    DB_SSL_CA: str = _get_setting("DB_SSL_CA", "")
    
    # SQLite fallback file path if cloud MySQL is unreachable
    SQLITE_PATH: Path = BASE_DIR / "data" / "ai_registry.db"
    
    API_TITLE: str = "AI Model Registry API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = (
        "Enterprise-grade Database Management & Data Structures Backend "
        "for searching, evaluating, comparing, and benchmarking AI models."
    )
    
    # DSA configurations
    CACHE_CAPACITY: int = 128
    CACHE_TTL: int = 300  # 5 minutes
    RECENT_VIEWS_CAPACITY: int = 10


settings = Settings()
