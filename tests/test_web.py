import io
import re
from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

import web.app as webapp
from src.database.connection import ConnectionManager
from src.database.executor import QueryExecutor

ROOT = Path(__file__).resolve().parent.parent

SQL_RANGO = "SELECT * FROM t comp WHERE comp.Fecha > '2024-12-31' AND comp.Fecha < '2026-02-01'"
SQL_BANCO = "SELECT * FROM mb WHERE mb.Fecha > '2021-06-30'\n\tAND mb.Fecha < '2026-02-01'"
SQL_SIMPLE = "SELECT 1 AS uno"


@pytest.fixture
def querys(tmp_path, monkeypatch):
    (tmp_path / 'rango.sql').write_text(SQL_RANGO, encoding='latin-1')
    (tmp_path / 'banco.sql').write_text(SQL_BANCO, encoding='latin-1')
    (tmp_path / 'simple.sql').write_text(SQL_SIMPLE, encoding='latin-1')
    (tmp_path / 'acentos_ñ.sql').write_text("SELECT 'año' AS c", encoding='latin-1')
    (tmp_path / 'no_sql.txt').write_text('ignorar')
    monkeypatch.setattr(webapp, 'QUERYS_DIR', tmp_path)
    return tmp_path


@pytest.fixture
def fake_db(monkeypatch):
    """Sustituye la BD: guarda el SQL final y devuelve un DataFrame fijo."""
    state = {'sql': None, 'df': pd.DataFrame({
        'Cuenta': ['A', 'B', 'C'],
        'Monto': [1.5, float('nan'), 3.0],
        'Fecha': pd.to_datetime(['2026-01-01', None, '2026-03-01']),
    }), 'disconnects': 0}

    class FakeCursor:
        def __init__(self, df):
            self.error = df if isinstance(df, Exception) else None
            self.description = [] if self.error else [(str(c),) for c in df.columns]
            self.rows = [] if self.error else list(df.itertuples(index=False, name=None))
            self.pos = 0

        def execute(self, sql):
            state['sql'] = sql
            if self.error:
                raise self.error

        def fetchmany(self, n):
            chunk = self.rows[self.pos:self.pos + n]
            self.pos += len(chunk)
            return chunk

        def close(self):
            pass

    class FakeConnection:
        def cursor(self):
            return FakeCursor(state['df'])

    monkeypatch.setattr(ConnectionManager, 'has_config', lambda self: True)
    monkeypatch.setattr(ConnectionManager, 'get_connection', lambda self: FakeConnection())

    def disconnect(self):
        state['disconnects'] += 1
    monkeypatch.setattr(ConnectionManager, 'disconnect', disconnect)
    return state


@pytest.fixture
def client(querys, fake_db):
    return TestClient(webapp.app)


# ---------- executor ----------

def test_rango_inclusivo_reemplaza_todas_las_apariciones():
    ex = QueryExecutor(None)
    sql = ' UNION ALL '.join([SQL_RANGO] * 9)
    out = ex.apply_date_filter(sql, date(2026, 6, 30), date(2026, 3, 1))
    assert out.count("comp.Fecha > '2026-02-28'") == 9
    assert out.count("comp.Fecha < '2026-07-01'") == 9
    assert '2024-12-31' not in out and '2026-02-01' not in out


def test_fechas_originales_dejan_sql_igual():
    ex = QueryExecutor(None)
    assert ex.apply_date_filter(SQL_RANGO, date(2026, 1, 31), date(2025, 1, 1)) == SQL_RANGO


def test_cruce_de_anio_y_bisiesto():
    ex = QueryExecutor(None)
    out = ex.apply_date_filter(SQL_RANGO, date(2028, 2, 29), date(2026, 1, 1))
    assert "> '2025-12-31'" in out and "< '2028-03-01'" in out


def test_solo_fin_no_toca_inicio():
    out = QueryExecutor(None).apply_date_filter(SQL_BANCO, date(2026, 10, 31))
    assert "mb.Fecha > '2021-06-30'" in out and "mb.Fecha < '2026-11-01'" in out


def test_default_dates():
    assert QueryExecutor(None).default_dates(SQL_RANGO) == (date(2025, 1, 1), date(2026, 1, 31))
    assert QueryExecutor(None).default_dates(SQL_SIMPLE) == (None, None)


def test_executor_valida_orden():
    with pytest.raises(ValueError):
        QueryExecutor(None).execute_query(SQL_RANGO, date(2026, 1, 1), date(2026, 2, 1))


