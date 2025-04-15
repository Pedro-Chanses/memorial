from flask import Flask
from flask_migrate import Migrate
from extensions import db, login_manager, migrate, mail, cache, limiter, babel, get_locale, get_timezone
from models import User, News, OwnWork
from blueprints.main import main_bp
from blueprints.auth import auth_bp
from blueprints.admin import admin_bp
from blueprints.events_stub import events_bp  # Використовуємо заглушку замість оригінального файлу
from blueprints.gallery import gallery_bp
from blueprints.news import news_bp
from blueprints.excel_routes import excel_bp
from blueprints.monument_routes import monument_bp
from blueprints.simple_edit import simple_edit_bp  # Новий blueprint для простого редагування
from blueprints.own_works import own_works_bp  # Blueprint для власних робіт
import os
import logging
from logging.handlers import RotatingFileHandler
from flask_wtf.csrf import CSRFProtect
from config import config, get_environment
from flask import render_template, session, request, current_app
from flask_login import current_user
from datetime import timedelta
import cloudinary

# Визначаємо, чи запущено на Render
is_render = os.environ.get('RENDER') == 'true'

def create_app(config_name=None):
    # Якщо конфігурація не вказана, визначаємо автоматично
    if config_name is None:
        config_name = get_environment()
        
    app = Flask(__name__)
    
    # Завантаження конфігурації
    app.config.from_object(config[config_name])
    
    # Створюємо папки для завантажень
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'news'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'gallery'), exist_ok=True)
    
    # Налаштування логування
    configure_logging(app)
    
    # Налаштування Cloudinary
    cloudinary.config(
        cloud_name=app.config.get('CLOUDINARY_CLOUD_NAME'),
        api_key=app.config.get('CLOUDINARY_API_KEY'),
        api_secret=app.config.get('CLOUDINARY_API_SECRET')
    )
    
    # Ініціалізація розширень
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    babel.init_app(app, locale_selector=get_locale, timezone_selector=get_timezone)
    
    # Налаштування CSRF-захисту
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # Налаштування сесій
    app.config['SESSION_COOKIE_SECURE'] = False  # В продакшені змінити на True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_COOKIE_NAME'] = 'memorial_session'
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=31)
    app.config['REMEMBER_COOKIE_SECURE'] = False
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['SESSION_TYPE'] = 'filesystem'  # Використовуємо файлову систему для зберігання сесій
    app.config['SESSION_USE_SIGNER'] = True  # Підписуємо сесії для більшої безпеки
    
    # Налаштування login_manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Будь ласка, увійдіть для доступу до цієї сторінки.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'basic'  # Змінюємо на 'basic' для менш суворої перевірки сесії
    login_manager.refresh_view = 'auth.login'  # Сторінка для оновлення сесії
    login_manager.needs_refresh_message = 'Будь ласка, пройдіть авторизацію ще раз для продовження.'
    login_manager.needs_refresh_message_category = 'info'
    
    # Додаємо логування для відстеження проблем з сесією
    @app.before_request
    def log_request_info():
        app.logger.debug('Headers: %s', request.headers)
        app.logger.debug('Body: %s', request.get_data())
        app.logger.debug('Session: %s', session)
        if current_user.is_authenticated:
            app.logger.debug('User: %s (id=%s, is_admin=%s)', 
                          current_user.username, 
                          current_user.id, 
                          current_user.is_admin)
        else:
            app.logger.debug('User not authenticated')
    
    # Завантаження користувача
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Створення необхідних директорій
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Реєстрація blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(events_bp, url_prefix='/events')
    app.register_blueprint(gallery_bp, url_prefix='/gallery')
    app.register_blueprint(news_bp, url_prefix='/news')
    app.register_blueprint(excel_bp)
    app.register_blueprint(monument_bp)
    app.register_blueprint(simple_edit_bp, url_prefix='/simple')
    app.register_blueprint(own_works_bp, url_prefix='/own-works')
    
    # Фільтр для адаптації URL зображень
    @app.template_filter('adapt_url')
    def adapt_url(url):
        if not url:
            return url
            
        # Визначаємо, чи ми в продакшн-середовищі
        is_production = os.environ.get('RENDER') == 'true' or os.environ.get('FLASK_ENV') == 'production'
        
        # В продакшні використовуємо HTTPS
        if is_production and url.startswith('http:'):
            return url.replace('http:', 'https:')
        # В локальному середовищі використовуємо HTTP
        elif not is_production and url.startswith('https:'):
            return url.replace('https:', 'http:')
        return url
    
    # Контекстні процесори
    @app.context_processor
    def utility_processor():
        def get_branches():
            return []  # Повертаємо порожній список, оскільки модель Branch видалена
            
        def get_upcoming_events():
            return []  # Повертаємо порожній список, оскільки модель Event видалена
            
        def get_latest_news():
            return News.query.filter_by(is_published=True).order_by(News.created_at.desc()).limit(5).all()
            
        return dict(
            get_branches=get_branches,
            get_upcoming_events=get_upcoming_events,
            get_latest_news=get_latest_news
        )
    
    # Обробка помилок
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Створення папок для завантажень
    upload_folders = [
        os.path.join(app.static_folder, 'uploads'),
        os.path.join(app.static_folder, 'uploads', 'events'),
        os.path.join(app.static_folder, 'uploads', 'gallery'),
        os.path.join(app.static_folder, 'uploads', 'news')
    ]
    
    for folder in upload_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    # Команди Flask CLI
    @app.cli.command("init-db")
    def init_db():
        """Ініціалізація бази даних."""
        db.create_all()
        print('База даних ініціалізована.')
    

    
    return app

def configure_logging(app):
    """
    Налаштування логування для додатку
    """
    if not app.debug and not app.testing:
        try:
            # Створення обробника файлів логів
            if app.config.get('LOG_FILE'):
                log_file = app.config['LOG_FILE']
                # Створюємо директорію для логів, якщо вона не існує
                log_dir = os.path.dirname(log_file)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
            else:
                log_dir = os.path.join(app.config['BASE_DIR'], 'logs')
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                log_file = os.path.join(log_dir, 'memorial.log')
            
            file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            # Встановлення рівня логування
            app.logger.setLevel(logging.INFO)
            app.logger.info('Memorial startup')
        except Exception as e:
            # Якщо виникла помилка з логами, використовуємо консольний логер
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            console_handler.setLevel(logging.INFO)
            app.logger.addHandler(console_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.error(f'Error setting up file logging: {str(e)}')
            app.logger.info('Memorial startup (console logging)')

# Створення екземпляру додатку
app = create_app()

# Друкуємо інформацію про підключення до бази даних
print(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')}")

# Автоматична ініціалізація бази даних та створення папок
with app.app_context():
    # Створюємо папки для зберігання зображень
    upload_folders = [
        os.path.join('static', 'uploads'),
        os.path.join('static', 'uploads', 'news'),
        os.path.join('static', 'uploads', 'gallery'),
        os.path.join('static', 'uploads', 'avatars')
    ]
    
    for folder in upload_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Створено папку: {folder}")
    
    # Ініціалізуємо міграції
    migrate.init_app(app, db)
    print("Flask-Migrate успішно ініціалізовано!")

if __name__ == '__main__':
    app.run(debug=True)
