from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Image
from forms.gallery import ImageUploadForm, ImageEditForm
import os
from PIL import Image as PILImage
import uuid
from datetime import datetime
from sqlalchemy import desc
import cloudinary
import cloudinary.uploader

gallery_bp = Blueprint('gallery', __name__)

def save_image(file, category=None, description=None):
    """Зберігає завантажене зображення в Cloudinary"""
    from utils.image_handler import upload_image, get_thumbnail_url
    
    if not file:
        return None
    
    # Завантажуємо оригінальне зображення
    upload_result = upload_image(
        file,
        folder='gallery',
        width=1920,
        height=1080,
        crop='limit'
    )
    
    if not upload_result:
        return None
    
    # Отримуємо URL мініатюри
    thumbnail_url = get_thumbnail_url(upload_result['public_id'])
    
    try:
        # Створюємо запис в базі даних
        image = Image(
            filename=upload_result['secure_url'],
            thumbnail=thumbnail_url,
            cloudinary_public_id=upload_result['public_id'],
            description=description,
            category=category,
            is_gallery=True
        )
        db.session.add(image)
        db.session.commit()
        current_app.logger.info(f"Зображення успішно збережено: {upload_result['public_id']}")
        return image
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Помилка збереження зображення: {str(e)}")
        return None

@gallery_bp.route('/')
def index():
    """Головна сторінка галереї"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    
    # Базовий запит
    query = Image.query.filter_by(is_gallery=True)
    
    # Фільтрація за категорією
    if category:
        query = query.filter_by(category=category)
    
    # Отримуємо зображення з пагінацією
    images = query.order_by(desc(Image.created_at)).paginate(
        page=page,
        per_page=current_app.config['GALLERY_ITEMS_PER_PAGE'],
        error_out=False
    )
    
    return render_template('gallery/index.html',
                         title='Галерея',
                         images=images,
                         current_category=category)

@gallery_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Завантаження нових зображень"""
    if not current_user.is_admin and not current_user.is_coach:
        flash('У вас немає прав для завантаження зображень', 'error')
        return redirect(url_for('gallery.index'))
    
    form = ImageUploadForm()
    
    if form.validate_on_submit():
        success_count = 0
        error_count = 0
        files = request.files.getlist('images')
        
        for file in files:
            if file:
                image = save_image(
                    file,
                    category=form.category.data,
                    description=form.description.data
                )
                if image:
                    success_count += 1
                else:
                    error_count += 1
        
        if success_count > 0:
            flash(f'{success_count} зображень успішно завантажено!', 'success')
        if error_count > 0:
            flash(f'Не вдалося завантажити {error_count} зображень.', 'error')
        
        return redirect(url_for('gallery.index'))
    
    return render_template('gallery/upload.html',
                         title='Завантаження зображень',
                         form=form)

@gallery_bp.route('/edit/<int:image_id>', methods=['GET', 'POST'])
@login_required
def edit(image_id):
    """Редагування інформації про зображення"""
    if not current_user.is_admin and not current_user.is_coach:
        flash('У вас немає прав для редагування зображень', 'error')
        return redirect(url_for('gallery.index'))
    
    image = Image.query.get_or_404(image_id)
    form = ImageEditForm(obj=image)
    
    if form.validate_on_submit():
        image.description = form.description.data
        image.category = form.category.data
        db.session.commit()
        
        flash('Інформацію про зображення оновлено!', 'success')
        return redirect(url_for('gallery.index'))
    
    return render_template('gallery/edit.html',
                         title='Редагування зображення',
                         form=form,
                         image=image)

@gallery_bp.route('/delete/<int:image_id>', methods=['POST'])
@login_required
def delete(image_id):
    """Видалення зображення"""
    if not current_user.is_admin and not current_user.is_coach:
        return jsonify({'success': False, 'error': 'Недостатньо прав'}), 403
    
    image = Image.query.get_or_404(image_id)
    
    try:
        # Налаштування Cloudinary
        cloudinary.config(
            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=current_app.config['CLOUDINARY_API_KEY'],
            api_secret=current_app.config['CLOUDINARY_API_SECRET']
        )
        
        # Видаляємо зображення з Cloudinary
        if image.cloudinary_public_id:
            try:
                cloudinary.uploader.destroy(image.cloudinary_public_id)
                current_app.logger.info(f"Зображення видалено з Cloudinary: {image.cloudinary_public_id}")
            except Exception as e:
                current_app.logger.error(f"Помилка видалення зображення з Cloudinary: {str(e)}")
        
        # Видаляємо запис з бази даних
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Помилка видалення зображення: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
