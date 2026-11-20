"""Versión web de SQL2Excel.

Lista los .sql de Querys/, ejecuta el elegido contra SQL Server y devuelve
el resultado como .xlsx para descargar. Además permite encolar la generación
y recibir por correo un enlace de descarga. Pensada para red local (sin login).

Ejecutar desde la raíz del repositorio:
    uvicorn web.app:app --host 0.0.0.0 --port 8000
"""
import os
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.database.connection import ConnectionManager  # noqa: E402
from src.database.executor import QueryExecutor  # noqa: E402
from web import jobs, reports, settings  # noqa: E402

XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

app = FastAPI(title='SQL2Excel Web', docs_url=None, redoc_url=None)


def _remove(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _validar_fechas(sql, inicio, fin):
    executor = QueryExecutor(None)
    if executor.has_end_param(sql) and fin is None:
        raise HTTPException(status_code=400, detail='Este informe requiere la fecha fin')
    if inicio and fin and inicio > fin:
        raise HTTPException(
            status_code=400,
            detail='La fecha de inicio no puede ser posterior a la fecha fin',
        )


@app.get('/', include_in_schema=False)
def index():
    return FileResponse(Path(__file__).parent / 'static' / 'index.html')


@app.get('/api/informes')
def listar_informes():
    executor = QueryExecutor(None)
    informes = []
    for nombre, path in reports.scripts().items():
        sql = reports.read_sql(path)
        inicio_default, _ = executor.default_dates(sql)
        informes.append({
            'nombre': nombre,
            'usa_fecha_inicio': executor.has_start_param(sql),
            'usa_fecha_fin': executor.has_end_param(sql),
            'inicio_default': inicio_default.isoformat() if inicio_default else None,
        })
    return informes


@app.post('/api/informes/{nombre}/email', status_code=202)
def encolar_informe(
    nombre: str,
    inicio: date | None = Query(default=None, description='Fecha inicio (inclusiva)'),
    fin: date | None = Query(default=None, description='Fecha fin (inclusiva)'),
):
    path = reports.scripts().get(nombre)
    if path is None:
        raise HTTPException(status_code=404, detail='Informe no encontrado')

    sql = reports.read_sql(path)
    _validar_fechas(sql, inicio, fin)

    if not settings.ALLOWED_RECIPIENTS:
        raise HTTPException(status_code=500, detail='No hay destinatarios configurados')

    if jobs.count_recent(3600) >= settings.MAX_JOBS_PER_HOUR:
        raise HTTPException(status_code=429, detail='Demasiadas solicitudes; intenta más tarde')

    job_id = jobs.create_job(
        nombre,
        inicio.isoformat() if inicio else None,
        fin.isoformat() if fin else None,
    )
    return {
        'id': job_id,
        'estado': jobs.STATUS_PENDING,
        'destinatarios': settings.ALLOWED_RECIPIENTS,
    }


@app.get('/api/jobs/{job_id}')
def estado_job(job_id: str):
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail='Trabajo no encontrado')
    return {
        'id': job['id'],
        'estado': job['status'],
        'filas': job['filas'],
        'error': job['error'],
        'expira': job['expires_at'],
        'destinatarios': settings.ALLOWED_RECIPIENTS,
    }


@app.get('/descargas/{token}')
def descargar_por_token(token: str):
    job = jobs.get_by_token(token)
    if job is None:
        raise HTTPException(status_code=404, detail='Enlace no válido')
    if job['expires_at'] and datetime.fromisoformat(job['expires_at']) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail='El enlace ha caducado')

    path = settings.REPORTS_DIR / f'{job["id"]}.xlsx'
    if not path.is_file():
        raise HTTPException(status_code=410, detail='El archivo ya no está disponible')
    return FileResponse(path, media_type=XLSX_MIME, filename=job['filename'])


@app.get('/api/informes/{nombre}')
def descargar_informe(
    nombre: str,
    inicio: date | None = Query(default=None, description='Fecha inicio (inclusiva)'),
    fin: date | None = Query(default=None, description='Fecha fin (inclusiva)'),
):
    path = reports.scripts().get(nombre)
    if path is None:
        raise HTTPException(status_code=404, detail='Informe no encontrado')

    # Conexión nueva por petición: pymssql no es seguro entre hilos.
    conn_manager = ConnectionManager()
    if not conn_manager.has_config():
        raise HTTPException(status_code=500, detail='Falta la configuración de la base de datos (.env)')

    executor = QueryExecutor(conn_manager)
    sql = reports.read_sql(path)
    _validar_fechas(sql, inicio, fin)

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
