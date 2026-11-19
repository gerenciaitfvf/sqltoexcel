import os
import re
import pandas as pd
from datetime import date, datetime, timedelta

from src.export.excel_writer import write_workbook_stream


def _to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


class QueryExecutor:
    def __init__(self, connection_manager):
        self.conn_manager = connection_manager

    # Columnas de fecha que se pueden parametrizar en los .sql
    _DATE_COLS = r"(?:comp|mb)\.Fecha"
    _START_RE = re.compile(rf"({_DATE_COLS}\s*>\s*')(\d{{4}}-\d{{2}}-\d{{2}})(')", re.IGNORECASE)
    _END_RE = re.compile(rf"({_DATE_COLS}\s*<\s*')(\d{{4}}-\d{{2}}-\d{{2}})(')", re.IGNORECASE)

    def has_date_params(self, sql_content):
        return self.has_start_param(sql_content) or self.has_end_param(sql_content)

    def has_start_param(self, sql_content):
        return bool(self._START_RE.search(sql_content))

    def has_end_param(self, sql_content):
        return bool(self._END_RE.search(sql_content))

    def default_dates(self, sql_content):
        """Fechas (inclusivas) que trae escritas el SQL: (inicio, fin) o None."""
        inicio = fin = None
        m = self._START_RE.search(sql_content)
        if m:
            inicio = _to_date(m.group(2)) + timedelta(days=1)
        m = self._END_RE.search(sql_content)
        if m:
            fin = _to_date(m.group(2)) - timedelta(days=1)
        return inicio, fin

    def apply_date_filter(self, sql_content, fecha_fin=None, fecha_inicio=None):
        """Aplica un rango de fechas INCLUSIVO.

        El SQL usa comparaciones estrictas (Fecha > X AND Fecha < Y), así que
        inicio se escribe como inicio - 1 día y fin como fin + 1 día.
        """
        if fecha_inicio:
            valor = (_to_date(fecha_inicio) - timedelta(days=1)).isoformat()
            sql_content = self._START_RE.sub(rf"\g<1>{valor}\g<3>", sql_content)
        if fecha_fin:
            valor = (_to_date(fecha_fin) + timedelta(days=1)).isoformat()
            sql_content = self._END_RE.sub(rf"\g<1>{valor}\g<3>", sql_content)
        return sql_content

    def execute_query(self, sql_content, fecha_fin=None, fecha_inicio=None):
        sql_content = self._prepare_sql(sql_content, fecha_fin, fecha_inicio)
        conn = self.conn_manager.get_connection()
        try:
            df = pd.read_sql(sql_content, conn)
            return df
        except Exception as e:
            raise Exception(f"Error al ejecutar la consulta: {str(e)}")

    def execute_query_to_xlsx(self, sql_content, path, fecha_fin=None, fecha_inicio=None, sheet_name='Data'):
        """Ejecuta la consulta y escribe el resultado en un .xlsx por streaming.

        Evita cargar todo el resultado en memoria (DataFrame + workbook), que
        agotaba la RAM del servidor con informes grandes. Devuelve el nº de filas.
        """
        sql_content = self._prepare_sql(sql_content, fecha_fin, fecha_inicio)
        conn = self.conn_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql_content)
            return write_workbook_stream(cursor, path, sheet_name)
        except Exception as e:
            raise Exception(f"Error al ejecutar la consulta: {str(e)}")
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    def _prepare_sql(self, sql_content, fecha_fin, fecha_inicio):
        if fecha_inicio and fecha_fin and _to_date(fecha_inicio) > _to_date(fecha_fin):
            raise ValueError('La fecha de inicio no puede ser posterior a la fecha fin')
        sql_content = self.apply_date_filter(sql_content, fecha_fin, fecha_inicio)

        # DEBUG (opcional): SQL_DEBUG=1 guarda el SQL final para inspección
        if os.getenv('SQL_DEBUG'):
            try:
                with open('/tmp/debug_last_query.sql', 'w', encoding='utf-8') as f:
                    f.write(sql_content)
                print(f"DEBUG: SQL guardado en /tmp/debug_last_query.sql ({len(sql_content)} bytes)")
            except Exception as debug_err:
                print(f"DEBUG: No se pudo guardar debug SQL: {debug_err}")
        return sql_content

    def execute_from_file(self, file_path, fecha_fin=None, fecha_inicio=None):
        with open(file_path, 'r', encoding='latin-1') as f:
            sql_content = f.read()
        print(f"DEBUG: SQL file: {file_path}")
        print(f"DEBUG: SQL length: {len(sql_content)}")
        return self.execute_query(sql_content, fecha_fin, fecha_inicio)
