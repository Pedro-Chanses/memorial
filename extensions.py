from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
# Видалено Flask-Caching
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babel import Babel
from flask import request, session

# Ініціалізація розширень
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()

# Заглушка для cache, щоб не змінювати інші файли
class DummyCache:
    def init_app(self, app):
        pass
    def cached(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator
    def get(self, *args, **kwargs):
        return None
    def set(self, *args, **kwargs):
        pass

cache = DummyCache()
limiter = Limiter(key_func=get_remote_address)
babel = Babel()

def get_locale():
    # Спочатку перевіряємо, чи є мова в сесії
    if 'language' in session:
        return session['language']
    
    # Потім перевіряємо заголовок Accept-Language
    return request.accept_languages.best_match(['uk', 'en'])

def get_timezone():
    return 'Europe/Kiev'