def test_querys_reales_detectados():
    ex = QueryExecutor(None)
    mega = (ROOT / 'Querys' / 'mega_query.sql').read_text(encoding='latin-1')
    assert ex.has_start_param(mega) and ex.has_end_param(mega)
    out = ex.apply_date_filter(mega, date(2026, 6, 30), date(2026, 3, 1))
    assert len(re.findall(r"comp\.Fecha > '2026-02-28'", out, re.I)) == 9
    assert len(re.findall(r"comp\.Fecha < '2026-07-01'", out, re.I)) == 9


# ---------- API ----------

def test_pagina_principal(client):
    r = client.get('/')
    assert r.status_code == 200 and 'Informes financieros' in r.text


def test_listado(client):
    data = {i['nombre']: i for i in client.get('/api/informes').json()}
    assert set(data) == {'acentos_ñ', 'banco', 'rango', 'simple'}
    assert data['rango'] == {'nombre': 'rango', 'usa_fecha_inicio': True,
                             'usa_fecha_fin': True, 'inicio_default': '2025-01-01'}
    assert data['banco']['inicio_default'] == '2021-07-01'
    assert data['simple']['usa_fecha_inicio'] is False and data['simple']['usa_fecha_fin'] is False


def test_listado_se_refresca_sin_reiniciar(client, querys):
    (querys / 'nuevo.sql').write_text(SQL_SIMPLE)
    assert 'nuevo' in [i['nombre'] for i in client.get('/api/informes').json()]


def test_descarga_con_rango(client, fake_db):
    r = client.get('/api/informes/rango', params={'inicio': '2026-03-01', 'fin': '2026-06-30'})
    assert r.status_code == 200
    assert r.headers['content-type'].startswith('application/vnd.openxmlformats')
    assert "filename=\"rango_2026-03-01_a_2026-06-30.xlsx\"" in r.headers['content-disposition']
    assert r.headers['x-filas'] == '3'
    assert "> '2026-02-28'" in fake_db['sql'] and "< '2026-07-01'" in fake_db['sql']
    filas = [[c.value for c in row] for row in load_workbook(io.BytesIO(r.content)).active.iter_rows()]
    assert filas[0] == ['Cuenta', 'Monto', 'Fecha']
    assert len(filas) == 4  # encabezado + 3 filas, ninguna perdida
    assert filas[2][1:] == [None, None]  # NaN/NaT -> celdas vacías
    assert fake_db['disconnects'] == 1


def test_descarga_sin_inicio_usa_el_del_sql(client, fake_db):
    r = client.get('/api/informes/rango', params={'fin': '2026-06-30'})
    assert r.status_code == 200
    assert "> '2024-12-31'" in fake_db['sql']


def test_descarga_sin_fechas(client, fake_db):
    r = client.get('/api/informes/simple')
    assert r.status_code == 200 and fake_db['sql'] == SQL_SIMPLE


def test_nombre_con_acentos(client):
    r = client.get('/api/informes/acentos_ñ')
    assert r.status_code == 200
    assert 'acentos_%C3%B1_' in r.headers['content-disposition']


def test_resultado_vacio(client, fake_db):
    fake_db['df'] = pd.DataFrame({'a': []})
    r = client.get('/api/informes/simple')
    assert r.status_code == 200 and r.headers['x-filas'] == '0'


@pytest.mark.parametrize('params, detalle', [
    ({'inicio': '2026-03-01'}, 'requiere la fecha fin'),
    ({'inicio': '2026-07-01', 'fin': '2026-06-30'}, 'no puede ser posterior'),
])
def test_validaciones_400(client, params, detalle):
    r = client.get('/api/informes/rango', params=params)
    assert r.status_code == 400 and detalle in r.json()['detail']


def test_fecha_invalida_422(client):
    assert client.get('/api/informes/rango', params={'fin': '31/12/2026'}).status_code == 422


@pytest.mark.parametrize('nombre', ['no_existe', '..%2F..%2Fetc%2Fpasswd', 'no_sql', '..%2Fweb%2Fapp'])
def test_nombres_invalidos_404(client, nombre):
    assert client.get(f'/api/informes/{nombre}').status_code == 404


def test_error_de_bd_se_reporta_y_cierra_conexion(client, fake_db):
    fake_db['df'] = Exception("Invalid object name 'COMPROBANTE'")
    r = client.get('/api/informes/simple')
    assert r.status_code == 500 and 'COMPROBANTE' in r.json()['detail']
    assert fake_db['disconnects'] == 1


def test_sin_configuracion(querys, monkeypatch):
    monkeypatch.setattr(ConnectionManager, 'has_config', lambda self: False)
    r = TestClient(webapp.app).get('/api/informes/simple')
    assert r.status_code == 500 and '.env' in r.json()['detail']
