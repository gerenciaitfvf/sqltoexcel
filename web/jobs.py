"""Cola de trabajos persistente (SQLite) para generar informes en segundo plano.

Se usa SQLite porque la app corre con varios workers de uvicorn: una cola en
memoria no se compartiría entre ellos ni sobreviviría a un reinicio.
"""
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

from web import settings

STATUS_PENDING = 'pendiente'
STATUS_RUNNING = 'generando'
STATUS_READY = 'listo'
STATUS_ERROR = 'error'
STATUS_EXPIRED = 'expirado'

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    inicio TEXT,
    fin TEXT,
    status TEXT NOT NULL,
    filas INTEGER,
    error TEXT,
    filename TEXT,
    token TEXT,
    created_at TEXT NOT NULL,
    claimed_at TEXT,
    expires_at TEXT,
    sent_at TEXT
)
"""


def _now():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.astimezone(timezone.utc).isoformat(timespec='seconds')


def to_iso(value):
    """Convierte un datetime a la representación ISO usada en la base de datos."""
    return _iso(value)


def _connect():
    settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute(SCHEMA)
    return conn


def init_db():
    _connect().close()


def _fetch_one(query, params=()):
    conn = _connect()
    try:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _update(job_id, **fields):
    if not fields:
        return
    cols = ', '.join(f'{name} = ?' for name in fields)
    conn = _connect()
    try:
        with conn:
            conn.execute(f'UPDATE jobs SET {cols} WHERE id = ?', (*fields.values(), job_id))
    finally:
        conn.close()


def create_job(nombre, inicio=None, fin=None):
    job_id = uuid.uuid4().hex
    conn = _connect()
    try:
        with conn:
            conn.execute(
                'INSERT INTO jobs (id, nombre, inicio, fin, status, created_at) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (job_id, nombre, inicio, fin, STATUS_PENDING, _iso(_now())),
            )
    finally:
        conn.close()
    return job_id


def claim_next():
    """Marca y devuelve el trabajo pendiente más antiguo, o None."""
    conn = _connect()
    try:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute(
            'SELECT * FROM jobs WHERE status = ? ORDER BY created_at LIMIT 1',
            (STATUS_PENDING,),
        ).fetchone()
        if row is None:
            conn.rollback()
            return None
        claimed = _iso(_now())
        conn.execute(
            'UPDATE jobs SET status = ?, claimed_at = ? WHERE id = ?',
            (STATUS_RUNNING, claimed, row['id']),
        )
        conn.commit()
        job = dict(row)
        job['status'] = STATUS_RUNNING
        job['claimed_at'] = claimed
        return job
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def mark_generated(job_id, filas, filename, token, expires_at):
    _update(job_id, filas=filas, filename=filename, token=token, expires_at=expires_at)


def mark_listo(job_id, error=None):
    _update(job_id, status=STATUS_READY, sent_at=_iso(_now()), error=error)


def mark_error(job_id, error):
    _update(job_id, status=STATUS_ERROR, error=str(error)[:1000])


def get_job(job_id):
    return _fetch_one('SELECT * FROM jobs WHERE id = ?', (job_id,))


def get_by_token(token):
    return _fetch_one('SELECT * FROM jobs WHERE token = ?', (token,))


def count_recent(seconds):
    since = _iso(_now() - timedelta(seconds=seconds))
    row = _fetch_one('SELECT COUNT(*) AS n FROM jobs WHERE created_at >= ?', (since,))
    return row['n'] if row else 0


def expire_jobs():
    """Marca como expirados los trabajos listos/erróneos cuya caducidad pasó."""
    now = _iso(_now())
    conn = _connect()
    try:
        with conn:
            rows = conn.execute(
                'SELECT * FROM jobs WHERE status IN (?, ?) AND expires_at IS NOT NULL '
                'AND expires_at <= ?',
                (STATUS_READY, STATUS_ERROR, now),
            ).fetchall()
            conn.executemany(
                'UPDATE jobs SET status = ? WHERE id = ?',
                [(STATUS_EXPIRED, r['id']) for r in rows],
            )
    finally:
        conn.close()
    return [dict(r) for r in rows]


def reset_stale(minutes=30):
    """Devuelve a pendiente los trabajos que quedaron colgados en 'generando'."""
    limit = _iso(_now() - timedelta(minutes=minutes))
    conn = _connect()
    try:
        with conn:
            rows = conn.execute(
                'SELECT * FROM jobs WHERE status = ? AND claimed_at <= ?',
                (STATUS_RUNNING, limit),
            ).fetchall()
            conn.executemany(
                'UPDATE jobs SET status = ?, claimed_at = NULL WHERE id = ?',
                [(STATUS_PENDING, r['id']) for r in rows],
            )
    finally:
        conn.close()
    return [dict(r) for r in rows]
