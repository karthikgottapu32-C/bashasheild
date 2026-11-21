import sqlite3
import json
import os
import logging
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
        from psycopg2.pool import SimpleConnectionPool
        
        # Render provides postgres:// which psycopg2 accepts if normalized
        dsn = DATABASE_URL
        if dsn.startswith("postgres://"):
            dsn = dsn.replace("postgres://", "postgresql://", 1)
        
        pg_pool = SimpleConnectionPool(1, 10, dsn)
        USE_POSTGRES = True
        logger.info("Configured PostgreSQL persistence engine via DATABASE_URL.")
    except Exception as e:
        logger.warning(f"Failed to initialize PostgreSQL pool: {e}. Falling back to SQLite WAL engine.")
        USE_POSTGRES = False


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
    if USE_POSTGRES and pg_pool:
        conn = pg_pool.getconn()
        try:
            with conn.cursor() as cursor:
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
                    is_saved BOOLEAN NOT NULL DEFAULT TRUE
                );
                """)
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
                conn.commit()
                logger.info("PostgreSQL database tables and indexes initialized.")
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
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
            is_saved INTEGER NOT NULL DEFAULT 1
        )
        """)

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
        conn.commit()
        conn.close()
        logger.info("SQLite database tables and indexes initialized in WAL mode.")


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
    save_to_history: bool = True
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
        is_saved=save_to_history
    )

    if not save_to_history:
        return record

    if USE_POSTGRES and pg_pool:
        conn = pg_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                INSERT INTO scans (id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, full_text, is_saved)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    record.is_saved
                ))
                conn.commit()
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO scans (id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, full_text, is_saved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            1 if record.is_saved else 0
        ))
        conn.commit()
        conn.close()
    return record


def get_scans(
    limit: int = 50,
    offset: int = 0,
    query: Optional[str] = None,
    risk_level: Optional[str] = None
) -> List[ScanRecord]:
    conditions = []
    params: List[Any] = []

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
        SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved
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
        SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved
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
            cats = json.loads(cats)
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
            is_saved=bool(r["is_saved"])
        ))
    return scans


def get_scan_by_id(scan_id: str) -> Optional[ScanRecord]:
    if USE_POSTGRES and pg_pool:
        import psycopg2.extras
        conn = pg_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved
                FROM scans WHERE id = %s
                """, (scan_id,))
                r = cursor.fetchone()
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved
        FROM scans WHERE id = ?
        """, (scan_id,))
        r = cursor.fetchone()
        conn.close()

    if not r:
        return None
    cats = r["threat_categories"]
    if isinstance(cats, str):
        cats = json.loads(cats)
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
        is_saved=bool(r["is_saved"])
    )


def delete_scan(scan_id: str) -> bool:
    if USE_POSTGRES and pg_pool:
        conn = pg_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM scans WHERE id = %s", (scan_id,))
                deleted = cursor.rowcount > 0
                conn.commit()
                return deleted
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted


def clear_scans() -> int:
    if USE_POSTGRES and pg_pool:
        conn = pg_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM scans")
                count = cursor.rowcount
                conn.commit()
                return count
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scans")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count


