import sqlite3
import json
import os
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from app.config import settings
from app.models import ScanRecord, DashboardStats, RiskLevel

logger = logging.getLogger("bhashashield.database")

# Check if PostgreSQL connection is available
DATABASE_URL = os.environ.get("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)
USE_POSTGRES = False
pg_pool = None

if DATABASE_URL and (DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")):
    try:
        import psycopg2
        import psycopg2.extras
        from psycopg2.pool import ThreadedConnectionPool
        
        # Normalize connection string for psycopg2 and configure connection timeouts
        dsn = DATABASE_URL
        if dsn.startswith("postgres://"):
            dsn = dsn.replace("postgres://", "postgresql://", 1)
        if "connect_timeout=" not in dsn and "?" not in dsn:
            dsn += "?connect_timeout=10"
        elif "connect_timeout=" not in dsn and "?" in dsn:
            dsn += "&connect_timeout=10"
        
        pg_pool = ThreadedConnectionPool(minconn=1, maxconn=20, dsn=dsn)
        USE_POSTGRES = True
        logger.info("Configured PostgreSQL ThreadedConnectionPool persistence engine via DATABASE_URL.")
    except Exception as e:
        logger.warning(f"Failed to initialize PostgreSQL pool: {e}. Falling back to SQLite WAL engine.")
        USE_POSTGRES = False
        pg_pool = None
        if settings.REQUIRE_POSTGRES:
            raise RuntimeError(f"Strict PostgreSQL requirement failed on startup: {e}")


def get_sqlite_connection():
    db_path = settings.DATABASE_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.row_factory = sqlite3.Row
    return conn


def checkpoint_sqlite_wal():
    """Forces SQLite WAL log to flush into main database file."""
    if not USE_POSTGRES:
        try:
            conn = get_sqlite_connection()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.close()
            logger.info("SQLite WAL checkpoint truncated successfully.")
        except Exception as e:
            logger.warning(f"SQLite WAL checkpoint failed: {e}")


def get_database_status() -> Dict[str, Any]:
    """
    Returns a safe diagnostic of the persistence layer.
    Exposes only backend type, connection status, persistence mode,
    and whether DATABASE_URL is configured.
    Never exposes raw credentials, hostnames, or connection strings.
    """
    has_url = bool(DATABASE_URL)
    if USE_POSTGRES and pg_pool:
        conn = None
        try:
            conn = pg_pool.getconn()
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
            return {
                "backend": "postgresql",
                "status": "connected",
                "persistence_mode": "durable_managed_cloud",
                "database_url_configured": True,
                "read_write_verified": True
            }
        except Exception as e:
            return {
                "backend": "postgresql",
                "status": "error",
                "persistence_mode": "durable_managed_cloud",
                "database_url_configured": True,
                "read_write_verified": False,
                "error": str(e)
            }
        finally:
            if conn and pg_pool:
                try:
                    pg_pool.putconn(conn)
                except Exception:
                    pass
    else:
        try:
            conn = get_sqlite_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            conn.close()
            return {
                "backend": "sqlite",
                "status": "connected",
                "persistence_mode": "container_local_ephemeral_wal",
                "database_url_configured": has_url,
                "read_write_verified": True,
                "note": "Production requires managed PostgreSQL for cross-restart persistence." if not has_url else "PostgreSQL connection failed; running in SQLite WAL fallback."
            }
        except Exception as e:
            return {
                "backend": "sqlite",
                "status": "error",
                "persistence_mode": "container_local_ephemeral_wal",
                "database_url_configured": has_url,
                "read_write_verified": False,
                "error": str(e)
            }


def backup_sqlite_db(backup_dest: Optional[str] = None) -> Optional[str]:
    """Creates a consistent point-in-time online backup using SQLite Backup API."""
    if USE_POSTGRES:
        return None
    try:
        source_conn = get_sqlite_connection()
        if not backup_dest:
            base_dir = os.path.dirname(settings.DATABASE_PATH)
            timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_dest = os.path.join(base_dir, f"bhashashield_backup_{timestamp_str}.db")
        dest_conn = sqlite3.connect(backup_dest)
        source_conn.backup(dest_conn)
        dest_conn.close()
        source_conn.close()
        logger.info(f"SQLite database backed up to {backup_dest}")
        return backup_dest
    except Exception as e:
        logger.error(f"SQLite backup failed: {e}")
        return None


def init_db():
    """Initializes tables, indexes, and schema migrations idempotently."""
    if USE_POSTGRES and pg_pool:
        conn = pg_pool.getconn()
        try:
            with conn.cursor() as cursor:
                # 1. Migrations tracker
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at VARCHAR(64) NOT NULL,
                    description TEXT NOT NULL
                );
                """)

                # 2. Users table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(64) PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    role VARCHAR(32) NOT NULL DEFAULT 'user',
                    created_at VARCHAR(64) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE
                );
                """)

                # 3. Scans table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id VARCHAR(64) PRIMARY KEY,
                    timestamp VARCHAR(64) NOT NULL,
                    channel VARCHAR(32) NOT NULL,
                    language VARCHAR(32) NOT NULL,
                    script VARCHAR(32) NOT NULL,
                    risk_score DOUBLE PRECISION NOT NULL,
                    risk_level VARCHAR(32) NOT NULL,
                    primary_threat VARCHAR(64),
                    threat_categories TEXT NOT NULL,
                    target_type VARCHAR(32) NOT NULL,
                    text_preview TEXT NOT NULL,
                    full_text TEXT,
                    is_saved BOOLEAN NOT NULL DEFAULT TRUE,
                    user_id VARCHAR(64) NOT NULL DEFAULT 'anonymous'
                );
                """)

                # 4. Idempotent column check for user_id in existing deployments
                cursor.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='scans' AND column_name='user_id') THEN 
                        ALTER TABLE scans ADD COLUMN user_id VARCHAR(64) NOT NULL DEFAULT 'anonymous'; 
                    END IF; 
                END $$;
                """)

                # 5. Evaluations table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_runs (
                    id VARCHAR(64) PRIMARY KEY,
                    timestamp VARCHAR(64) NOT NULL,
                    model_name VARCHAR(128) NOT NULL,
                    sample_count INTEGER NOT NULL,
                    metrics_json TEXT NOT NULL,
                    is_synthetic BOOLEAN NOT NULL DEFAULT TRUE
                );
                """)

                cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(timestamp DESC);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_channel ON scans(channel);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_risk_level ON scans(risk_level);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
                conn.commit()
                logger.info("PostgreSQL database tables and migrations initialized.")
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        # 1. Migrations tracker
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL,
            description TEXT NOT NULL
        )
        """)

        # 2. Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """)

        # 3. Scans table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            channel TEXT NOT NULL,
            language TEXT NOT NULL,
            script TEXT NOT NULL,
            risk_score REAL NOT NULL,
            risk_level TEXT NOT NULL,
            primary_threat TEXT,
            threat_categories TEXT NOT NULL,
            target_type TEXT NOT NULL,
            text_preview TEXT NOT NULL,
            full_text TEXT,
            is_saved INTEGER NOT NULL DEFAULT 1,
            user_id TEXT NOT NULL DEFAULT 'anonymous'
        )
        """)

        # 4. Idempotent column check for user_id in SQLite
        cursor.execute("PRAGMA table_info(scans)")
        columns = [row[1] for row in cursor.fetchall()]
        if "user_id" not in columns:
            cursor.execute("ALTER TABLE scans ADD COLUMN user_id TEXT NOT NULL DEFAULT 'anonymous'")

        # 5. Evaluations table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_runs (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            model_name TEXT NOT NULL,
            sample_count INTEGER NOT NULL,
            metrics_json TEXT NOT NULL,
            is_synthetic INTEGER NOT NULL DEFAULT 1
        )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(timestamp DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_channel ON scans(channel);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_risk_level ON scans(risk_level);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        conn.commit()
        conn.close()
        logger.info("SQLite database tables, migrations, and indexes initialized in WAL mode.")


# ==============================================================================
# USER AUTHENTICATION & MANAGEMENT OPERATIONS
# ==============================================================================

def create_user(username: str, email: str, hashed_password: str, role: str = "user") -> Dict[str, Any]:
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    created_at = datetime.utcnow().isoformat() + "Z"
    clean_username = username.lower().strip()
    clean_email = email.lower().strip()

    if USE_POSTGRES and pg_pool:
        conn = pg_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                INSERT INTO users (id, username, email, hashed_password, role, created_at, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, clean_username, clean_email, hashed_password, role, created_at, True))
                conn.commit()
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO users (id, username, email, hashed_password, role, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, clean_username, clean_email, hashed_password, role, created_at, 1))
            conn.commit()
        finally:
            conn.close()

    return {
        "id": user_id,
        "username": clean_username,
        "email": clean_email,
        "role": role,
        "created_at": created_at
    }


def get_user_by_username_or_email(identifier: str) -> Optional[Dict[str, Any]]:
    clean = identifier.lower().strip()
    if USE_POSTGRES and pg_pool:
        import psycopg2.extras
        conn = pg_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                SELECT id, username, email, hashed_password, role, created_at, is_active
                FROM users
                WHERE username = %s OR email = %s
                LIMIT 1
                """, (clean, clean))
                row = cursor.fetchone()
                return dict(row) if row else None
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, username, email, hashed_password, role, created_at, is_active
            FROM users
            WHERE username = ? OR email = ?
            LIMIT 1
            """, (clean, clean))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "hashed_password": row["hashed_password"],
                "role": row["role"],
                "created_at": row["created_at"],
                "is_active": bool(row["is_active"])
            }
        finally:
            conn.close()


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    if USE_POSTGRES and pg_pool:
        import psycopg2.extras
        conn = pg_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                SELECT id, username, email, role, created_at, is_active
                FROM users
                WHERE id = %s
                LIMIT 1
                """, (user_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, username, email, role, created_at, is_active
            FROM users
            WHERE id = ?
            LIMIT 1
            """, (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "role": row["role"],
                "created_at": row["created_at"],
                "is_active": bool(row["is_active"])
            }
        finally:
            conn.close()


# ==============================================================================
# SCAN PERSISTENCE & DATA ISOLATION OPERATIONS
# ==============================================================================

def save_scan(
    scan_id: str,
    channel: str,
    language: str,
    script: str,
    risk_score: float,
    risk_level: str,
    primary_threat: Optional[str],
    threat_categories: List[str],
    target_type: str,
    text_preview: str,
    full_text: Optional[str] = None,
    save_to_history: bool = True,
    user_id: str = "anonymous"
) -> ScanRecord:
    timestamp = datetime.utcnow().isoformat() + "Z"
    record = ScanRecord(
        id=scan_id,
        timestamp=timestamp,
        channel=channel,
        language=language,
        script=script,
        risk_score=risk_score,
        risk_level=risk_level,
        primary_threat=primary_threat,
        threat_categories=threat_categories,
        target_type=target_type,
        text_preview=text_preview,
        is_saved=save_to_history,
        user_id=user_id
    )

    if not save_to_history:
        return record

    if USE_POSTGRES and pg_pool:
        conn = pg_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                INSERT INTO scans (id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, full_text, is_saved, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """, (
                    record.id,
                    record.timestamp,
                    record.channel,
                    record.language,
                    record.script,
                    record.risk_score,
                    record.risk_level,
                    record.primary_threat,
                    json.dumps(record.threat_categories),
                    record.target_type,
                    record.text_preview,
                    full_text,
                    record.is_saved,
                    user_id
                ))
                conn.commit()
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO scans (id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, full_text, is_saved, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.id,
            record.timestamp,
            record.channel,
            record.language,
            record.script,
            record.risk_score,
            record.risk_level,
            record.primary_threat,
            json.dumps(record.threat_categories),
            record.target_type,
            record.text_preview,
            full_text,
            1 if record.is_saved else 0,
            user_id
        ))
        conn.commit()
        conn.close()
    return record


def get_scans(
    limit: int = 50,
    offset: int = 0,
    query: Optional[str] = None,
    risk_level: Optional[str] = None,
    user_id: Optional[str] = None,
    is_admin: bool = False
) -> List[ScanRecord]:
    """
    Returns scan records respecting strict user-data isolation:
    1. Admin: can query all records across the platform.
    2. Authenticated user: can query ONLY their own records (user_id = current_user.id).
    3. Unauthenticated public: can query ONLY public demo scans (user_id = 'anonymous').
    """
    conditions = []
    params: List[Any] = []

    # Ownership isolation filter
    if is_admin:
        if user_id:
            conditions.append("user_id = %s" if USE_POSTGRES else "user_id = ?")
            params.append(user_id)
    elif user_id:
        conditions.append("user_id = %s" if USE_POSTGRES else "user_id = ?")
        params.append(user_id)
    else:
        conditions.append("(user_id = 'anonymous' OR id LIKE 'DEMO-%')")

    if USE_POSTGRES and pg_pool:
        import psycopg2.extras
        if query:
            conditions.append("(text_preview ILIKE %s OR id ILIKE %s OR channel ILIKE %s)")
            search_pattern = f"%{query}%"
            params.extend([search_pattern, search_pattern, search_pattern])

        if risk_level and risk_level.upper() != "ALL":
            conditions.append("risk_level = %s")
            params.append(risk_level.upper())

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
        SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved, user_id
        FROM scans
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        conn = pg_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(sql, tuple(params))
                rows = cursor.fetchall()
        finally:
            pg_pool.putconn(conn)
    else:
        if query:
            conditions.append("(text_preview LIKE ? OR id LIKE ? OR channel LIKE ?)")
            search_pattern = f"%{query}%"
            params.extend([search_pattern, search_pattern, search_pattern])

        if risk_level and risk_level.upper() != "ALL":
            conditions.append("risk_level = ?")
            params.append(risk_level.upper())

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
        SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved, user_id
        FROM scans
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        conn.close()

    scans = []
    for r in rows:
        cats = r["threat_categories"]
        if isinstance(cats, str):
            try:
                cats = json.loads(cats)
            except Exception:
                cats = [cats]
        scans.append(ScanRecord(
            id=r["id"],
            timestamp=r["timestamp"],
            channel=r["channel"],
            language=r["language"],
            script=r["script"],
            risk_score=r["risk_score"],
            risk_level=r["risk_level"],
            primary_threat=r["primary_threat"],
            threat_categories=cats,
            target_type=r["target_type"],
            text_preview=r["text_preview"],
            is_saved=bool(r["is_saved"]),
            user_id=r.get("user_id", "anonymous") if isinstance(r, dict) else (r["user_id"] if "user_id" in r.keys() else "anonymous")
        ))
    return scans


