import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from app.config import settings
from app.models import ScanRecord, DashboardStats, RiskLevel

def get_connection():
    db_path = settings.DATABASE_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
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

    conn = get_connection()
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

def get_scans(limit: int = 50, offset: int = 0) -> List[ScanRecord]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved
    FROM scans
    ORDER BY timestamp DESC
    LIMIT ? OFFSET ?
    """, (limit, offset))
    rows = cursor.fetchall()
    conn.close()

    scans = []
    for r in rows:
        scans.append(ScanRecord(
            id=r["id"],
            timestamp=r["timestamp"],
            channel=r["channel"],
            language=r["language"],
            script=r["script"],
            risk_score=r["risk_score"],
            risk_level=r["risk_level"],
            primary_threat=r["primary_threat"],
            threat_categories=json.loads(r["threat_categories"]),
            target_type=r["target_type"],
            text_preview=r["text_preview"],
            is_saved=bool(r["is_saved"])
        ))
    return scans

def clear_scans() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scans")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

def get_dashboard_stats() -> DashboardStats:
    conn = get_connection()
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

    # Risk distribution
    risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    cursor.execute("SELECT risk_level, COUNT(*) as cnt FROM scans GROUP BY risk_level")
    for r in cursor.fetchall():
        if r["risk_level"] in risk_distribution:
            risk_distribution[r["risk_level"]] = r["cnt"]

    # Language distribution
    language_distribution = {"Telugu": 0, "Hindi": 0, "English": 0, "Romanized Telugu": 0, "Romanized Hindi": 0, "Mixed": 0}
    cursor.execute("SELECT language, COUNT(*) as cnt FROM scans GROUP BY language")
    for r in cursor.fetchall():
        language_distribution[r["language"]] = r["cnt"]

    # Threat distribution
    threat_distribution = {}
    cursor.execute("SELECT threat_categories FROM scans WHERE risk_level != 'LOW'")
    for r in cursor.fetchall():
        cats = json.loads(r["threat_categories"])
        for c in cats:
            if c != "BENIGN":
                threat_distribution[c] = threat_distribution.get(c, 0) + 1

    # Channel distribution
    channel_distribution = {"UPI Remark": 0, "SMS": 0, "WhatsApp": 0, "Email": 0, "General Text": 0}
    cursor.execute("SELECT channel, COUNT(*) as cnt FROM scans GROUP BY channel")
    for r in cursor.fetchall():
        channel_distribution[r["channel"]] = r["cnt"]

    # Target distribution
    target_distribution = {"AI_SYSTEM": 0, "HUMAN_USER": 0, "BOTH": 0, "NONE": 0}
    cursor.execute("SELECT target_type, COUNT(*) as cnt FROM scans GROUP BY target_type")
    for r in cursor.fetchall():
        target_distribution[r["target_type"]] = r["cnt"]

    # Recent scans
    cursor.execute("""
    SELECT id, timestamp, channel, language, script, risk_score, risk_level, primary_threat, threat_categories, target_type, text_preview, is_saved
    FROM scans
    ORDER BY timestamp DESC
    LIMIT 10
    """)
    recent_rows = cursor.fetchall()
    conn.close()

    recent_scans = [
        ScanRecord(
            id=r["id"],
            timestamp=r["timestamp"],
            channel=r["channel"],
            language=r["language"],
            script=r["script"],
            risk_score=r["risk_score"],
            risk_level=r["risk_level"],
            primary_threat=r["primary_threat"],
            threat_categories=json.loads(r["threat_categories"]),
            target_type=r["target_type"],
            text_preview=r["text_preview"],
            is_saved=bool(r["is_saved"])
        ) for r in recent_rows
    ]

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
    conn = get_connection()
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
    conn = get_connection()
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
