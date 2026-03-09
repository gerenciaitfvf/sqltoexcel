import re
import pandas as pd
from datetime import datetime


class QueryExecutor:
    def __init__(self, connection_manager):
        self.conn_manager = connection_manager

    def has_date_params(self, sql_content):
        patterns = [
            r"comp\.Fecha\s*<\s*'[\d-]+'",
            r"mb\.Fecha\s*<\s*'[\d-]+'",
            r"comp\.Fecha\s*>\s*'[\d-]+'",
            r"mb\.Fecha\s*>\s*'[\d-]+'",
        ]
        for pattern in patterns:
            if re.search(pattern, sql_content, re.IGNORECASE):
                return True
        return False

    def apply_date_filter(self, sql_content, fecha_fin):
        fecha_str = fecha_fin.strftime('%Y-%m-%d') if isinstance(fecha_fin, datetime) else str(fecha_fin)
        
        sql_content = re.sub(
            r"(comp\.Fecha\s*<\s*')[\d-]+(')",
            rf"\g<1>{fecha_str}\g<2>",
            sql_content,
            flags=re.IGNORECASE
        )
        sql_content = re.sub(
            r"(mb\.Fecha\s*<\s*')[\d-]+(')",
            rf"\g<1>{fecha_str}\g<2>",
            sql_content,
            flags=re.IGNORECASE
        )
        
        return sql_content

    def execute_query(self, sql_content, fecha_fin=None):
        if fecha_fin and self.has_date_params(sql_content):
            sql_content = self.apply_date_filter(sql_content, fecha_fin)
        
        # DEBUG: guardar el SQL final a un archivo para inspección
        try:
            with open('/tmp/debug_last_query.sql', 'w', encoding='utf-8') as f:
                f.write(sql_content)
            print(f"DEBUG: SQL guardado en /tmp/debug_last_query.sql ({len(sql_content)} bytes)")
        except Exception as debug_err:
            print(f"DEBUG: No se pudo guardar debug SQL: {debug_err}")

        conn = self.conn_manager.get_connection()
        try:
            df = pd.read_sql(sql_content, conn)
            return df
        except Exception as e:
            raise Exception(f"Error al ejecutar la consulta: {str(e)}")

    def execute_from_file(self, file_path, fecha_fin=None):
        with open(file_path, 'r', encoding='latin-1') as f:
            sql_content = f.read()
        print(f"DEBUG: SQL file: {file_path}")
        print(f"DEBUG: SQL length: {len(sql_content)}")
        return self.execute_query(sql_content, fecha_fin)
