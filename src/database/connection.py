import os
import pymssql
from dotenv import load_dotenv, set_key


class ConnectionManager:
    def __init__(self):
        load_dotenv()
        self.connection = None
        self.env_file = os.path.join(os.getcwd(), '.env')
        self.config = {
            'server': os.getenv('DB_HOST', ''),
            'port': os.getenv('DB_PORT', '1433'),
            'database': os.getenv('DB_NAME', ''),
            'user': os.getenv('DB_USER', ''),
            'password': os.getenv('DB_PASS', ''),
        }

    def has_config(self):
        return all([self.config['server'], self.config['database'], self.config['user'], self.config['password']])

    def save_config(self, server=None, database=None, user=None, password=None, driver=None):
        if server:
            self.config['server'] = server
            set_key(self.env_file, 'DB_HOST', server)
        if database:
            self.config['database'] = database
            set_key(self.env_file, 'DB_NAME', database)
        if user:
            self.config['user'] = user
            set_key(self.env_file, 'DB_USER', user)
        if password:
            self.config['password'] = password
            set_key(self.env_file, 'DB_PASS', password)

    def connect(self):
        try:
            port = int(self.config['port']) if self.config['port'] else 1433
            self.connection = pymssql.connect(
                server=self.config['server'],
                port=port,
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database']
            )
            return True
        except Exception as e:
            raise Exception(f"Error al conectar con la base de datos: {str(e)}")

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def is_connected(self):
        if self.connection:
            try:
                self.connection.cursor()
                return True
            except:
                return False
        return False

    def get_connection(self):
        if not self.connection or not self.is_connected():
            self.connect()
        return self.connection
