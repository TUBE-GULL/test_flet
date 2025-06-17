# Импорт необходимых библиотек
import sqlite3      # Библиотека для работы с SQLite базой данных
import json        # Библиотека для работы с JSON форматом
from datetime import datetime  # Библиотека для работы с датой и временем
import threading   # Библиотека для обеспечения потокобезопасности
    
class APICredentialManager :
    """
    Класс для хранения данных пользователя  в SQLite базе данных
    
    
    """
    def __init__(self):
        """
        Инициализация базы данных.
        
        Создает:
        - Файл базы данных SQLite
        - Потокобезопасное хранилище соединений
        - Необходимые таблицы в базе данных
        """
        
        # имя файла SQLite базы  данных 
        self.db_name = 'api_credentials.db'
        
        # Создание потокобезопасного хранилища соединений
        # Каждый поток будет иметь свое собственное соединение с базой
        self.local = threading.local()
        
        # Создание необходимых таблиц при инициализации
        self.create_tables()


    def get_connection(self):
        """
        Получение соединения с базой данных для текущего потока.
        
        Returns:
            sqlite3.Connection: Объект соединения с базой данных
            
        Note:
            Каждый поток получает свое собственное соединение,
            что обеспечивает потокобезопасность работы с базой.
        """
        # Проверяем, есть ли уже соединение в текущем потоке
        if not hasattr(self.local, 'connection'):
            # Если соединения нет - создаем новое
            self.local.connection = sqlite3.connect(self.db_name)
        return self.local.connection  

    def create_tables(self):
        """
        Создание необходимых таблиц в базе данных.

        Таблица auth_data:
        - id         Уникальный идентификатор (первичный ключ)
        - api_key    API-ключ OpenRouter
        - pin_code   4-значный PIN-код
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auth_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT NOT NULL,
                pin_code INTEGER NOT NULL
            )
        ''')

        conn.commit()
        conn.close()


    def save_security(self, api_key, pin):
        """
        Сохранение данных пользователя в базе данных.
    
        Args:
            api_key (str): API-ключ OpenRouter
            pin (int): 4-значный PIN-код
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO auth_data (api_key, pin_code)
            VALUES (?, ?)
        ''', (api_key, pin))
        conn.commit()

    
    def  search_user(self, api_key):
        """
        поиск пользователя в  database по api_key 

        Args:
            api_key (str): API-ключ OpenRouter 
            
        Returns :
            dict | None: Данные пользователя (id, api_key, pin_code) или None, если не найден
        """
        
        conn = self.get_connection() # Получение соединения  для текущего потока 
        cursor = conn.cursor()
        
        cursor.execute('''
                    SELECT id, api_key, pin_code FROM auth_data WHERE api_key = ?
                       ''', (api_key,))
        
        row = cursor.fetchone()
        
        if row:
            return {
                "id": row[0],
                "api_key": row[1],
                "pin_code": row[2]
            }
        else:
            return None


    def verify_pin(self, pin_code):
        """
        Проверка, существует ли введённый PIN-код в базе.

        Args:
            pin_code (int): PIN-код для проверки

        Returns:
            dict | None: Данные пользователя или None, если PIN не найден
        """

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, api_key, pin_code FROM auth_data WHERE pin_code = ?
        ''', (pin_code,))

        row = cursor.fetchone()

        if row:
            return {
                "id": row[0],
                "api_key": row[1],
                "pin_code": row[2]
            }
        else:
            return None


    def __del__(self):
        """
        Деструктор класса.
        
        Закрывает соединения с базой данных при уничтожении объекта,
        предотвращая утечки ресурсов.
        """
        # Проверка наличия соединения в текущем потоке
        if hasattr(self.local, 'connection'):
            self.local.connection.close()  # Закрытие соединения




    def get_all_users(self):
        """
        Получение всех записей из таблицы auth_data.

        Returns:
            list of dict: Список словарей с данными пользователей.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, api_key, pin_code FROM auth_data')
        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "api_key": row[1],
                "pin_code": row[2]
            }
            for row in rows
        ]
#
# class APICredential: