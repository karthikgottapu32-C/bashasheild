import os
import pytest
from unittest.mock import patch, MagicMock
from backend.app.database import (
    parse_postgres_dsn,
    _sanitize_error,
    _classify_pg_error,
    get_database_status,
    init_postgres_pool
)
from backend.app.config import settings

def test_parse_postgres_dsn_supabase_session_pooler():
    """Verify parsing of Supabase Session Pooler URL with project-scoped username."""
    url = "postgresql://postgres.abcdefghijklmnop:MySuperSecret123!@aws-1-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require"
    parsed = parse_postgres_dsn(url)
    assert bool(parsed) is True
    assert parsed["user"] == "postgres.abcdefghijklmnop"
    assert parsed["password"] == "MySuperSecret123!"
    assert parsed["host"] == "aws-1-ap-south-1.pooler.supabase.com"
    assert parsed["port"] == 5432
    assert parsed["dbname"] == "postgres"
    assert parsed["sslmode"] == "require"

def test_parse_postgres_dsn_percent_encoded_password():
    """Verify parsing and decoding of percent-encoded passwords with special characters."""
    url = "postgres://postgres.abcdef:P%40ssw0rd%2399%25!@aws-1-ap-south-1.pooler.supabase.com:5432/postgres"
    parsed = parse_postgres_dsn(url)
    assert bool(parsed) is True
    assert parsed["user"] == "postgres.abcdef"
    assert parsed["password"] == "P@ssw0rd#99%!"
    assert parsed["raw_password"] == "P%40ssw0rd%2399%25!"
    assert parsed["host"] == "aws-1-ap-south-1.pooler.supabase.com"
    assert parsed["port"] == 5432
    assert parsed["dbname"] == "postgres"

def test_parse_postgres_dsn_unquoted_special_characters():
    """Verify regex fallback handles unquoted special chars (@, :, #) in password."""
    url = "postgresql://postgres.myproject:pass@word:123#xyz@aws-1-ap-south-1.pooler.supabase.com:5432/postgres"
    parsed = parse_postgres_dsn(url)
    assert bool(parsed) is True
    assert parsed["user"] == "postgres.myproject"
    assert parsed["password"] == "pass@word:123#xyz"
    assert parsed["host"] == "aws-1-ap-south-1.pooler.supabase.com"
    assert parsed["port"] == 5432

def test_parse_postgres_dsn_quoted_and_whitespace():
    """Verify surrounding quotes or leading/trailing whitespace in env var are cleaned."""
    url = "  'postgresql://postgres.xyz:secretpass@aws-1-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require'  "
    parsed = parse_postgres_dsn(url)
    assert bool(parsed) is True
    assert parsed["user"] == "postgres.xyz"
    assert parsed["password"] == "secretpass"
    assert parsed["host"] == "aws-1-ap-south-1.pooler.supabase.com"

def test_parse_postgres_dsn_invalid():
    """Verify invalid format returns empty dict."""
    assert not parse_postgres_dsn("")
    assert not parse_postgres_dsn("not_a_valid_url")
    assert not parse_postgres_dsn("http://localhost:8000")

def test_sanitize_error_strips_passwords():
    """Ensure error messages never leak raw credentials or passwords."""
    raw_error = 'connection to "postgresql://postgres:MySecretPassword123@db.supabase.com:5432/postgres" failed: FATAL: password authentication failed'
    sanitized = _sanitize_error(raw_error)
    assert "MySecretPassword123" not in sanitized
    assert "***" in sanitized

def test_classify_pg_error_categories():
    """Ensure various PostgreSQL error messages are categorized accurately."""
    assert _classify_pg_error('FATAL: password authentication failed for user "postgres"') == "AUTH_FAILED"
    assert _classify_pg_error('could not translate host name "foo.bar" to address') == "DNS_RESOLUTION_FAILED"
    assert _classify_pg_error('connection to server at "1.2.3.4" failed: Connection timed out') == "CONNECT_TIMEOUT"
    assert _classify_pg_error('connection to server at "1.2.3.4" failed: Connection refused') == "CONNECTION_REFUSED"
    assert _classify_pg_error('SSL connection has been closed unexpectedly') == "SSL_ERROR"
    assert _classify_pg_error('unknown miscellaneous error') == "CONNECTION_ERROR"

def test_get_database_status_structure_and_no_leakage():
    """Ensure get_database_status returns diagnostic details without leaking password."""
    status = get_database_status()
    assert "backend" in status
    assert "status" in status
    assert "connection_diagnostics" in status
    
    diag = status["connection_diagnostics"]
    assert "password" not in diag
    assert "has_password" in diag
    assert "failure_category" in diag
    assert "host" in diag
    assert "port" in diag
    assert "user" in diag

@patch("psycopg2.pool.ThreadedConnectionPool")
def test_strict_postgres_requirement_enforcement(mock_pool):
    """Ensure REQUIRE_POSTGRES=true raises RuntimeError on pool initialization failure."""
    mock_pool.side_effect = Exception('FATAL: password authentication failed for user "postgres"')
    
    with patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://postgres:wrong_password@aws-1-ap-south-1.pooler.supabase.com:5432/postgres",
        "REQUIRE_POSTGRES": "true"
    }):
        with pytest.raises(RuntimeError) as exc_info:
            init_postgres_pool()
        assert "Strict PostgreSQL requirement failed on startup" in str(exc_info.value)