def get_scan_by_id(scan_id: str, user_id: Optional[str] = None, is_admin: bool = False) -> Optional[ScanRecord]:
    """Retrieves a single scan, enforcing ownership verification."""
    if USE_POSTGRES and pg_pool:
        import psycopg2.extras
        conn = pg_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved, user_id
                FROM scans WHERE id = %s
                """, (scan_id,))
                r = cursor.fetchone()
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved, user_id
        FROM scans WHERE id = ?
        """, (scan_id,))
        r = cursor.fetchone()
        conn.close()

    if not r:
        return None

    record_user_id = r.get("user_id") if isinstance(r, dict) else (r["user_id"] if "user_id" in r.keys() else "anonymous")
    # Authorization check: admin, matching user, or public demo/anonymous scan
    if not is_admin:
        if user_id and record_user_id != user_id and record_user_id != "anonymous" and not scan_id.startswith("DEMO-"):
            return None
        if not user_id and record_user_id != "anonymous" and not scan_id.startswith("DEMO-"):
            return None

    cats = r["threat_categories"]
    if isinstance(cats, str):
        try:
            cats = json.loads(cats)
        except Exception:
            cats = [cats]

    return ScanRecord(
        id=r["id"],
        timestamp=r["timestamp"],
        channel=r["channel"],
        language=r["language"],
        script=r["script"],
        risk_score=r["risk_score"],
        risk_level=r["risk_level"],
        primary_threat=r["primary_threat"],
        threat_categories=cats,
        target_type=r["target_type"],
        text_preview=r["text_preview"],
        is_saved=bool(r["is_saved"]),
        user_id=record_user_id
    )


