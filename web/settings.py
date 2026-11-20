"""Configuración de la versión web, leída de variables de entorno (.env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')

DATA_DIR = Path(os.getenv('DATA_DIR', str(ROOT / 'data'))).resolve()
REPORTS_DIR = DATA_DIR / 'reportes'
DB_PATH = DATA_DIR / 'jobs.db'

PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', 'http://localhost:8000').rstrip('/')
DOWNLOAD_TTL_HOURS = int(os.getenv('DOWNLOAD_TTL_HOURS', '72'))
MAX_JOBS_PER_HOUR = int(os.getenv('MAX_JOBS_PER_HOUR', '10'))

ALLOWED_RECIPIENTS = [
    r.strip() for r in os.getenv('ALLOWED_RECIPIENTS', '').split(',') if r.strip()
]

SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
MAIL_FROM = os.getenv('MAIL_FROM', '')
