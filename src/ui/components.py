# Импорт необходимых библиотек и модулей
import flet as ft                  # Фреймворк для создания пользовательского интерфейса
from utils.security import APICredentialManager #  Импорт класса  для работы с бд авторизации
from ui.styles import AppStyles    # Импорт стилей приложения
import asyncio                     # Библиотека для асинхронного программирования
import random

class MessageBubble(ft.Container):
    """
    Компонент "пузырька" сообщения в чате.
    
    Наследуется от ft.Container для создания стилизованного контейнера сообщения.
    Отображает сообщения пользователя и AI с разными стилями и позиционированием.
    
    Args:
        message (str): Текст сообщения для отображения
        is_user (bool): Флаг, указывающий, является ли это сообщением пользователя
    """
    def __init__(self, message: str, is_user: bool):
        # Инициализация родительского класса Container
        super().__init__()
        
        # Настройка отступов внутри пузырька
        self.padding = 10
        
        # Настройка скругления углов пузырька
        self.border_radius = 10
        
        # Установка цвета фона в зависимости от отправителя:
        # - Синий для сообщений пользователя
        # - Серый для сообщений AI
        self.bgcolor = ft.Colors.BLUE_700 if is_user else ft.Colors.GREY_700
        
        # Установка выравнивания пузырька:
        # - Справа для сообщений пользователя
        # - Слева для сообщений AI
        self.alignment = ft.alignment.center_right if is_user else ft.alignment.center_left
        
        # Настройка внешних отступов для создания эффекта диалога:
        # - Отступ слева для сообщений пользователя
        # - Отступ справа для сообщений AI
        # - Небольшие отступы сверху и снизу для разделения сообщений
        self.margin = ft.margin.only(
            left=50 if is_user else 0,      # Отступ слева
            right=0 if is_user else 50,      # Отступ справа
            top=5,                           # Отступ сверху
            bottom=5                         # Отступ снизу
        )
        
        # Создание содержимого пузырька
        self.content = ft.Column(
            controls=[
                # Текст сообщения с настройками отображения
                ft.Text(
                    value=message,                    # Текст сообщения
                    color=ft.Colors.WHITE,            # Белый цвет текста
                    size=16,                         # Размер шрифта
                    selectable=True,                 # Возможность выделения текста
                    weight=ft.FontWeight.W_400       # Нормальная толщина шрифта
                )
            ],
            tight=True  # Плотное расположение элементов в колонке
        )


class ModelSelector(ft.Dropdown):
    """
    Выпадающий список для выбора AI модели с функцией поиска.
    
    Наследуется от ft.Dropdown для создания кастомного выпадающего списка
    с дополнительным полем поиска для фильтрации моделей.
    
    Args:
        models (list): Список доступных моделей в формате:
                      [{"id": "model-id", "name": "Model Name"}, ...]
    """
    def __init__(self, models: list):
        # Инициализация родительского класса Dropdown
        super().__init__()
        
        # Применение стилей из конфигурации к компоненту
        for key, value in AppStyles.MODEL_DROPDOWN.items():
            setattr(self, key, value)
            
        # Настройка внешнего вида выпадающего списка
        self.label = None                    # Убираем текстовую метку
        self.hint_text = "Выбор модели"      # Текст-подсказка
        
        # Создание списка опций из предоставленных моделей
        self.options = [
            ft.dropdown.Option(
                key=model['id'],             # ID модели как ключ
                text=model['name']           # Название модели как отображаемый текст
            ) for model in models
        ]
        
        # Сохранение полного списка опций для фильтрации
        self.all_options = self.options.copy()
        
        # Установка начального значения (первая модель из списка)
        self.value = models[0]['id'] if models else None
        
        # Создание поля поиска для фильтрации моделей
        self.search_field = ft.TextField(
            on_change=self.filter_options,        # Функция обработки изменений
            hint_text="Поиск модели",            # Текст-подсказка в поле поиска
            **AppStyles.MODEL_SEARCH_FIELD       # Применение стилей из конфигурации
        )

    def filter_options(self, e):
        """
        Фильтрация списка моделей на основе введенного текста поиска.
        
        Args:
            e: Событие изменения текста в поле поиска
        """
        # Получение текста поиска в нижнем регистре
        search_text = self.search_field.value.lower() if self.search_field.value else ""
        
        # Если поле поиска пустое - показываем все модели
        if not search_text:
            self.options = self.all_options
        else:
            # Фильтрация моделей по тексту поиска
            # Ищем совпадения в названии или ID модели
            self.options = [
                opt for opt in self.all_options
                if search_text in opt.text.lower() or search_text in opt.key.lower()
            ]
        
        # Обновление интерфейса для отображения отфильтрованного списка
        e.page.update()


class AuthorizationWindow(ft.UserControl):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.db = APICredentialManager()

        self.api_key_field = ft.TextField(label="API-ключ OpenRouter.ai", password=True)
        self.pin_field = ft.TextField(label="Введите PIN", password=True, max_length=4, visible=False)
        self.message_text = ft.Text("", color=ft.colors.RED)
        self.auth_button = ft.ElevatedButton("Войти", on_click=self.handle_auth)
        self.reset_button = ft.TextButton("Сбросить ключи", on_click=self.reset_auth, visible=False)

        self.controls = [
            ft.Text("Аутентификация", size=22, weight=ft.FontWeight.BOLD),
            self.api_key_field,
            self.pin_field,
            self.message_text,
            ft.Row([self.auth_button, self.reset_button])
        ]

        self.check_existing_users()

    def check_existing_users(self):
        users = self.db.get_all_users()
        if users:
            # Если есть хотя бы одна запись — входим по PIN
            self.api_key_field.visible = False
            self.pin_field.visible = True
            self.reset_button.visible = True
            self.auth_button.text = "Войти по PIN"
        else:
            # Если нет — вводим API-ключ
            self.api_key_field.visible = True
            self.pin_field.visible = False
            self.reset_button.visible = False
            self.auth_button.text = "Сохранить ключ"

    def reset_auth(self, e):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auth_data")
        conn.commit()
        self.check_existing_users()
        self.api_key_field.value = ""
        self.pin_field.value = ""
        self.message_text.value = "Все ключи сброшены."
        self.update()

    def handle_auth(self, e):
        users = self.db.get_all_users()
        if users:
            # Ввод PIN
            try:
                pin = int(self.pin_field.value)
            except ValueError:
                self.message_text.value = "PIN должен быть числом."
                self.update()
                return

            user = self.db.verify_pin(pin)
            if user:
                self.on_success(user["api_key"])
            else:
                self.message_text.value = "Неверный PIN."
            self.update()
        else:
            # Ввод API-ключа
            api_key = self.api_key_field.value.strip()
            if not api_key:
                self.message_text.value = "Введите API-ключ."
                self.update()
                return

            async def async_check():
                valid, balance = await self.check_key_balance(api_key)
                if valid and balance > 0:
                    pin = int("".join([str(random.randint(0, 9)) for _ in range(4)]))
                    self.db.save_security(api_key, pin)
                    self.message_text.value = f"Ключ сохранён. Ваш PIN: {pin}"
                    self.check_existing_users()
                    self.update()
                else:
                    self.message_text.value = "Неверный ключ или нулевой баланс."
                    self.update()

            asyncio.create_task(async_check())

    async def check_key_balance(self, key):
        # Заглушка проверки баланса
        await asyncio.sleep(1)
        return True, 100  # Можно подключить реальный API запрос

    def build(self):
        return ft.Column(self.controls, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
