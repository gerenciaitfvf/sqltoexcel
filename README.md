# 📊 SQL Query to Excel Desktop

## 📖 Descripción del Proyecto

**SQL2Excel** es una herramienta de escritorio desarrollada en Python enfocada en la automatización de la ejecución de scripts SQL hacia bases de datos de **Microsoft SQL Server**, y su posterior exportación directa e inmediata a formato **Excel (.xlsx)**. Cuenta con una Interfaz Gráfica de Usuario (GUI) intuitiva que facilita su configuración y uso diario para analistas y desarrolladores.

---

## 🏗️ Arquitectura y Estructura de Archivos

El proyecto está diseñado siguiendo una estructura modular para separar la lógica de conexión, la interfaz gráfica y los procesos de exportación de datos.

### 📂 Rutas Clave del Proyecto

* **`main.py`**
  Archivo principal (entry point) de la aplicación. Inicializa la interfaz gráfica utilizando PyQt6 y lanza la ventana principal.
* **`AGENTS.MD`**
  Documentación interna que detalla las características principales del proyecto, stack tecnológico y la forma de empaquetar el código en un ejecutable de Windows.
* **`requirements.txt`**
  Listado de dependencias y librerías de Python necesarias para ejecutar la aplicación.
* **`.env`** (Archivo de configuración local)
  Contiene las variables de entorno para la configuración de la base de datos (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`).
* **`Querys/`** _(Directorio)_
  Carpeta destinada para almacenar todos los archivos con extensión `.sql`. La aplicación escanea este directorio para procesarlos automáticamente.

### 🧩 Código Fuente (`src/`)

* **`src/database/`** (Lógica de Base de Datos)
  * `connection.py`: Encargado de gestionar, y asegurar la conexión con Microsoft SQL Server usando la cadena de conexión de ODBC.
  * `executor.py`: Realiza la ejecución de las consultas SQL llamando a la conexión proporcionada.
* **`src/export/`** (Lógica de Exportación)
  * `excel_writer.py`: Contiene la lógica responsable de tomar los `DataFrames` (resultados del query) y transformarlos físicamente a los archivos `.xlsx`.
* **`src/gui/`** (Interfaz Gráfica)
  * `main_window.py`: Define y controla la ventana principal de interacciones del usuario de la herramienta.
  * `config_dialog.py`: Se encarga de la ventana emergente/modal para ingresar y guardar las configuraciones de la conexión a la base de datos dentro de la aplicación.

---

## 📚 Librerías Principales

El sistema logra su funcionamiento gracias al uso del siguiente stack de Python:

* **[PyQt6](https://pypi.org/project/PyQt6/):** Framework para la creación de la Interfaz Gráfica de Usuario (GUI). Provee todos los componentes visuales.
* **[pyodbc](https://pypi.org/project/pyodbc/):** Módulo de conexión ODBC. Se requiere tener instalado el _Microsoft ODBC Driver for SQL Server_ a nivel sistema para funcionar.
* **[pandas](https://pypi.org/project/pandas/):** Utilizado por su excelente y rápida capacidad de procesamiento de los conjuntos de datos obtenidos (DataFrames).
* **[openpyxl](https://pypi.org/project/openpyxl/):** El motor sobre el cual Pandas se apoya para la escritura de los documentos de Microsoft Excel (`.xlsx`).
* **[python-dotenv](https://pypi.org/project/python-dotenv/):** Lectura del archivo `.env` garantizando un manejo seguro de las credenciales fuera del código fuente.
* **[pyinstaller](https://pypi.org/project/pyinstaller/):** Permite compilar/empaquetar la aplicación de Python y sus dependencias en un único ejecutable (`.exe`).

---

## 🚀 Uso Rápido

1. Crear y configurar un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```
2. Instalar las dependencias listadas:
   ```bash
   pip install -r requirements.txt
   ```
3. Completar las conexiones en el archivo `.env` o a través de la UI.
4. Ejecutar la aplicación:
   ```bash
   python main.py
   ```

---

## 🌐 Versión Web (red local)

Además de la app de escritorio, el proyecto incluye una versión web en `web/` para desplegar en un servidor de la red local. El usuario abre la página, elige el informe (y la fecha de corte si el SQL la usa) y descarga el `.xlsx`. No tiene login, así que **no debe exponerse a internet**.

* `web/app.py`: servidor FastAPI. Reutiliza `src/database` y `src/export`.
* `web/static/index.html`: la página de informes.
* Los informes son los `.sql` de `Querys/`; la lista se relee en cada carga de página.
* **Rango de fechas:** si un `.sql` contiene `comp.Fecha > 'AAAA-MM-DD'` o `mb.Fecha > '...'`, aparece el campo **Desde**; si contiene `... < 'AAAA-MM-DD'`, aparece **Hasta**. Ambas fechas son inclusivas: Desde 01/01/2025 y Hasta 31/01/2026 se aplican como `> '2024-12-31'` y `< '2026-02-01'`. Lo mismo vale para la app de escritorio.

### Opción A: Docker (recomendado)

1. Crear el `.env` en la raíz con `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS` (idealmente un usuario de SQL Server de solo lectura).
2. Levantar el servicio:
   ```bash
   docker compose up -d --build
   ```
3. Abrir `http://<ip-del-servidor>:8000` desde cualquier equipo de la red.

`Querys/` se monta como volumen: para añadir o cambiar un informe basta con copiar el `.sql` a esa carpeta, sin reconstruir.

### Opción B: Sin Docker

```bash
python -m venv venv-web
source venv-web/bin/activate
pip install -r web/requirements.txt
uvicorn web.app:app --host 0.0.0.0 --port 8000 --workers 2
```

Variables opcionales: `QUERYS_DIR` (otra carpeta de `.sql`) y `SQL_DEBUG=1` (guarda el último SQL ejecutado en `/tmp/debug_last_query.sql`).
