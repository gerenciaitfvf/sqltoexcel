from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt


class ConfigDialog(QDialog):
    def __init__(self, connection_manager, parent=None):
        super().__init__(parent)
        self.connection_manager = connection_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Configuración de Conexión")
        self.setModal(True)
        self.resize(450, 280)

        layout = QVBoxLayout()

        self.server_input = self._create_field("Servidor:", self.connection_manager.config['server'])
        self.database_input = self._create_field("Base de datos:", self.connection_manager.config['database'])
        self.user_input = self._create_field("Usuario:", self.connection_manager.config['user'])
        self.password_input = self._create_field("Contraseña:", self.connection_manager.config['password'])
        self.driver_input = self._create_field("Driver:", self.connection_manager.config['driver'])

        layout.addLayout(self.server_input['layout'])
        layout.addLayout(self.database_input['layout'])
        layout.addLayout(self.user_input['layout'])
        layout.addLayout(self.password_input['layout'])
        layout.addLayout(self.driver_input['layout'])

        btn_layout = QHBoxLayout()
        self.test_btn = QPushButton("Probar Conexión")
        self.save_btn = QPushButton("Guardar")
        self.cancel_btn = QPushButton("Cancelar")

        self.test_btn.clicked.connect(self.test_connection)
        self.save_btn.clicked.connect(self.save_config)
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.test_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _create_field(self, label_text, default_value):
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(100)
        input_field = QLineEdit(default_value)
        if label_text == "Contraseña:":
            input_field.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(label)
        layout.addWidget(input_field)
        return {'layout': layout, 'input': input_field}

    def test_connection(self):
        server = self.server_input['input'].text()
        database = self.database_input['input'].text()
        user = self.user_input['input'].text()
        password = self.password_input['input'].text()
        driver = self.driver_input['input'].text()
        
        try:
            temp_config = self.connection_manager.config.copy()
            self.connection_manager.config['server'] = server
            self.connection_manager.config['database'] = database
            self.connection_manager.config['user'] = user
            self.connection_manager.config['password'] = password
            self.connection_manager.config['driver'] = driver
            self.connection_manager.connect()
            self.connection_manager.disconnect()
            self.connection_manager.config = temp_config
            QMessageBox.information(self, "Éxito", "Conexión exitosa!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo conectar: {str(e)}")

    def save_config(self):
        self.connection_manager.save_config(
            server=self.server_input['input'].text(),
            database=self.database_input['input'].text(),
            user=self.user_input['input'].text(),
            password=self.password_input['input'].text(),
            driver=self.driver_input['input'].text()
        )
        self.accept()
