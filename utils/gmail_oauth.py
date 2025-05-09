import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import current_app, url_for, session, request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
from google.oauth2 import id_token
import google.auth.transport.requests

def create_oauth_flow(for_gmail=False):
    """Створює об'єкт Flow для OAuth 2.0
    
    Ця функція динамічно визначає правильний redirect_uri залежно від середовища виконання:
    - Локальне середовище: http://localhost:5000/auth/oauth2callback
    - Render: визначається за RENDER_EXTERNAL_URL або за request.host
    - Heroku та інші продакшн: https://{request.host}/auth/oauth2callback
    
    ВАЖЛИВО: Всі ці redirect_uri мають бути додані у Google Cloud Console в налаштуваннях OAuth 2.0 Client ID.
    Після зміни налаштувань у Google Cloud Console може знадобитися до кількох годин для застосування змін.
    
    Args:
        for_gmail (bool): Якщо True, використовується для Gmail API, інакше для звичайної авторизації
    
    Returns:
        Flow: Об'єкт Flow для OAuth 2.0 авторизації
    """
    try:
        # Конфігурація клієнта OAuth
        client_config = {
            "web": {
                "client_id": current_app.config['GOOGLE_CLIENT_ID'],
                "client_secret": current_app.config['GOOGLE_CLIENT_SECRET'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [
                    # Локальне середовище
                    "http://127.0.0.1:5000/auth/oauth2callback",
                    "http://localhost:5000/auth/oauth2callback",
                    # Heroku
                    "https://memorial-app-835445eb1cf7.herokuapp.com/auth/oauth2callback",
                    "https://memorial-app-835445eb1cf7.herokuapp.com/auth/authorize",
                    # Render
                    "https://memorial-05p8.onrender.com/auth/oauth2callback",
                    "https://memorial-05p8.onrender.com/auth/authorize",
                    "https://stoune.pp.ua/auth/oauth2callback",
                    "https://stoune.pp.ua/auth/authorize"
                ]
            }
        }
        
        # Визначаємо поточний URI для перенаправлення залежно від середовища
        if os.environ.get('RENDER') == 'true':
            # Середовище Render
            render_url = os.environ.get('RENDER_EXTERNAL_URL', '')
            if render_url:
                redirect_uri = f"{render_url}/auth/oauth2callback"
            else:
                redirect_uri = f"https://{request.host}/auth/oauth2callback"
                current_app.logger.info(f"RENDER середовище без RENDER_EXTERNAL_URL, використовуємо request.host: {request.host}")
        elif request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
            # Локальне середовище
            if request.host.startswith('localhost'):
                redirect_uri = "http://localhost:5000/auth/oauth2callback"
            else:
                redirect_uri = "http://127.0.0.1:5000/auth/oauth2callback"
        else:
            # Heroku та інші продакшн-сервери
            redirect_uri = f"https://{request.host}/auth/oauth2callback"
            current_app.logger.info(f"Використовуємо продакшн redirect_uri для хоста: {request.host}")
        
        # Різні області доступу для Gmail і звичайної авторизації
        if for_gmail:
            scopes = ['https://www.googleapis.com/auth/gmail.send']
        else:
            scopes = [
                'openid',
                'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile'
            ]
        
        # Створюємо Flow з конфігурації клієнта
        flow = Flow.from_client_config(
            client_config,
            scopes=scopes,
            redirect_uri=redirect_uri
        )
        
        # Діагностика redirect_uri
        current_app.logger.info(f"OAuth DEBUG: Using redirect_uri={redirect_uri}, host={request.host}")
        print(f"DEBUG OAUTH: Using redirect_uri={redirect_uri}, host={request.host}")
        
        return flow
        
    except Exception as e:
        # Логуємо помилку і прокидаємо її далі
        current_app.logger.error(f"OAuth flow creation error: {str(e)}")
        raise

def get_google_user_info(credentials):
    """Отримує інформацію про користувача Google"""
    try:
        request_session = google.auth.transport.requests.Request()
        
        # Додаємо параметр clock_skew_in_seconds для компенсації різниці в часі
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, 
            request_session,
            current_app.config['GOOGLE_CLIENT_ID'],
            clock_skew_in_seconds=10  # Дозволяємо різницю в часі до 10 секунд
        )

        return {
            'email': id_info.get('email'),
            'name': id_info.get('name'),
            'picture': id_info.get('picture')
        }
    except Exception as e:
        current_app.logger.error(f"Error getting user info: {str(e)}")
        return None

def get_gmail_service():
    """Створює сервіс Gmail API з збережених облікових даних"""
    if 'credentials' not in session:
        return None
        
    credentials = Credentials(**session['credentials'])
    
    return build('gmail', 'v1', credentials=credentials)

def create_message(sender, to, subject, message_text):
    """Створює повідомлення для Gmail API"""
    from email.mime.text import MIMEText
    import base64
    
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    raw = base64.urlsafe_b64encode(message.as_bytes())
    return {'raw': raw.decode()}
