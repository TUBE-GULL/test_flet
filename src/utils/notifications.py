import os
import smtplib
from email.mime.text import MIMEText
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

# Конфигурация
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

NOTIFICATION_METHOD = os.getenv("NOTIFICATION_METHOD", "email").lower()


# Отправка email уведомления
def send_email_notification(subject: str, message: str):
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS  # Можно задать отдельный email для админа

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print("📧 Email-уведомление отправлено.")
    except Exception as e:
        print(f"❌ Ошибка отправки email: {e}")


# Отправка telegram уведомления
async def send_telegram_notification(message: str):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print("📨 Telegram-уведомление отправлено.")
    except Exception as e:
        print(f"❌ Ошибка отправки telegram: {e}")


# Выбор способа отправки уведомлений
def notify_admin(subject: str, message: str):
    if NOTIFICATION_METHOD == "email":
        send_email_notification(subject, message)
    elif NOTIFICATION_METHOD == "telegram":
        import asyncio
        asyncio.run(send_telegram_notification(f"{subject}\n\n{message}"))
    else:
        print("❌ Способ уведомлений не настроен или указан неверно.")

