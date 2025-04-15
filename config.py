import os
from dotenv import load_dotenv
from datetime import timedelta
import platform

# Завантажуємо змінні середовища з .env файлу, якщо він існує
load_dotenv()

class Config:
    # Базові налаштування
    SECRET_KEY = os.environ.get('SECRET_KEY') or ';dkcfpcpl[sl[lc[[]]]]'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PostgreSQL конфігурація
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # Налаштування пулу з'єднань
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_recycle': 1800,
    }
    
    # Cloudinary налаштування
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
    USE_CLOUDINARY = True  # Використовувати Cloudinary замість локального сховища
    
    # Налаштування пошти
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@okinawa-karate.com')
    
    # Google OAuth налаштування
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    OAUTHLIB_INSECURE_TRANSPORT = True  # Тільки для розробки!
    
    # Facebook налаштування
    FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET')
    
    # Адміністратори системи
    ADMIN_EMAILS = os.environ.get('ADMIN_EMAILS', '').split(',')
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'csrf-key-dev'
    
    # Налаштування кешування
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 хвилин
    
    # Налаштування Flask-Limiter
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    
    # Налаштування завантаження файлів
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB максимальний розмір файлу
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Налаштування сесій
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    SESSION_COOKIE_SECURE = False  # Змінити на True при використанні HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_TYPE = 'filesystem'  # Використовуємо файлову систему для зберігання сесій
    SESSION_PERMANENT = True  # Робимо сесію постійною
    SESSION_USE_SIGNER = True  # Підписуємо сесійні куки
    
    # Налаштування безпеки
    CSRF_ENABLED = True
    CSRF_TIME_LIMIT = timedelta(minutes=30)
    
    # Налаштування локалізації
    BABEL_DEFAULT_LOCALE = 'uk'
    BABEL_DEFAULT_TIMEZONE = 'Europe/Kiev'
    LANGUAGES = ['uk', 'en']
    
    # Налаштування пагінації
    POSTS_PER_PAGE = 12
    NEWS_PER_PAGE = 10
    GALLERY_ITEMS_PER_PAGE = 24
    
    # reCAPTCHA
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY')
    
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    # В продакшені можемо використовувати Redis для ліміту запитів, якщо він доступний
    if 'PYTHONANYWHERE_SITE' in os.environ:
        CACHE_TYPE = 'simple'
        RATELIMIT_STORAGE_URL = "memory://"
    else:
        RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        CACHE_TYPE = 'redis'
        CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        
    # Налаштування для PythonAnywhere
    if 'PYTHONANYWHERE_SITE' in os.environ:
        # Шлях до логів на PythonAnywhere
        LOG_FILE = os.path.join(
            os.path.expanduser('~'),
            'logs',
            'okinava.log'
        )

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class PythonAnywhereConfig(ProductionConfig):
    """Спеціальна конфігурація для PythonAnywhere"""
    # Тут можна додати специфічні налаштування для PythonAnywhere
    pass

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'pythonanywhere': PythonAnywhereConfig,
    'default': DevelopmentConfig
}

class RenderConfig(ProductionConfig):
    """Спеціальна конфігурація для Render"""
    # SQLite конфігурація для Render
    if os.environ.get('USE_SQLITE') == 'true':
        SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    
    # Шлях до логів на Render (у директорії проекту)
    LOG_FILE = 'logs/memorial.log'
    
    # Налаштування для Render
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'

# Додаємо конфігурацію для Render
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'pythonanywhere': PythonAnywhereConfig,
    'render': RenderConfig,
    'default': DevelopmentConfig
}

# Автоматично визначаємо середовище
def get_environment():
    if os.environ.get('RENDER') == 'true':
        return 'render'
    elif 'PYTHONANYWHERE_SITE' in os.environ:
        return 'pythonanywhere'
    elif os.environ.get('FLASK_ENV') == 'production':
        return 'production'
    elif os.environ.get('FLASK_ENV') == 'testing':
        return 'testing'
    else:
        return 'development'
