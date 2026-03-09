# 📊 SQL Query to Excel Desktop (OpenConde)

Una herramienta de escritorio robusta desarrollada en **Python** con **PyQt6** para la ejecución automatizada de scripts SQL en servidores **Microsoft SQL Server** y la exportación directa de resultados a archivos **Excel (.xlsx)**.

---

## 🚀 Características Principal
* **Interfaz Gráfica (GUI):** Construida con PyQt6 para una gestión intuitiva de conexiones y archivos.
* **Gestor de Scripts:** Carga automática de archivos `.sql` desde un directorio local.
* **Motor de Datos:** Procesamiento eficiente de grandes volúmenes de datos mediante Pandas.
* **Portabilidad:** Capacidad de generar un archivo ejecutable `.exe` independiente para Windows.
* **Seguridad:** Manejo de credenciales mediante variables de entorno o entrada segura encriptada.

---

## 🏗️ Stack Tecnológico
* **Lenguaje:** Python 3.10+
* **Interfaz:** PyQt6 (Framework de escritorio)
* **Conectividad:** `pyodbc` + Microsoft ODBC Driver for SQL Server.
* **Procesamiento:** `Pandas` y `OpenPyXL`.
* **Distribución:** `PyInstaller` para el empaquetado del ejecutable.

---

## 📋 Requisitos Previos (Desarrollo)
Antes de comenzar, asegúrate de tener instalado:
1.  **Python 3.10+**
2.  **Microsoft ODBC Driver for SQL Server** (Versión 17 o 18 recomendada).
3.  **Entorno Virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

---

## 🛠️ Instalación y Configuración

1.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configurar conexión:**
    Crea un archivo `.env` o utiliza el panel de configuración de la app para definir:
    * `DB_HOST`: Dirección del servidor SQL.
    * `DB_NAME`: Nombre de la base de datos.
    * `DB_USER`: Usuario (SQL Auth).
    * `DB_PASS`: Contraseña.

3.  **Scripts SQL:**
    Coloca todos tus archivos `.sql` en la carpeta `Querys`. La aplicación los detectará automáticamente al iniciar.

---

## 📦 Generación del Ejecutable (.exe)
Para distribuir esta herramienta como una aplicación de Windows sin requerir instalación de Python en el cliente:

1. Crea un archivo `.spec` con el siguiente contenido:
```python
# SQL2Excel.spec
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('Querys', 'Querys')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SQL2Excel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

2. Genera el ejecutable:
```bash
pyinstaller SQL2Excel.spec
```

> ⚠️ **Importante:** PyInstaller genera ejecutables únicamente para el sistema operativo donde se ejecuta. Si estás en Linux, generará un binario de Linux, **no** un `.exe` de Windows.

### Compilar el `.exe` desde una máquina Windows

Si el entorno de desarrollo es Linux y necesitas el `.exe` para Windows, debes compilarlo desde una máquina Windows:

1. Copia el proyecto completo a la máquina Windows.
2. Instala **Python 3.10+** en esa máquina.
3. Crea el entorno virtual e instala las dependencias:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Genera el ejecutable:
   ```bash
   pyinstaller SQL2Excel.spec
   ```
5. El archivo `.exe` resultante estará en la carpeta `dist/`.

---

## 🐛 Bugs Conocidos y Correcciones

### Bug: Regex de reemplazo de fecha corrompía el SQL (corregido 2026-03-08)

**Archivo afectado:** `src/database/executor.py` → función `apply_date_filter`

**Síntoma:** Al ejecutar queries con parámetro de fecha (como `mega_query.sql`), SQL Server devolvía:
```
Incorrect syntax near ' AND [dbo].[cxP].ConsecutivoCompania ...
```

**Causa raíz:** El reemplazo regex usaba `rf"\1{fecha_str}\2"`. Cuando `fecha_str` era por ejemplo `2026-03-08`, Python generaba la cadena de reemplazo `\12026-03-08\2`. Python interpretaba `\12` (el `\1` + el `2` del año) como un **escape octal** (carácter ASCII 10 = salto de línea), en vez de "grupo 1 seguido del literal `2`".

Esto destruía silenciosamente el SQL:
| Original | Resultado con bug |
|---|---|
| `comp.Fecha < '2026-02-01'` | `(newline)026-03-08'` |

**Solución:** Cambiar `\1` y `\2` por la sintaxis no ambigua `\g<1>` y `\g<2>`:
```python
# ❌ Antes (bug):
rf"\1{fecha_str}\2"

# ✅ Después (correcto):
rf"\g<1>{fecha_str}\g<2>"
```

**Lección:** En Python, siempre usar `\g<N>` en reemplazos de `re.sub` cuando el texto adyacente puede comenzar con un dígito. La forma `\1` es ambigua porque `\12` puede interpretarse como escape octal o backreference al grupo 12.