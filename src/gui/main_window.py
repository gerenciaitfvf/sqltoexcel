import os
import sys
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QPushButton, QLabel, QMessageBox,
                             QDateEdit, QProgressBar, QStatusBar, QMenuBar, QMenu)
from PyQt6.QtCore import QThread, Qt, QDate
from PyQt6.QtGui import QAction

from src.gui.config_dialog import ConfigDialog
from src.database.connection import ConnectionManager
from src.database.executor import QueryExecutor
from src.export.excel_writer import ExcelExporter


class ExecuteQueryThread(QThread):
    def __init__(self, executor, file_path, fecha_fin):
        super().__init__()
        self.executor = executor
        self.file_path = file_path
        self.fecha_fin = fecha_fin
        self.df = None
        self.error = None

    def run(self):
        try:
            self.df = self.executor.execute_from_file(self.file_path, self.fecha_fin)
        except Exception as e:
            self.error = str(e)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.conn_manager = ConnectionManager()
        self.executor = QueryExecutor(self.conn_manager)
        self.exporter = ExcelExporter()
        
        if getattr(sys, 'frozen', False):
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_path = os.getcwd()
        self.querys_dir = os.path.join(base_path, 'Querys')
        
        self.current_file = None
        self.fecha_fin = None
        self.auto_connect_attempted = False
        self.init_ui()
        self.auto_connect()

    def init_ui(self):
        self.setWindowTitle("SQL to Excel")
        self.resize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        header = QLabel("Seleccione un archivo SQL para ejecutar:")
        layout.addWidget(header)

        self.script_list = QListWidget()
        self.script_list.itemClicked.connect(self.on_script_selected)
        layout.addWidget(self.script_list)

        self.param_label = QLabel("")
        layout.addWidget(self.param_label)

        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDate(QDate.currentDate())
        self.fecha_input.setMaximumDate(QDate.currentDate())
        self.fecha_input.setVisible(False)
        self.fecha_input.dateChanged.connect(self.on_fecha_changed)
        layout.addWidget(self.fecha_input)

        btn_layout = QHBoxLayout()
        self.execute_btn = QPushButton("Ejecutar y Exportar")
        self.execute_btn.clicked.connect(self.execute_query)
        self.execute_btn.setEnabled(False)
        
        btn_layout.addWidget(self.execute_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setFormat("Ejecutando consulta... %(percent)s")
        self.progress.setTextVisible(True)
        layout.addWidget(self.progress)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.load_scripts()

    def _create_menu(self):
        pass

    def load_scripts(self):
        self.script_list.clear()
        if os.path.exists(self.querys_dir):
            for file in sorted(os.listdir(self.querys_dir)):
                if file.endswith('.sql'):
                    self.script_list.addItem(file)
        else:
            QMessageBox.warning(self, "Advertencia", f"No se encontró la carpeta: {self.querys_dir}")

    def on_script_selected(self, item):
        self.current_file = os.path.join(self.querys_dir, item.text())
        
        with open(self.current_file, 'r', encoding='latin-1') as f:
            sql_content = f.read()
        
        if self.executor.has_date_params(sql_content):
            self.param_label.setText("Fecha fin ( parámetro ):")
            self.fecha_input.setVisible(True)
            self.fecha_fin = self.fecha_input.date().toPyDate()
        else:
            self.param_label.setText("")
            self.fecha_input.setVisible(False)
            self.fecha_fin = None
        
        self.execute_btn.setEnabled(True)
        self.status_bar.showMessage(f"Seleccionado: {item.text()}")

    def on_fecha_changed(self, date):
        self.fecha_fin = date.toPyDate()

    def open_config(self):
        dialog = ConfigDialog(self.conn_manager, self)
        dialog.exec()

    def execute_query(self):
        if not self.current_file:
            return
        
        if not self.conn_manager.is_connected():
            try:
                self.conn_manager.connect()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo conectar: {str(e)}")
                return

        self.execute_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.progress.setFormat("Conectado - Ejecutando consulta...")
        self.status_bar.showMessage("Ejecutando consulta...")

        self.thread = ExecuteQueryThread(self.executor, self.current_file, self.fecha_fin)
        self.thread.finished.connect(self.on_query_finished)
        self.thread.start()

    def on_query_finished(self):
        if self.thread.error:
            self.progress.setVisible(False)
            QMessageBox.critical(self, "Error", f"Error al ejecutar consulta: {self.thread.error}")
            self.execute_btn.setEnabled(True)
            self.status_bar.showMessage("Error en la consulta")
            return

        self.progress.setFormat("Exportando a Excel...")
        
        df = self.thread.df
        
        if df is not None and not df.empty:
            try:
                output_path = self.exporter.export(df, os.path.basename(self.current_file))
                self.progress.setVisible(False)
                QMessageBox.information(self, "Éxito", f"Archivo exportado:\n{output_path}")
                self.status_bar.showMessage(f"Exportado: {output_path}")
            except Exception as e:
                self.progress.setVisible(False)
                QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")
                self.status_bar.showMessage("Error al exportar")
        else:
            self.progress.setVisible(False)
            QMessageBox.warning(self, "Sin datos", "La consulta no devolvió resultados.")
            self.status_bar.showMessage("Sin datos")

        self.execute_btn.setEnabled(True)

    def auto_connect(self):
        if not self.conn_manager.has_config():
            self.status_bar.showMessage("Sin configuración de base de datos")
            return
        
        try:
            self.conn_manager.connect()
            self.status_bar.showMessage("Conectado a la base de datos")
        except Exception as e:
            self.status_bar.showMessage(f"Error de conexión: {str(e)}")
