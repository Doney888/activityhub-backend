from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
import random
import string
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_FROM", os.getenv("MAIL_USERNAME")),
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587)), 
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

def generate_email_token():
    return str(uuid.uuid4())

def generate_2fa_code():
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=6))

async def send_verification_link(email: EmailStr, token: str):
    domain = os.getenv("DOMAIN", "http://127.0.0.1:8000")
    link = f"{domain}/auth/verify-email?token={token}"
    html = f"""
    <h3>Добро пожаловать в ActivityHub!</h3>
    <p>Нажмите кнопку для активации аккаунта:</p>
    <a href="{link}" style="padding:10px 20px; background-color:#4CAF50; color:white; text-decoration:none; border-radius:5px;">Подтвердить Email</a>
    """
    message = MessageSchema(subject="ActivityHub: Подтверждение Email", recipients=[email], body=html, subtype=MessageType.html)
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_2fa_code(email: EmailStr, code: str):
    html = f"""
    <h3>Вход в ActivityHub</h3>
    <p>Ваш код безопасности:</p>
    <h1 style="letter-spacing: 5px;">{code}</h1>
    """
    message = MessageSchema(subject="ActivityHub: Код для входа", recipients=[email], body=html, subtype=MessageType.html)
    fm = FastMail(conf)
    await fm.send_message(message)
