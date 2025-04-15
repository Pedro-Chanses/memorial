from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from utils.decorators import admin_required
from models import db, OwnWork, Image
from forms.own_work import OwnWorkForm
from sqlalchemy import desc
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid
from PIL import Image as PILImage
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
import time

own_works_bp = Blueprint('own_works', __name__)

def save_own_work_image(file):
    """Зберігає зображення для власної роботи"""
    if not file:
        current_app.logger.warning("No file provided for upload")
        return None
    
    try:
        current_app.logger.info(f"Starting upload for file: {file.filename}")
        
        # Налаштування Cloudinary
        cloudinary.config(
            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=current_app.config['CLOUDINARY_API_KEY'],
            api_secret=current_app.config['CLOUDINARY_API_SECRET']
        )
        
        current_app.logger.info(f"Cloudinary settings: CLOUD_NAME={current_app.config['CLOUDINARY_CLOUD_NAME']}")
        
        # Генеруємо унікальне ім'я файлу
        filename = secure_filename(file.filename)
        public_id = f"own_work_{int(time.time())}_{filename}"
        
        current_app.logger.info(f"Generated public_id: {public_id}")
        
        # Завантажуємо файл до Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            folder="okinava",
            overwrite=True,
            resource_type="image"
        )
        
        current_app.logger.info(f"Upload successful. Result: {upload_result}")
        
        # Створюємо URL для мініатюри
        thumbnail_url = cloudinary.utils.cloudinary_url(
            upload_result['public_id'],
            width=400,
            height=300,
            crop="fill",
            quality="auto",
            fetch_format="auto"
        )[0]
        
        current_app.logger.info(f"Generated thumbnail URL: {thumbnail_url}")
        
        # Створюємо запис в базі даних
        image = Image(
            filename=upload_result['secure_url'],
            thumbnail=thumbnail_url,
            cloudinary_public_id=upload_result['public_id'],
            is_own_work=True
        )
        
        current_app.logger.info(f"Created image record: filename={image.filename}, thumbnail={image.thumbnail}")
        
        return image
        
    except Exception as e:
        current_app.logger.error(f"Error uploading image: {str(e)}")
        current_app.logger.exception("Full error details:")
        return None

