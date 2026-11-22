import os
import time
import asyncio
import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from backend.app.main import lifespan, _sync_startup_database
from backend.app.database import is_postgres_active
from backend.app.config import settings

def test_startup_successful_normal_mode():
    """Verify standard startup completes lifespan without error."""
    async def run():
        app = FastAPI(lifespan=lifespan)
        async with lifespan(app):
            assert True
    asyncio.run(run())

def test_startup_timeout_enforcement_strict_mode():
    """Verify that if DB startup blocks, strict mode raises RuntimeError promptly within timeout."""
    def blocking_sync_db():
        time.sleep(5.0)  # Simulates hanging socket/deadlock
    
    async def run():
        with patch.dict(os.environ, {
            "REQUIRE_POSTGRES": "true",
            "STARTUP_TIMEOUT_SECONDS": "0.3"
        }):
            with patch("backend.app.main._sync_startup_database", side_effect=blocking_sync_db):
                app = FastAPI(lifespan=lifespan)
                start_t = time.time()
                with pytest.raises(RuntimeError) as exc_info:
                    async with lifespan(app):
                        pass
                elapsed = time.time() - start_t
                assert elapsed < 2.0  # Must fail promptly, never hanging
                assert "database startup timed out" in str(exc_info.value).lower()
    asyncio.run(run())

def test_startup_timeout_fallback_non_strict():
    """Verify that if DB startup blocks, non-strict mode falls back to SQLite and completes."""
    def slow_failing_db():
        time.sleep(0.4)
        raise TimeoutError("Simulated slow pooler timeout")

    async def run():
        with patch.dict(os.environ, {
            "REQUIRE_POSTGRES": "false",
            "STARTUP_TIMEOUT_SECONDS": "0.2"
        }):
            with patch("backend.app.main._sync_startup_database", side_effect=slow_failing_db):
                app = FastAPI(lifespan=lifespan)
                start_t = time.time()
                async with lifespan(app):
                    assert True
                elapsed = time.time() - start_t
                assert elapsed < 2.0
    asyncio.run(run())

def test_strict_postgres_auth_failure_raises_promptly():
    """Verify REQUIRE_POSTGRES=true raises RuntimeError promptly on auth error."""
    async def run():
        with patch.dict(os.environ, {
            "REQUIRE_POSTGRES": "true",
            "STARTUP_TIMEOUT_SECONDS": "5.0"
        }):
            with patch("backend.app.main.is_postgres_active", return_value=False):
                with patch("backend.app.main.init_postgres_pool"):
                    with patch("backend.app.main.get_database_status", return_value={
                        "connection_diagnostics": {
                            "failure_category": "AUTH_FAILED",
                            "last_error": "FATAL: password authentication failed for user \"postgres\""
                        }
                    }):
                        app = FastAPI(lifespan=lifespan)
                        with pytest.raises(RuntimeError) as exc_info:
                            async with lifespan(app):
                                pass
                        err_msg = str(exc_info.value)
                        assert "FATAL: REQUIRE_POSTGRES is true" in err_msg
                        assert "AUTH_FAILED" in err_msg
    asyncio.run(run())

def test_is_postgres_active_helper():
    """Verify is_postgres_active accurately checks both USE_POSTGRES and pg_pool."""
    with patch("backend.app.database.USE_POSTGRES", False), patch("backend.app.database.pg_pool", None):
        assert is_postgres_active() is False

    with patch("backend.app.database.USE_POSTGRES", True), patch("backend.app.database.pg_pool", None):
        assert is_postgres_active() is False

    with patch("backend.app.database.USE_POSTGRES", True), patch("backend.app.database.pg_pool", MagicMock()):
        assert is_postgres_active() is True