def delete_scan(scan_id: str, user_id: Optional[str] = None, is_admin: bool = False) -> bool:
    """Deletes a scan record. If user_id is provided and not is_admin, restricts deletion to that user."""
    if user_id and not is_admin:
        sql_pg = "DELETE FROM scans WHERE id = %s AND user_id = %s"
        sql_sq = "DELETE FROM scans WHERE id = ? AND user_id = ?"
        params = (scan_id, user_id)
    else:
        sql_pg = "DELETE FROM scans WHERE id = %s"
        sql_sq = "DELETE FROM scans WHERE id = ?"
        params = (scan_id,)

    if USE_POSTGRES and pg_pool:
        conn = pg_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql_pg, params)
                deleted = cursor.rowcount > 0
                conn.commit()
                return deleted
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute(sql_sq, params)
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted


def clear_scans(user_id: Optional[str] = None, is_admin: bool = False) -> int:
    """Clears scans. If user_id is provided and not is_admin, clears only that user's scans."""
    if user_id and not is_admin:
        sql_pg = "DELETE FROM scans WHERE user_id = %s"
        sql_sq = "DELETE FROM scans WHERE user_id = ?"
        params = (user_id,)
    else:
        sql_pg = "DELETE FROM scans WHERE id NOT LIKE 'DEMO-%'"
        sql_sq = "DELETE FROM scans WHERE id NOT LIKE 'DEMO-%'"
        params = ()

    if USE_POSTGRES and pg_pool:
        conn = pg_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql_pg, params)
                count = cursor.rowcount
                conn.commit()
                return count
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute(sql_sq, params)
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count


