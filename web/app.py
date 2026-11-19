"""Versión web de SQL2Excel.

Lista los .sql de Querys/, ejecuta el elegido contra SQL Server y devuelve
el resultado como .xlsx para descargar. Pensada para red local (sin login).

Ejecutar desde la raíz del repositorio:
    uvicorn web.app:app --host 0.0.0.0 --port 8000
"""
import os
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.database.connection import ConnectionManager  # noqa: E402
from src.database.executor import QueryExecutor  # noqa: E402

QUERYS_DIR = Path(os.getenv('QUERYS_DIR', ROOT / 'Querys')).resolve()
SQL_ENCODING = 'latin-1'
XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

app = FastAPI(title='SQL2Excel Web', docs_url=None, redoc_url=None)


def _scripts():
    """Mapa nombre -> ruta de los .sql disponibles (se relee en cada petición)."""
    if not QUERYS_DIR.is_dir():
        return {}
    return {p.stem: p for p in sorted(QUERYS_DIR.glob('*.sql'), key=lambda p: p.stem.lower())}


def _read_sql(path):
    return path.read_text(encoding=SQL_ENCODING)


def _remove(path):
    try:
        os.remove(path)
    except OSError:
        pass


@app.get('/', include_in_schema=False)
def index():
    return FileResponse(Path(__file__).parent / 'static' / 'index.html')


@app.get('/api/informes')
def listar_informes():
    executor = QueryExecutor(None)
    informes = []
    for nombre, path in _scripts().items():
        sql = _read_sql(path)
        inicio_default, _ = executor.default_dates(sql)
        informes.append({
            'nombre': nombre,
            'usa_fecha_inicio': executor.has_start_param(sql),
            'usa_fecha_fin': executor.has_end_param(sql),
            'inicio_default': inicio_default.isoformat() if inicio_default else None,
        })
    return informes


@app.get('/api/informes/{nombre}')
def descargar_informe(
    nombre: str,
    inicio: date | None = Query(default=None, description='Fecha inicio (inclusiva)'),
    fin: date | None = Query(default=None, description='Fecha fin (inclusiva)'),
):
    path = _scripts().get(nombre)
    if path is None:
        raise HTTPException(status_code=404, detail='Informe no encontrado')

    # Conexión nueva por petición: pymssql no es seguro entre hilos.
    conn_manager = ConnectionManager()
    if not conn_manager.has_config():
        raise HTTPException(status_code=500, detail='Falta la configuración de la base de datos (.env)')

    executor = QueryExecutor(conn_manager)
    sql = _read_sql(path)
    if executor.has_end_param(sql) and fin is None:
        raise HTTPException(status_code=400, detail='Este informe requiere la fecha fin')
    if inicio and fin and inicio > fin:
        raise HTTPException(status_code=400, detail='La fecha de inicio no puede ser posterior a la fecha fin')

    fd, tmp_path = tempfile.mkstemp(prefix=f'{nombre}_', suffix='.xlsx')
    os.close(fd)
    try:
        filas = executor.execute_query_to_xlsx(sql, tmp_path, fin, inicio)
    except Exception as e:
        _remove(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn_manager.disconnect()

    if inicio and fin:
        sufijo = f'{inicio.isoformat()}_a_{fin.isoformat()}'
    elif fin:
        sufijo = fin.isoformat()
    else:
        sufijo = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{nombre}_{sufijo}.xlsx'
    return FileResponse(
        tmp_path,
        media_type=XLSX_MIME,
        filename=filename,
        headers={'X-Filas': str(filas)},
        background=BackgroundTask(_remove, tmp_path),
    )
