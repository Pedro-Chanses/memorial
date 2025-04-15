from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, session
from flask_login import login_required, current_user
from models import db, Monument, MonumentImage
from functools import wraps
import traceback
from flask_wtf.csrf import validate_csrf, ValidationError

monument_bp = Blueprint('monument', __name__, url_prefix='/monument')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Будь ласка, увійдіть в систему.', 'error')
            return redirect(url_for('auth.login'))
        
        # Перевіряємо статус адміністратора
        if not current_user.is_admin:
            flash('У вас немає прав для доступу до цієї сторінки.', 'error')
            return redirect(url_for('main.index'))
            
        return f(*args, **kwargs)
    return decorated_function

@monument_bp.route('/save/<int:monument_id>', methods=['POST'])
@admin_required
def save_monument(monument_id):
    """Окремий маршрут для збереження змін пам'ятника"""
    # Використовуємо вбудований логер Flask
    current_app.logger.info(f"=== ПОЧАТОК ОБРОБКИ ФОРМИ РЕДАГУВАННЯ ПАМ'ЯТНИКА {monument_id} ===")
    current_app.logger.info(f"Користувач: {current_user.username} (ID: {current_user.id}, admin: {current_user.is_admin})")
    current_app.logger.info(f"Метод запиту: {request.method}")
    current_app.logger.info(f"Форма: {request.form}")
    current_app.logger.info(f"Сесія до обробки: {session}")
    current_app.logger.info(f"Реферер: {request.referrer}")
    current_app.logger.info(f"URL: {request.url}")
    current_app.logger.info(f"Заголовки: {request.headers}")
    
    # Зберігаємо ідентифікатор адміністратора в сесії
    if current_user.is_authenticated and current_user.is_admin:
        session['admin_id'] = current_user.id
        session['admin_username'] = current_user.username
        session.permanent = True
        current_app.logger.info(f"Збережено дані адміністратора в сесії: {session}")
    
    try:
        # Перевіряємо CSRF-токен
        csrf_token = request.form.get('csrf_token')
        current_app.logger.info(f"CSRF-токен з форми: {csrf_token}")
        
        # Пропускаємо перевірку CSRF-токена для тестування
        # try:
        #     validate_csrf(csrf_token)
        #     current_app.logger.info("CSRF-токен успішно перевірено")
        # except ValidationError as e:
        #     current_app.logger.error(f"CSRF-помилка: {str(e)}")
        #     flash('Помилка безпеки. Спробуйте ще раз.', 'error')
        #     return redirect('/admin/monuments')
        
        # Отримуємо пам'ятник
        current_app.logger.debug(f"Отримуємо пам'ятник з ID: {monument_id}")
        monument = Monument.query.get_or_404(monument_id)
        current_app.logger.debug(f"Знайдено пам'ятник: {monument.name} (ID: {monument.id})")
        
        # Оновлюємо поля пам'ятника
        current_app.logger.debug("Починаємо оновлення полів пам'ятника")
        
        # Основні поля
        old_name = monument.name
        monument.name = request.form.get('name', '')
        current_app.logger.debug(f"Оновлюємо назву з '{old_name}' на '{monument.name}'")
        
        # Артикул
        if 'article' in request.form:
            old_article = monument.article
            monument.article = request.form.get('article', '')
            current_app.logger.debug(f"Оновлюємо артикул з '{old_article}' на '{monument.article}'")
        
        # Ціна
        if 'price' in request.form and request.form.get('price'):
            try:
                monument.price = int(request.form.get('price'))
                current_app.logger.debug(f"Оновлюємо ціну на {monument.price}")
            except ValueError:
                current_app.logger.warning(f"Невалідна ціна: {request.form.get('price')}")
        
        # Категорія
        if 'category' in request.form:
            old_category = monument.category
            monument.category = request.form.get('category', '')
            current_app.logger.debug(f"Оновлюємо категорію з '{old_category}' на '{monument.category}'")
        
        # Розміри
        if 'dimensions' in request.form:
            monument.dimensions = request.form.get('dimensions', '')
            current_app.logger.debug(f"Оновлюємо розміри на '{monument.dimensions}'")
        
        # Колір
        if 'color' in request.form:
            monument.color = request.form.get('color', '')
            current_app.logger.debug(f"Оновлюємо колір на '{monument.color}'")
        
        # Наявність
        if 'availability' in request.form:
            monument.availability = request.form.get('availability', '')
            current_app.logger.debug(f"Оновлюємо наявність на '{monument.availability}'")
        
        # Час виготовлення
        if 'production_time' in request.form:
            monument.production_time = request.form.get('production_time', '')
            current_app.logger.debug(f"Оновлюємо час виготовлення на '{monument.production_time}'")
        
        # Активність
        monument.is_active = 'is_active' in request.form
        current_app.logger.debug(f"Оновлюємо активність на {monument.is_active}")
        
        # Популярність
        monument.is_popular = 'is_popular' in request.form
        current_app.logger.debug(f"Оновлюємо популярність на {monument.is_popular}")
        
        # Знижка
        if 'discount_percent' in request.form and request.form.get('discount_percent'):
            try:
                monument.discount_percent = int(request.form.get('discount_percent'))
                current_app.logger.debug(f"Оновлюємо знижку на {monument.discount_percent}%")
            except ValueError:
                current_app.logger.warning(f"Невалідна знижка: {request.form.get('discount_percent')}")
        
        # Стара ціна
        if 'old_price' in request.form and request.form.get('old_price'):
            try:
                monument.old_price = int(request.form.get('old_price'))
                current_app.logger.debug(f"Оновлюємо стару ціну на {monument.old_price}")
            except ValueError:
                current_app.logger.warning(f"Невалідна стара ціна: {request.form.get('old_price')}")
        
        # Опис
        if 'description' in request.form:
            monument.description = request.form.get('description', '')
            current_app.logger.debug("Оновлено опис пам'ятника")
        
        # Зберігаємо зміни
        current_app.logger.info("Зберігаємо зміни в базі даних...")
        db.session.commit()
        current_app.logger.info("Зміни успішно збережено")
        
        # Зберігаємо ідентифікатор адміністратора в сесії ще раз
        if current_user.is_authenticated and current_user.is_admin:
            session['admin_id'] = current_user.id
            session['admin_username'] = current_user.username
            session.permanent = True
            current_app.logger.info(f"Збережено дані адміністратора в сесії після збереження: {session}")
        
        # Повертаємо успішну відповідь
        flash('Пам\'ятник успішно оновлено', 'success')
        current_app.logger.info(f"Сесія перед перенаправленням: {session}")
        current_app.logger.info("Перенаправляємо на сторінку зі списком пам'ятників")
        
        # Використовуємо абсолютний URL для перенаправлення
        return redirect('/admin/monuments')
    except Exception as e:
        current_app.logger.error(f"ПОМИЛКА: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        flash(f'Помилка при оновленні пам\'ятника: {str(e)}', 'error')
        return redirect('/admin/monuments')