@own_works_bp.route('/')
def index():
    """Головна сторінка власних робіт"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    
    # Базовий запит
    query = OwnWork.query.filter_by(is_published=True)
    
    # Фільтрація за категорією
    if category:
        query = query.filter_by(category=category)
    
    # Отримуємо роботи з пагінацією
    works = query.order_by(desc(OwnWork.created_at)).paginate(
        page=page,
        per_page=current_app.config.get('WORKS_PER_PAGE', 9),
        error_out=False
    )
    
    return render_template('own_works/index.html',
                         title='Власні роботи',
                         works=works,
                         current_category=category)

@own_works_bp.route('/<int:work_id>')
def view(work_id):
    """Перегляд окремої роботи"""
    work_item = OwnWork.query.get_or_404(work_id)
    
    # Якщо робота не опублікована, її можуть бачити тільки адміністратори
    if not work_item.is_published and (not current_user.is_authenticated or not current_user.is_admin):
        abort(404)
    
    # Збільшуємо лічильник переглядів
    work_item.views += 1
    db.session.commit()
    
    return render_template('own_works/view.html', title=work_item.title, work=work_item)

@own_works_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """Створення нової роботи"""
    form = OwnWorkForm()
    
    if form.validate_on_submit():
        work = OwnWork(
            title=form.title.data,
            content=form.content.data,
            category=form.category.data,
            summary=form.summary.data,
            is_published=bool(int(form.is_published.data)),
            author_id=current_user.id
        )
        
        db.session.add(work)
        db.session.commit()
        
        # Зберігаємо зображення
        files = request.files.getlist('gallery_images')
        for file in files:
            if file:
                image = save_own_work_image(file)
                if image:
                    work.images.append(image)
                    db.session.commit()
        
        flash('Роботу успішно створено!', 'success')
        return redirect(url_for('own_works.view', work_id=work.id))
    
    return render_template('own_works/create.html',
                         title='Створення нової роботи',
                         form=form)

@own_works_bp.route('/edit/<int:work_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(work_id):
    """Редагування роботи"""
    
    work = OwnWork.query.get_or_404(work_id)
    form = OwnWorkForm(obj=work)
    
    if form.validate_on_submit():
        work.title = form.title.data
        work.content = form.content.data
        work.category = form.category.data
        work.summary = form.summary.data
        work.is_published = bool(int(form.is_published.data))
        work.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Роботу успішно оновлено!', 'success')
        return redirect(url_for('own_works.edit', work_id=work.id))

    return render_template('own_works/edit.html',
                         title='Редагування роботи',
                         form=form,
                         work=work)

@own_works_bp.route('/upload_images/<int:work_id>', methods=['POST'])
@login_required
@admin_required
def upload_images(work_id):
    """Завантаження зображень для роботи"""
    work = OwnWork.query.get_or_404(work_id)
    
    # Перевіряємо, чи є файли у запиті
    if 'images' not in request.files:
        flash('Не вибрано жодного файлу', 'error')
        return redirect(url_for('own_works.edit', work_id=work.id))
    
    files = request.files.getlist('images')
    
    # Перевіряємо, чи не порожній список файлів
    if not files or files[0].filename == '':
        flash('Не вибрано жодного файлу', 'error')
        return redirect(url_for('own_works.edit', work_id=work.id))
    
    try:
        # Налаштування Cloudinary
        cloudinary.config(
            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=current_app.config['CLOUDINARY_API_KEY'],
            api_secret=current_app.config['CLOUDINARY_API_SECRET']
        )
        
        # Обробляємо кожен файл
        for file in files:
            if file and allowed_file(file.filename):
                # Генеруємо унікальне ім'я файлу
                filename = secure_filename(file.filename)
                public_id = f"own_work_{int(time.time())}_{filename}"
                
                # Завантажуємо файл до Cloudinary
                upload_result = cloudinary.uploader.upload(
                    file,
                    public_id=public_id,
                    folder="okinava",
                    overwrite=True,
                    resource_type="image"
                )
                
                # Створюємо URL для мініатюри
                thumbnail_url = cloudinary.utils.cloudinary_url(
                    upload_result['public_id'],
                    width=400,
                    height=300,
                    crop="fill",
                    quality="auto",
                    fetch_format="auto"
                )[0]
                
                # Перевіряємо, чи є вже зображення для цієї роботи
                existing_images = Image.query.filter_by(own_work_id=work.id, is_own_work=True).count()
                
                # Створюємо запис в базі даних
                image = Image(
                    filename=upload_result['secure_url'],
                    thumbnail=thumbnail_url,
                    cloudinary_public_id=upload_result['public_id'],
                    is_own_work=True,
                    own_work_id=work.id,
                    is_main=(existing_images == 0)  # Якщо це перше зображення, встановлюємо його як головне
                )
                
                if existing_images == 0:
                    # Якщо це перше зображення, встановлюємо його як головне в роботі
                    work.main_image = upload_result['secure_url']
                    current_app.logger.info(f"Встановлено як головне зображення: {filename}")
                
                db.session.add(image)
                current_app.logger.info(f"Зображення успішно завантажено: {filename}")
            else:
                flash(f'Непідтримуваний формат файлу: {file.filename}', 'error')
        
        db.session.commit()
        flash('Зображення успішно завантажені', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Помилка збереження зображень: {str(e)}")
        flash(f'Помилка збереження зображень: {str(e)}', 'error')
    
    # Перенаправляємо на секцію з галереєю зображень
    return redirect(url_for('own_works.edit', work_id=work.id) + '#gallery')

@own_works_bp.route('/image/set_main/<int:image_id>/<int:work_id>', methods=['POST'])
@login_required
@admin_required
def set_main_image(image_id, work_id):
    """Встановлення головного зображення роботи"""
    current_app.logger.info(f"Спроба встановлення головного зображення: image_id={image_id}, work_id={work_id}")
    
    image = Image.query.get_or_404(image_id)
    work = OwnWork.query.get_or_404(work_id)
    
    # Перевіряємо, чи зображення належить цій роботі
    if image.own_work_id != work.id or not image.is_own_work:
        current_app.logger.error(f"Помилка: зображення не належить цій роботі. image.own_work_id={image.own_work_id}, work.id={work.id}, image.is_own_work={image.is_own_work}")
        flash('Помилка: зображення не належить цій роботі', 'error')
        return redirect(url_for('own_works.edit', work_id=work.id))
    
    try:
        # Скидаємо попереднє головне зображення
        for img in work.images:
            # Безпечна перевірка атрибута is_main
            if hasattr(img, 'is_main'):
                img.is_main = False
                current_app.logger.info(f"Скинуто головне зображення: {img.id}")
        
        # Встановлюємо нове головне зображення
        image.is_main = True
        work.main_image = image.filename
        work.updated_at = datetime.utcnow()
        current_app.logger.info(f"Встановлено нове головне зображення: {image.id}")
        
        db.session.commit()
        flash('Головне зображення успішно оновлено', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Помилка при встановленні головного зображення: {str(e)}")
        flash(f'Помилка при встановленні головного зображення: {str(e)}', 'error')
    
    return redirect(url_for('own_works.edit', work_id=work.id))

def allowed_file(filename):
    """Перевіряє, чи дозволений формат файлу"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