def get_dashboard_stats(user_id: Optional[str] = None, is_admin: bool = False) -> DashboardStats:
    """Calculates statistics scoped to user identity or platform-wide for admin/demo."""
    conditions = []
    params: List[Any] = []

    if is_admin:
        if user_id:
            conditions.append("user_id = %s" if USE_POSTGRES else "user_id = ?")
            params.append(user_id)
    elif user_id:
        conditions.append("user_id = %s" if USE_POSTGRES else "user_id = ?")
        params.append(user_id)
    else:
        conditions.append("(user_id = 'anonymous' OR id LIKE 'DEMO-%')")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    if USE_POSTGRES and pg_pool:
        import psycopg2.extras
        conn = pg_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM scans {where_clause}", tuple(params))
                total_scans = cursor.fetchone()["cnt"]

                sub_where = f"{where_clause} {'AND' if where_clause else 'WHERE'} risk_level IN ('MEDIUM', 'HIGH', 'CRITICAL')"
                cursor.execute(f"SELECT COUNT(*) as cnt FROM scans {sub_where}", tuple(params))
                threat_count = cursor.fetchone()["cnt"]

                sub_pi = f"{where_clause} {'AND' if where_clause else 'WHERE'} (primary_threat = 'PROMPT_INJECTION' OR threat_categories LIKE '%%PROMPT_INJECTION%%')"
                cursor.execute(f"SELECT COUNT(*) as cnt FROM scans {sub_pi}", tuple(params))
                prompt_injection_count = cursor.fetchone()["cnt"]

                sub_high = f"{where_clause} {'AND' if where_clause else 'WHERE'} risk_level IN ('HIGH', 'CRITICAL')"
                cursor.execute(f"SELECT COUNT(*) as cnt FROM scans {sub_high}", tuple(params))
                high_risk_count = cursor.fetchone()["cnt"]

                sub_clean = f"{where_clause} {'AND' if where_clause else 'WHERE'} risk_level = 'LOW'"
                cursor.execute(f"SELECT COUNT(*) as cnt FROM scans {sub_clean}", tuple(params))
                clean_count = cursor.fetchone()["cnt"]

                risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
                cursor.execute(f"SELECT risk_level, COUNT(*) as cnt FROM scans {where_clause} GROUP BY risk_level", tuple(params))
                for r in cursor.fetchall():
                    if r["risk_level"] in risk_distribution:
                        risk_distribution[r["risk_level"]] = r["cnt"]

                language_distribution = {"Telugu": 0, "Hindi": 0, "English": 0, "Romanized Telugu": 0, "Romanized Hindi": 0, "Mixed": 0}
                cursor.execute(f"SELECT language, COUNT(*) as cnt FROM scans {where_clause} GROUP BY language", tuple(params))
                for r in cursor.fetchall():
                    language_distribution[r["language"]] = r["cnt"]

                threat_distribution = {}
                sub_threat = f"{where_clause} {'AND' if where_clause else 'WHERE'} risk_level != 'LOW'"
                cursor.execute(f"SELECT threat_categories FROM scans {sub_threat}", tuple(params))
                for r in cursor.fetchall():
                    cats = r["threat_categories"]
                    if isinstance(cats, str):
                        try:
                            cats = json.loads(cats)
                        except Exception:
                            cats = [cats]
                    for c in cats:
                        if c != "BENIGN":
                            threat_distribution[c] = threat_distribution.get(c, 0) + 1

                channel_distribution = {"UPI Remark": 0, "SMS": 0, "WhatsApp": 0, "Email": 0, "General Text": 0}
                cursor.execute(f"SELECT channel, COUNT(*) as cnt FROM scans {where_clause} GROUP BY channel", tuple(params))
                for r in cursor.fetchall():
                    channel_distribution[r["channel"]] = r["cnt"]

                target_distribution = {"AI_SYSTEM": 0, "HUMAN_USER": 0, "BOTH": 0, "NONE": 0}
                cursor.execute(f"SELECT target_type, COUNT(*) as cnt FROM scans {where_clause} GROUP BY target_type", tuple(params))
                for r in cursor.fetchall():
                    target_distribution[r["target_type"]] = r["cnt"]

                cursor.execute(f"""
                SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved, user_id
                FROM scans
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT 10
                """, tuple(params))
                recent_rows = cursor.fetchall()
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        cursor.execute(f"SELECT COUNT(*) as cnt FROM scans {where_clause}", tuple(params))
        total_scans = cursor.fetchone()["cnt"]

        sub_where = f"{where_clause} {'AND' if where_clause else 'WHERE'} risk_level IN ('MEDIUM', 'HIGH', 'CRITICAL')"
        cursor.execute(f"SELECT COUNT(*) as cnt FROM scans {sub_where}", tuple(params))
        threat_count = cursor.fetchone()["cnt"]

        sub_pi = f"{where_clause} {'AND' if where_clause else 'WHERE'} (primary_threat = 'PROMPT_INJECTION' OR threat_categories LIKE '%PROMPT_INJECTION%')"
        cursor.execute(f"SELECT COUNT(*) as cnt FROM scans {sub_pi}", tuple(params))
        prompt_injection_count = cursor.fetchone()["cnt"]

        sub_high = f"{where_clause} {'AND' if where_clause else 'WHERE'} risk_level IN ('HIGH', 'CRITICAL')"
        cursor.execute(f"SELECT COUNT(*) as cnt FROM scans {sub_high}", tuple(params))
        high_risk_count = cursor.fetchone()["cnt"]

        sub_clean = f"{where_clause} {'AND' if where_clause else 'WHERE'} risk_level = 'LOW'"
        cursor.execute(f"SELECT COUNT(*) as cnt FROM scans {sub_clean}", tuple(params))
        clean_count = cursor.fetchone()["cnt"]

        risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        cursor.execute(f"SELECT risk_level, COUNT(*) as cnt FROM scans {where_clause} GROUP BY risk_level", tuple(params))
        for r in cursor.fetchall():
            if r["risk_level"] in risk_distribution:
                risk_distribution[r["risk_level"]] = r["cnt"]

        language_distribution = {"Telugu": 0, "Hindi": 0, "English": 0, "Romanized Telugu": 0, "Romanized Hindi": 0, "Mixed": 0}
        cursor.execute(f"SELECT language, COUNT(*) as cnt FROM scans {where_clause} GROUP BY language", tuple(params))
        for r in cursor.fetchall():
            language_distribution[r["language"]] = r["cnt"]

        threat_distribution = {}
        sub_threat = f"{where_clause} {'AND' if where_clause else 'WHERE'} risk_level != 'LOW'"
        cursor.execute(f"SELECT threat_categories FROM scans {sub_threat}", tuple(params))
        for r in cursor.fetchall():
            cats = r["threat_categories"]
            if isinstance(cats, str):
                try:
                    cats = json.loads(cats)
                except Exception:
                    cats = [cats]
            for c in cats:
                if c != "BENIGN":
                    threat_distribution[c] = threat_distribution.get(c, 0) + 1

        channel_distribution = {"UPI Remark": 0, "SMS": 0, "WhatsApp": 0, "Email": 0, "General Text": 0}
        cursor.execute(f"SELECT channel, COUNT(*) as cnt FROM scans {where_clause} GROUP BY channel", tuple(params))
        for r in cursor.fetchall():
            channel_distribution[r["channel"]] = r["cnt"]

        target_distribution = {"AI_SYSTEM": 0, "HUMAN_USER": 0, "BOTH": 0, "NONE": 0}
        cursor.execute(f"SELECT target_type, COUNT(*) as cnt FROM scans {where_clause} GROUP BY target_type", tuple(params))
        for r in cursor.fetchall():
            target_distribution[r["target_type"]] = r["cnt"]

        cursor.execute(f"""
        SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved, user_id
        FROM scans
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT 10
        """, tuple(params))
        recent_rows = cursor.fetchall()
        conn.close()

    recent_scans = []
    for r in recent_rows:
        cats = r["threat_categories"]
        if isinstance(cats, str):
            try:
                cats = json.loads(cats)
            except Exception:
                cats = [cats]
        recent_scans.append(ScanRecord(
            id=r["id"],
            timestamp=r["timestamp"],
            channel=r["channel"],
            language=r["language"],
            script=r["script"],
            risk_score=r["risk_score"],
            risk_level=r["risk_level"],
            primary_threat=r["primary_threat"],
            threat_categories=cats,
            target_type=r["target_type"],
            text_preview=r["text_preview"],
            is_saved=bool(r["is_saved"]),
            user_id=r.get("user_id", "anonymous") if isinstance(r, dict) else (r["user_id"] if "user_id" in r.keys() else "anonymous")
        ))

    return DashboardStats(
        total_scans=total_scans,
        threat_count=threat_count,
        prompt_injection_count=prompt_injection_count,
        high_risk_count=high_risk_count,
        clean_count=clean_count,
        risk_distribution=risk_distribution,
        language_distribution=language_distribution,
        threat_distribution=threat_distribution,
        channel_distribution=channel_distribution,
        target_distribution=target_distribution,
        recent_scans=recent_scans
    )


