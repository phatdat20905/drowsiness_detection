# ============================================================
#  database/db.py  –  SQLite schema + CRUD helpers
# ============================================================

import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dms.db")


# ── Context manager ──────────────────────────────────────────
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Schema ───────────────────────────────────────────────────
def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'driver',   -- 'admin' | 'driver'
            full_name   TEXT    NOT NULL DEFAULT '',
            email       TEXT    DEFAULT '',
            phone       TEXT    DEFAULT '',
            license_no  TEXT    DEFAULT '',
            avatar_url  TEXT    DEFAULT '',
            created_at  TEXT    DEFAULT (datetime('now','localtime')),
            is_active   INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL REFERENCES users(id),
            started_at    TEXT    DEFAULT (datetime('now','localtime')),
            ended_at      TEXT,
            duration_sec  INTEGER DEFAULT 0,
            min_score     REAL    DEFAULT 100,
            total_closed  INTEGER DEFAULT 0,
            total_yawn    INTEGER DEFAULT 0,
            total_warning INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL REFERENCES users(id),
            session_id     INTEGER REFERENCES sessions(id),
            timestamp      TEXT    DEFAULT (datetime('now','localtime')),
            status         TEXT    NOT NULL,   -- NORMAL | TIRED | DROWSY
            score          REAL    DEFAULT 100,
            ear            REAL    DEFAULT 0,
            mar            REAL    DEFAULT 0,
            blink_rate     INTEGER DEFAULT 0,
            head_pose      TEXT    DEFAULT '',
            cnn_prob_eye   REAL    DEFAULT 0,
            cnn_prob_mouth REAL    DEFAULT 0,
            fused_eye      REAL    DEFAULT 0,
            fused_mouth    REAL    DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_alerts_user    ON alerts(user_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_ts      ON alerts(timestamp);
        CREATE INDEX IF NOT EXISTS idx_alerts_status  ON alerts(status);
        CREATE INDEX IF NOT EXISTS idx_sessions_user  ON sessions(user_id);
        """)

    # Seed admin nếu chưa có
    _seed_admin()


def _seed_admin():
    with get_conn() as conn:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE username='admin'"
        ).fetchone()
        if not exists:
            conn.execute(
                """INSERT INTO users (username, password, role, full_name, email)
                   VALUES (?, ?, 'admin', 'Administrator', 'admin@dms.local')""",
                ("admin", _hash("admin123")),
            )
            conn.execute(
                """INSERT INTO users (username, password, role, full_name, email, phone, license_no)
                   VALUES (?, ?, 'driver', 'Nguyễn Văn An', 'an@dms.local', '0901234567', 'B2-123456')""",
                ("driver1", _hash("driver123")),
            )
            conn.execute(
                """INSERT INTO users (username, password, role, full_name, email, phone, license_no)
                   VALUES (?, ?, 'driver', 'Trần Thị Bình', 'binh@dms.local', '0912345678', 'B2-654321')""",
                ("driver2", _hash("driver123")),
            )
    # Gọi seed data SAU KHI transaction users đã commit
    _seed_demo_data()


def _seed_demo_data():
    """Tạo dữ liệu mẫu để demo biểu đồ."""
    import random
    with get_conn() as conn:
        cnt = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        if cnt > 0:
            return

        drivers = conn.execute(
            "SELECT id FROM users WHERE role='driver'"
        ).fetchall()

        random.seed(42)
        for d in drivers:
            uid = d["id"]
            for day_offset in range(30):
                dt = datetime.now() - timedelta(days=day_offset)
                # 1-3 session/ngày
                for _ in range(random.randint(1, 3)):
                    sess_start = dt.replace(
                        hour=random.randint(6, 22),
                        minute=random.randint(0, 59),
                    )
                    n_alerts = random.randint(0, 8)
                    min_sc   = random.uniform(30, 100)
                    closed   = random.randint(0, 20)
                    yawn     = random.randint(0, 10)
                    warn     = random.randint(0, 5)

                    conn.execute(
                        """INSERT INTO sessions
                           (user_id, started_at, ended_at, duration_sec,
                            min_score, total_closed, total_yawn, total_warning)
                           VALUES (?,?,?,?,?,?,?,?)""",
                        (uid,
                         sess_start.strftime("%Y-%m-%d %H:%M:%S"),
                         (sess_start + timedelta(hours=random.uniform(0.5, 4))).strftime("%Y-%m-%d %H:%M:%S"),
                         random.randint(1800, 14400),
                         round(min_sc, 1), closed, yawn, warn),
                    )
                    sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

                    for _ in range(n_alerts):
                        status = random.choices(
                            ["TIRED", "DROWSY"], weights=[0.6, 0.4]
                        )[0]
                        ts = (sess_start + timedelta(
                            minutes=random.randint(5, 120)
                        )).strftime("%Y-%m-%d %H:%M:%S")
                        conn.execute(
                            """INSERT INTO alerts
                               (user_id, session_id, timestamp, status, score,
                                ear, mar, blink_rate, head_pose)
                               VALUES (?,?,?,?,?,?,?,?,?)""",
                            (uid, sid, ts, status,
                             round(random.uniform(20, 70), 1),
                             round(random.uniform(0.10, 0.25), 3),
                             round(random.uniform(0.4, 0.9), 3),
                             random.randint(8, 50),
                             random.choice(["Nhin thang", "Guc dau", "Quay trai", "Quay phai"])),
                        )


# ── Password ──────────────────────────────────────────────────
def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


# ── Auth ──────────────────────────────────────────────────────
def authenticate(username: str, password: str):
    """Trả về Row user nếu đúng, None nếu sai."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username=? AND password=? AND is_active=1",
            (username, _hash(password)),
        ).fetchone()