@own_works_bp.route('/delete/<int:work_id>', methods=['POST'])
@login_required
@admin_required
def delete(work_id):
    """Видалення роботи"""
    
    work = OwnWork.query.get_or_404(work_id)
    
    try:
        # Налаштування Cloudinary
        cloudinary.config(
            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=current_app.config['CLOUDINARY_API_KEY'],
            api_secret=current_app.config['CLOUDINARY_API_SECRET']
        )
        
        # Видаляємо зображення
        for image in work.images:
            if image.cloudinary_public_id:
                try:
                    cloudinary.uploader.destroy(image.cloudinary_public_id)
                    current_app.logger.info(f"Зображення видалено з Cloudinary: {image.cloudinary_public_id}")
                except Exception as e:
                    current_app.logger.error(f"Помилка видалення зображення з Cloudinary: {str(e)}")
            db.session.delete(image)
        
        db.session.delete(work)
        db.session.commit()
        
        flash('Роботу успішно видалено!', 'success')
        return redirect(url_for('own_works.index'))
        
    except Exception as e:
        current_app.logger.error(f"Помилка видалення роботи: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@own_works_bp.route('/image_delete/<int:image_id>/<int:work_id>', methods=['POST'])
@login_required
@admin_required
def delete_image(image_id, work_id):
    """Видалення зображення з роботи"""
    # Додаємо логування для відстеження виклику функції
    current_app.logger.info(f"Виклик функції delete_image з image_id={image_id}, work_id={work_id}")
    
    # Отримуємо об'єкти з бази даних
    work = OwnWork.query.get_or_404(work_id)
    image = Image.query.get_or_404(image_id)
    
    current_app.logger.info(f"Знайдено роботу: {work.id}, зображення: {image.id}")
    
    # Перевіряємо, чи зображення належить цій роботі
    if image.own_work_id != work.id or not image.is_own_work:
        current_app.logger.error(f"Зображення не належить роботі: image.own_work_id={image.own_work_id}, work.id={work.id}")
        flash('Помилка: зображення не належить цій роботі', 'error')
        return redirect(url_for('own_works.edit', work_id=work.id))
    
    current_app.logger.info(f"Перевірка пройдена: зображення належить роботі")
    
    # Якщо це головне зображення, скидаємо головне зображення роботи
    if image.is_main:
        current_app.logger.info(f"Зображення є головним, шукаємо заміну")
        # Шукаємо інше зображення для встановлення як головне
        other_image = Image.query.filter(
            Image.own_work_id == work.id,
            Image.id != image.id,
            Image.is_own_work == True
        ).first()
        
        if other_image:
            current_app.logger.info(f"Знайдено інше зображення для головного: {other_image.id}")
            other_image.is_main = True
            work.main_image = other_image.filename
        else:
            current_app.logger.info(f"Інших зображень не знайдено, скидаємо головне зображення")
            work.main_image = None
    
    # Видаляємо зображення з Cloudinary
    try:
        if image.cloudinary_public_id:
            current_app.logger.info(f"Видаляємо зображення з Cloudinary: {image.cloudinary_public_id}")
            # Налаштування Cloudinary
            cloudinary.config(
                cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
                api_key=current_app.config['CLOUDINARY_API_KEY'],
                api_secret=current_app.config['CLOUDINARY_API_SECRET']
            )
            
            # Видаляємо зображення з Cloudinary
            result = cloudinary.uploader.destroy(image.cloudinary_public_id)
            current_app.logger.info(f"Результат видалення з Cloudinary: {result}")
    except Exception as e:
        current_app.logger.error(f"Помилка видалення зображення з Cloudinary: {str(e)}")
    
    # Видаляємо зв'язок зображення з роботою
    current_app.logger.info(f"Видаляємо зображення з бази даних: {image.id}")
    image.own_work_id = None
    
    # Видаляємо зображення з бази даних
    db.session.delete(image)
    
    # Зберігаємо зміни в базі даних
    try:
        db.session.commit()
        current_app.logger.info(f"Зображення успішно видалено з бази даних")
        flash('Зображення успішно видалено', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Помилка при збереженні змін в базі даних: {str(e)}")
        flash(f'Помилка при видаленні зображення: {str(e)}', 'error')
    
    # Перенаправляємо на секцію з галереєю зображень
    return redirect(url_for('own_works.edit', work_id=work.id) + '#gallery')

