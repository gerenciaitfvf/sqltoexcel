import io
import os
from datetime import datetime
from openpyxl import Workbook

# Filas que se piden a la base de datos por lote al exportar en streaming.
STREAM_CHUNK_SIZE = 5000


def build_workbook(df, sheet_name='Data'):
    """Crea un Workbook con la fila de encabezados y luego los datos."""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append([str(c) for c in df.columns])
    for row in df.itertuples(index=False):
        ws.append([None if _is_null(v) else v for v in row])
    return wb


def _is_null(value):
    try:
        return value != value  # NaN / NaT
    except Exception:
        return False


def workbook_bytes(df, sheet_name='Data'):
    """Devuelve el .xlsx en memoria (para descargas web)."""
    buffer = io.BytesIO()
    build_workbook(df, sheet_name).save(buffer)
    return buffer.getvalue()


def write_workbook_stream(cursor, path, sheet_name='Data', chunk_size=STREAM_CHUNK_SIZE):
    """Escribe un .xlsx directamente desde un cursor DBAPI2, por lotes.

    Usa el modo write_only de openpyxl para no mantener el libro en memoria:
    imprescindible con resultados grandes en servidores con poca RAM.
    Devuelve el número de filas escritas.
    """
    wb = Workbook(write_only=True)
    ws = wb.create_sheet(sheet_name)
    ws.append([str(d[0]) for d in cursor.description])

    total = 0
    while True:
        rows = cursor.fetchmany(chunk_size)
        if not rows:
            break
        for row in rows:
            ws.append([None if _is_null(v) else v for v in row])
        total += len(rows)

    wb.save(path)
    return total


class ExcelExporter:
    def __init__(self):
        self.default_output_dir = os.path.join(os.getcwd(), 'output')
        if not os.path.exists(self.default_output_dir):
            os.makedirs(self.default_output_dir)

    def generate_filename(self, base_name):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name_without_ext = os.path.splitext(base_name)[0]
        return f"{name_without_ext}_{timestamp}.xlsx"

    def export(self, df, filename=None, sheet_name='Data'):
        if filename is None:
            filename = self.generate_filename('output')
        
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        output_path = os.path.join(self.default_output_dir, filename)
        
        try:
            build_workbook(df, sheet_name).save(output_path)
            return output_path
        except Exception as e:
            raise Exception(f"Error al exportar a Excel: {str(e)}")

    def get_output_dir(self):
        return self.default_output_dir