def get_dashboard_stats() -> DashboardStats:
    if USE_POSTGRES and pg_pool:
        import psycopg2.extras
        conn = pg_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT COUNT(*) as cnt FROM scans")
                total_scans = cursor.fetchone()["cnt"]

                cursor.execute("SELECT COUNT(*) as cnt FROM scans WHERE risk_level IN ('MEDIUM', 'HIGH', 'CRITICAL')")
                threat_count = cursor.fetchone()["cnt"]

                cursor.execute("SELECT COUNT(*) as cnt FROM scans WHERE primary_threat = 'PROMPT_INJECTION' OR threat_categories LIKE '%PROMPT_INJECTION%'")
                prompt_injection_count = cursor.fetchone()["cnt"]

                cursor.execute("SELECT COUNT(*) as cnt FROM scans WHERE risk_level IN ('HIGH', 'CRITICAL')")
                high_risk_count = cursor.fetchone()["cnt"]

                cursor.execute("SELECT COUNT(*) as cnt FROM scans WHERE risk_level = 'LOW'")
                clean_count = cursor.fetchone()["cnt"]

                risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
                cursor.execute("SELECT risk_level, COUNT(*) as cnt FROM scans GROUP BY risk_level")
                for r in cursor.fetchall():
                    if r["risk_level"] in risk_distribution:
                        risk_distribution[r["risk_level"]] = r["cnt"]

                language_distribution = {"Telugu": 0, "Hindi": 0, "English": 0, "Romanized Telugu": 0, "Romanized Hindi": 0, "Mixed": 0}
                cursor.execute("SELECT language, COUNT(*) as cnt FROM scans GROUP BY language")
                for r in cursor.fetchall():
                    language_distribution[r["language"]] = r["cnt"]

                threat_distribution = {}
                cursor.execute("SELECT threat_categories FROM scans WHERE risk_level != 'LOW'")
                for r in cursor.fetchall():
                    cats = r["threat_categories"]
                    if isinstance(cats, str):
                        cats = json.loads(cats)
                    for c in cats:
                        if c != "BENIGN":
                            threat_distribution[c] = threat_distribution.get(c, 0) + 1

                channel_distribution = {"UPI Remark": 0, "SMS": 0, "WhatsApp": 0, "Email": 0, "General Text": 0}
                cursor.execute("SELECT channel, COUNT(*) as cnt FROM scans GROUP BY channel")
                for r in cursor.fetchall():
                    channel_distribution[r["channel"]] = r["cnt"]

                target_distribution = {"AI_SYSTEM": 0, "HUMAN_USER": 0, "BOTH": 0, "NONE": 0}
                cursor.execute("SELECT target_type, COUNT(*) as cnt FROM scans GROUP BY target_type")
                for r in cursor.fetchall():
                    target_distribution[r["target_type"]] = r["cnt"]

                cursor.execute("""
                SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved
                FROM scans
                ORDER BY timestamp DESC
                LIMIT 10
                """)
                recent_rows = cursor.fetchall()
        finally:
            pg_pool.putconn(conn)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as cnt FROM scans")
        total_scans = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM scans WHERE risk_level IN ('MEDIUM', 'HIGH', 'CRITICAL')")
        threat_count = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM scans WHERE primary_threat = 'PROMPT_INJECTION' OR threat_categories LIKE '%PROMPT_INJECTION%'")
        prompt_injection_count = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM scans WHERE risk_level IN ('HIGH', 'CRITICAL')")
        high_risk_count = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM scans WHERE risk_level = 'LOW'")
        clean_count = cursor.fetchone()["cnt"]

        risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        cursor.execute("SELECT risk_level, COUNT(*) as cnt FROM scans GROUP BY risk_level")
        for r in cursor.fetchall():
            if r["risk_level"] in risk_distribution:
                risk_distribution[r["risk_level"]] = r["cnt"]

        language_distribution = {"Telugu": 0, "Hindi": 0, "English": 0, "Romanized Telugu": 0, "Romanized Hindi": 0, "Mixed": 0}
        cursor.execute("SELECT language, COUNT(*) as cnt FROM scans GROUP BY language")
        for r in cursor.fetchall():
            language_distribution[r["language"]] = r["cnt"]

        threat_distribution = {}
        cursor.execute("SELECT threat_categories FROM scans WHERE risk_level != 'LOW'")
        for r in cursor.fetchall():
            cats = json.loads(r["threat_categories"])
            for c in cats:
                if c != "BENIGN":
                    threat_distribution[c] = threat_distribution.get(c, 0) + 1

        channel_distribution = {"UPI Remark": 0, "SMS": 0, "WhatsApp": 0, "Email": 0, "General Text": 0}
        cursor.execute("SELECT channel, COUNT(*) as cnt FROM scans GROUP BY channel")
        for r in cursor.fetchall():
            channel_distribution[r["channel"]] = r["cnt"]

        target_distribution = {"AI_SYSTEM": 0, "HUMAN_USER": 0, "BOTH": 0, "NONE": 0}
        cursor.execute("SELECT target_type, COUNT(*) as cnt FROM scans GROUP BY target_type")
        for r in cursor.fetchall():
            target_distribution[r["target_type"]] = r["cnt"]

        cursor.execute("""
        SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved
        FROM scans
        ORDER BY timestamp DESC
        LIMIT 10
        """)
        recent_rows = cursor.fetchall()
        conn.close()

    recent_scans = []
    for r in recent_rows:
        cats = r["threat_categories"]
        if isinstance(cats, str):
            cats = json.loads(cats)
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
            is_saved=bool(r["is_saved"])
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
