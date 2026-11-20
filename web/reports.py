"""Acceso a los informes (.sql) disponibles en Querys/."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUERYS_DIR = Path(os.getenv('QUERYS_DIR', str(ROOT / 'Querys'))).resolve()
SQL_ENCODING = 'latin-1'


def scripts():
    """Mapa nombre -> ruta de los .sql disponibles (se relee en cada petición)."""
    if not QUERYS_DIR.is_dir():
        return {}
    return {p.stem: p for p in sorted(QUERYS_DIR.glob('*.sql'), key=lambda p: p.stem.lower())}


def read_sql(path):
    return Path(path).read_text(encoding=SQL_ENCODING)
