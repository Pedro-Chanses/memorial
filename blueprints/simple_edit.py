from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
from functools import wraps
from models import Monument, db, MonumentImage
from werkzeug.utils import secure_filename
import os
import uuid
import cloudinary
import cloudinary.uploader
from datetime import datetime

simple_edit_bp = Blueprint('simple_edit', __name__)

# Декоратор для перевірки прав адміністратора
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('У вас немає прав для доступу до цієї сторінки', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@simple_edit_bp.route('/edit_monument/<int:monument_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_monument(monument_id):
    """Спрощена функція редагування пам'ятника"""
    # Зберігаємо ідентифікатор адміністратора в сесії
    if current_user.is_authenticated and current_user.is_admin:
        session['admin_id'] = current_user.id
        session['admin_username'] = current_user.username
        session.permanent = True
    
    # Отримуємо пам'ятник для редагування
    monument = Monument.query.get_or_404(monument_id)
    
    # Обробка POST-запиту (збереження змін)
    if request.method == 'POST':
        try:
            # Отримуємо новий артикул
            new_article = request.form.get('article', '').upper()
            
            # Перевіряємо, чи існує вже пам'ятник з таким артикулом
            existing_monument = Monument.query.filter(Monument.article == new_article, 
                                                    Monument.id != monument_id).first()
            if existing_monument:
                flash(f'Пам\'ятник з артикулом {new_article} вже існує. Виберіть інший артикул.', 'error')
                return render_template('admin/simple_edit.html', 
                                     title='Редагування пам\'ятника',
                                     monument=monument)
            
            # Оновлюємо основні поля пам'ятника
            monument.name = request.form.get('name', '')
            monument.article = new_article
            
            price = request.form.get('price')
            monument.price = int(price) if price and price.isdigit() else None
            
            monument.description = request.form.get('description')
            monument.category = request.form.get('category')
            monument.dimensions = request.form.get('dimensions')
            monument.material = request.form.get('material')
            monument.color = request.form.get('color')
            monument.is_active = 'is_active' in request.form
            
            # Зберігаємо зміни в базі даних
            db.session.commit()
            
            # Повторно зберігаємо ідентифікатор адміністратора в сесії
            if current_user.is_authenticated and current_user.is_admin:
                session['admin_id'] = current_user.id
                session['admin_username'] = current_user.username
                session.permanent = True
            
            flash('Пам\'ятник успішно оновлено', 'success')
            return redirect(url_for('admin.monuments'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Помилка при оновленні пам'ятника: {str(e)}")
            flash(f'Помилка при оновленні пам\'ятника: {str(e)}', 'error')
    
    # Відображаємо форму редагування
    return render_template('admin/simple_edit.html', 
                         title='Редагування пам\'ятника',
                         monument=monument)

@simple_edit_bp.route('/delete_monument/<int:monument_id>', methods=['POST'])
@login_required
@admin_required
def delete_monument(monument_id):
    """Видалення пам'ятника"""
    monument = Monument.query.get_or_404(monument_id)
    
    try:
        # Видаляємо пам'ятник з бази даних
        db.session.delete(monument)
        db.session.commit()
        flash('Пам\'ятник успішно видалено', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Помилка при видаленні пам'ятника: {str(e)}")
        flash(f'Помилка при видаленні пам\'ятника: {str(e)}', 'error')
    
    return redirect(url_for('admin.monuments'))

@simple_edit_bp.route('/upload_images/<int:monument_id>', methods=['POST'])
@login_required
@admin_required
def upload_images(monument_id):
    """Завантаження зображень для пам'ятника"""
    monument = Monument.query.get_or_404(monument_id)
    
    if 'images' not in request.files:
        flash('Не вибрано жодного файлу', 'error')
        return redirect(url_for('simple_edit.edit_monument', monument_id=monument_id))
    
    files = request.files.getlist('images')
    if not files or files[0].filename == '':
        flash('Не вибрано жодного файлу', 'error')
        return redirect(url_for('simple_edit.edit_monument', monument_id=monument_id))
    
    # Перевіряємо, чи налаштований Cloudinary
    if not all([current_app.config.get('CLOUDINARY_CLOUD_NAME'),
                current_app.config.get('CLOUDINARY_API_KEY'),
                current_app.config.get('CLOUDINARY_API_SECRET')]):
        flash('Помилка: Cloudinary не налаштований', 'error')
        return redirect(url_for('simple_edit.edit_monument', monument_id=monument_id))
        
    # Налаштовуємо Cloudinary для поточного запиту
    cloudinary.config(
        cloud_name=current_app.config.get('CLOUDINARY_CLOUD_NAME'),
        api_key=current_app.config.get('CLOUDINARY_API_KEY'),
        api_secret=current_app.config.get('CLOUDINARY_API_SECRET')
    )
    
    success_count = 0
    error_count = 0
    
    for file in files:
        if file and file.filename:
            try:
                # Генеруємо унікальне ім'я файлу
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                
                # Завантажуємо файл в Cloudinary
                upload_result = cloudinary.uploader.upload(
                    file,
                    folder="monuments",
                    public_id=unique_filename.split('.')[0],  # Без розширення
                    overwrite=True,
                    resource_type="image"
                )
                
                # Створюємо запис про зображення в базі даних
                image_url = upload_result['secure_url']
                
                # Перевіряємо, чи є вже зображення для цього пам'ятника
                is_main = MonumentImage.query.filter_by(monument_id=monument.id).count() == 0
                
                new_image = MonumentImage(
                    monument_id=monument.id,
                    filename=image_url,
                    is_main=is_main
                )
                db.session.add(new_image)
                
                # Якщо це перше зображення або немає головного, встановлюємо його як головне
                if is_main:
                    monument.main_image = image_url
                
                success_count += 1
            except Exception as e:
                current_app.logger.error(f"Помилка завантаження зображення: {str(e)}")
                error_count += 1
    
    try:
        db.session.commit()
        if success_count > 0:
            flash(f'Успішно завантажено {success_count} зображень', 'success')
        if error_count > 0:
            flash(f'Помилка при завантаженні {error_count} зображень', 'error')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Помилка збереження зображень: {str(e)}")
        flash(f'Помилка збереження зображень: {str(e)}', 'error')
    
    return redirect(url_for('simple_edit.edit_monument', monument_id=monument_id))

@simple_edit_bp.route('/delete_image/<int:image_id>/<int:monument_id>', methods=['POST'])
@login_required
@admin_required
def delete_image(image_id, monument_id):
    """Видалення зображення пам'ятника"""
    image = MonumentImage.query.get_or_404(image_id)
    monument = Monument.query.get_or_404(monument_id)
    
    # Перевіряємо, чи зображення належить цьому пам'ятнику
    if image.monument_id != monument.id:
        flash('Помилка: зображення не належить цьому пам\'ятнику', 'error')
        return redirect(url_for('simple_edit.edit_monument', monument_id=monument_id))
    
    try:
        # Якщо це головне зображення, скидаємо головне зображення пам'ятника
        if image.is_main:
            monument.main_image = None
            
            # Шукаємо інше зображення, яке можна зробити головним
            other_image = MonumentImage.query.filter(MonumentImage.monument_id == monument.id, 
                                                    MonumentImage.id != image.id).first()
            if other_image:
                other_image.is_main = True
                monument.main_image = other_image.filename
        
        # Видаляємо зображення з бази даних
        db.session.delete(image)
        db.session.commit()
        flash('Зображення успішно видалено', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Помилка при видаленні зображення: {str(e)}")
        flash(f'Помилка при видаленні зображення: {str(e)}', 'error')
    
    return redirect(url_for('simple_edit.edit_monument', monument_id=monument_id))

@simple_edit_bp.route('/set_main_image/<int:image_id>/<int:monument_id>', methods=['POST'])
@login_required
@admin_required
def set_main_image(image_id, monument_id):
    """Встановлення головного зображення пам'ятника"""
    image = MonumentImage.query.get_or_404(image_id)
    monument = Monument.query.get_or_404(monument_id)
    
    # Перевіряємо, чи зображення належить цьому пам'ятнику
    if image.monument_id != monument.id:
        flash('Помилка: зображення не належить цьому пам\'ятнику', 'error')
        return redirect(url_for('simple_edit.edit_monument', monument_id=monument_id))
    
    try:
        # Скидаємо попереднє головне зображення
        previous_main = MonumentImage.query.filter_by(monument_id=monument.id, is_main=True).first()
        if previous_main:
            previous_main.is_main = False
        
        # Встановлюємо нове головне зображення
        image.is_main = True
        monument.main_image = image.filename
        monument.updated_at = datetime.now()
        
        db.session.commit()
        flash('Головне зображення успішно оновлено', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Помилка при встановленні головного зображення: {str(e)}")
        flash(f'Помилка при встановленні головного зображення: {str(e)}', 'error')
    
    return redirect(url_for('simple_edit.edit_monument', monument_id=monument_id))