# ── Users CRUD ────────────────────────────────────────────────
def get_all_users(role=None, search=None):
    sql = "SELECT * FROM users WHERE 1=1"
    params = []
    if role:
        sql += " AND role=?"; params.append(role)
    if search:
        sql += " AND (full_name LIKE ? OR username LIKE ? OR email LIKE ?)"
        params += [f"%{search}%"] * 3
    sql += " ORDER BY created_at DESC"
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def get_user(user_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()


def create_user(username, password, role, full_name, email="", phone="", license_no=""):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO users (username, password, role, full_name, email, phone, license_no)
               VALUES (?,?,?,?,?,?,?)""",
            (username, _hash(password), role, full_name, email, phone, license_no),
        )


def update_user(user_id, full_name, email, phone, license_no):
    with get_conn() as conn:
        conn.execute(
            """UPDATE users SET full_name=?, email=?, phone=?, license_no=?
               WHERE id=?""",
            (full_name, email, phone, license_no, user_id),
        )


def change_password(user_id, new_password):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET password=? WHERE id=?",
            (_hash(new_password), user_id),
        )


def delete_user(user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))


def toggle_user_active(user_id: int, active: bool):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET is_active=? WHERE id=?",
            (1 if active else 0, user_id),
        )


# ── Sessions ──────────────────────────────────────────────────
def start_session(user_id: int) -> int:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO sessions (user_id) VALUES (?)", (user_id,)
        )
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def end_session(session_id: int, min_score, total_closed, total_yawn, total_warning):
    with get_conn() as conn:
        conn.execute(
            """UPDATE sessions SET ended_at=datetime('now','localtime'),
               min_score=?, total_closed=?, total_yawn=?, total_warning=?
               WHERE id=?""",
            (min_score, total_closed, total_yawn, total_warning, session_id),
        )


# ── Alerts ────────────────────────────────────────────────────
def insert_alert(user_id, session_id, status, score,
                 ear=0, mar=0, blink_rate=0, head_pose="",
                 cnn_prob_eye=0, cnn_prob_mouth=0,
                 fused_eye=0, fused_mouth=0):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO alerts
               (user_id, session_id, status, score, ear, mar,
                blink_rate, head_pose, cnn_prob_eye, cnn_prob_mouth,
                fused_eye, fused_mouth)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (user_id, session_id, status, score,
             ear, mar, blink_rate, head_pose,
             cnn_prob_eye, cnn_prob_mouth, fused_eye, fused_mouth),
        )


def get_recent_alerts(user_id=None, limit=50, days=7, status_filter=None):
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    sql = """
        SELECT a.*, u.full_name, u.username
        FROM alerts a JOIN users u ON a.user_id=u.id
        WHERE a.timestamp >= ?
    """
    params = [cutoff]
    if user_id:
        sql += " AND a.user_id=?"; params.append(user_id)
    if status_filter and status_filter != "Tất cả":
        sql += " AND a.status=?"; params.append(status_filter)
    sql += " ORDER BY a.timestamp DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


# ── Statistics ────────────────────────────────────────────────
def get_kpi(days=30):
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    with get_conn() as conn:
        total_drivers = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role='driver' AND is_active=1"
        ).fetchone()[0]
        total_alerts = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE date(timestamp)>=?", (cutoff,)
        ).fetchone()[0]
        total_drowsy = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE status='DROWSY' AND date(timestamp)>=?",
            (cutoff,)
        ).fetchone()[0]
        total_closed = conn.execute(
            "SELECT COALESCE(SUM(total_closed),0) FROM sessions WHERE date(started_at)>=?",
            (cutoff,)
        ).fetchone()[0]
        total_yawn = conn.execute(
            "SELECT COALESCE(SUM(total_yawn),0) FROM sessions WHERE date(started_at)>=?",
            (cutoff,)
        ).fetchone()[0]
    return {
        "drivers":      total_drivers,
        "alerts":       total_alerts,
        "drowsy":       total_drowsy,
        "closed_eyes":  total_closed,
        "yawns":        total_yawn,
    }


def get_alerts_timeseries(user_id=None, days=30):
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    sql = """
        SELECT date(timestamp) as day, status, COUNT(*) as cnt
        FROM alerts
        WHERE date(timestamp) >= ?
    """
    params = [cutoff]
    if user_id:
        sql += " AND user_id=?"; params.append(user_id)
    sql += " GROUP BY day, status ORDER BY day"
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def get_alerts_by_driver(days=30):
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    with get_conn() as conn:
        return conn.execute(
            """SELECT u.full_name, u.username,
                      COUNT(*) as total,
                      SUM(CASE WHEN a.status='DROWSY' THEN 1 ELSE 0 END) as drowsy,
                      SUM(CASE WHEN a.status='TIRED'  THEN 1 ELSE 0 END) as tired,
                      MIN(a.score) as min_score
               FROM alerts a JOIN users u ON a.user_id=u.id
               WHERE date(a.timestamp)>=? AND u.role='driver'
               GROUP BY u.id ORDER BY total DESC""",
            (cutoff,)
        ).fetchall()


def get_monthly_stats(user_id=None, months=6):
    cutoff = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
    sql = """
        SELECT strftime('%Y-%m', timestamp) as month,
               COUNT(*) as total_alerts,
               SUM(CASE WHEN status='DROWSY' THEN 1 ELSE 0 END) as drowsy_count
        FROM alerts WHERE date(timestamp)>=?
    """
    params = [cutoff]
    if user_id:
        sql += " AND user_id=?"; params.append(user_id)
    sql += " GROUP BY month ORDER BY month"
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()
