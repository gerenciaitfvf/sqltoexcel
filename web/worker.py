"""Worker que procesa la cola de informes y envía los enlaces por correo.

Se ejecuta como servicio aparte:
    python -m web.worker
"""
import logging
import secrets
import time
from datetime import date, datetime, timedelta, timezone

from web import jobs, mailer, reports, settings
from src.database.connection import ConnectionManager
from src.database.executor import QueryExecutor

log = logging.getLogger('worker')

CLEANUP_INTERVAL = 60  # segundos


def _parse_fecha(valor):
    return date.fromisoformat(valor) if valor else None


def _sufijo(inicio, fin):
    if inicio and fin:
        return f'{inicio.isoformat()}_a_{fin.isoformat()}'
    if fin:
        return fin.isoformat()
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def _rango_texto(inicio, fin):
    if inicio and fin:
        return f'del {inicio.isoformat()} al {fin.isoformat()}'
    if fin:
        return f'hasta el {fin.isoformat()}'
    return 'completo'


def _file(job_id):
    return settings.REPORTS_DIR / f'{job_id}.xlsx'


def process_job(job):
    """Genera el Excel y envía un correo a cada destinatario permitido."""
    inicio = _parse_fecha(job['inicio'])
    fin = _parse_fecha(job['fin'])

    path = reports.scripts().get(job['nombre'])
    if path is None:
        raise RuntimeError(f'Informe no encontrado: {job["nombre"]}')
    sql = reports.read_sql(path)

    conn_manager = ConnectionManager()
    if not conn_manager.has_config():
        raise RuntimeError('Falta la configuración de la base de datos (.env)')

    executor = QueryExecutor(conn_manager)
    if executor.has_end_param(sql) and fin is None:
        raise RuntimeError('Este informe requiere la fecha fin')

    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    destino = _file(job['id'])
    try:
        filas = executor.execute_query_to_xlsx(sql, str(destino), fin, inicio)
    finally:
        conn_manager.disconnect()

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.DOWNLOAD_TTL_HOURS)
    filename = f'{job["nombre"]}_{_sufijo(inicio, fin)}.xlsx'
    jobs.mark_generated(job['id'], filas, filename, token, jobs.to_iso(expires_at))

    url = f'{settings.PUBLIC_BASE_URL}/descargas/{token}'
    rango = _rango_texto(inicio, fin)

    destinatarios = settings.ALLOWED_RECIPIENTS
    if not destinatarios:
        jobs.mark_error(job['id'], 'No hay destinatarios configurados (ALLOWED_RECIPIENTS)')
        return

    errores = []
    for destinatario in destinatarios:
        try:
            mailer.send_report_email(destinatario, job['nombre'], rango, url, expires_at)
            log.info('Correo enviado a %s (job %s)', destinatario, job['id'])
        except Exception as exc:  # noqa: BLE001
            log.exception('Error enviando a %s', destinatario)
            errores.append(str(exc))

    if len(errores) == len(destinatarios):
        jobs.mark_error(job['id'], 'No se pudo enviar el correo: ' + '; '.join(errores))
    else:
        jobs.mark_listo(job['id'], error='; '.join(errores) or None)


def _run_job(job):
    try:
        process_job(job)
    except Exception as exc:  # noqa: BLE001
        log.exception('El trabajo %s falló', job['id'])
        jobs.mark_error(job['id'], str(exc))
        try:
            _file(job['id']).unlink()
        except OSError:
            pass


def _cleanup():
    for job in jobs.expire_jobs():
        try:
            _file(job['id']).unlink()
            log.info('Archivo caducado eliminado: %s', job['id'])
        except OSError:
            pass
    for job in jobs.reset_stale():
        try:
            _file(job['id']).unlink()
        except OSError:
            pass
        log.warning('Trabajo colgado devuelto a la cola: %s', job['id'])


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    jobs.init_db()
    log.info('Worker iniciado. Destinatarios: %s', ', '.join(settings.ALLOWED_RECIPIENTS) or '(ninguno)')

    ultima_limpieza = 0.0
    while True:
        try:
            ahora = time.monotonic()
            if ahora - ultima_limpieza >= CLEANUP_INTERVAL:
                _cleanup()
                ultima_limpieza = ahora

            job = jobs.claim_next()
            if job is None:
                time.sleep(2)
                continue
            log.info('Procesando %s (%s)', job['id'], job['nombre'])
            _run_job(job)
        except KeyboardInterrupt:
            log.info('Worker detenido')
            break
        except Exception:  # noqa: BLE001
            log.exception('Error en el bucle del worker')
            time.sleep(5)


if __name__ == '__main__':
    main()