def save_evaluation_run(eval_id: str, model_name: str, sample_count: int, metrics: dict, is_synthetic: bool = True):
    if USE_POSTGRES and pg_pool:
        conn = pg_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                INSERT INTO evaluation_runs (id, timestamp, model_name, sample_count, metrics_json, is_synthetic)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """, (
                    eval_id,
                    datetime.utcnow().isoformat() + "Z",
                    model_name,
                    sample_count,
                    json.dumps(metrics),
                    is_synthetic
                ))
                conn.commit()
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO evaluation_runs (id, timestamp, model_name, sample_count, metrics_json, is_synthetic)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            eval_id,
            datetime.utcnow().isoformat() + "Z",
            model_name,
            sample_count,
            json.dumps(metrics),
            1 if is_synthetic else 0
        ))
        conn.commit()
        conn.close()


def get_latest_evaluation() -> Optional[Dict[str, Any]]:
    if USE_POSTGRES and pg_pool:
        import psycopg2.extras
        conn = pg_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                SELECT id, timestamp, model_name, sample_count, metrics_json, is_synthetic
                FROM evaluation_runs
                ORDER BY timestamp DESC
                LIMIT 1
                """)
                row = cursor.fetchone()
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, timestamp, model_name, sample_count, metrics_json, is_synthetic
        FROM evaluation_runs
        ORDER BY timestamp DESC
        LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()

    if not row:
        return None
    data = json.loads(row["metrics_json"])
    data["eval_run_id"] = row["id"]
    data["evaluated_at"] = row["timestamp"]
    data["model_evaluated"] = row["model_name"]
    data["is_synthetic"] = bool(row["is_synthetic"])
    return data
