from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from utils.decorators import admin_required
from models import db, News, Image
from forms.news import NewsForm
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

news_bp = Blueprint('news', __name__)

def save_news_image(file):
    """Зберігає зображення для новини"""
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
        public_id = f"news_{int(time.time())}_{filename}"
        
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
            is_news=True
        )
        
        current_app.logger.info(f"Created image record: filename={image.filename}, thumbnail={image.thumbnail}")
        
        return image
        
    except Exception as e:
        current_app.logger.error(f"Error uploading image: {str(e)}")
        current_app.logger.exception("Full error details:")
        return None

@news_bp.route('/')
def index():
    """Головна сторінка новин"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    
    # Базовий запит
    query = News.query.filter_by(is_published=True)
    
    # Фільтрація за категорією
    if category:
        query = query.filter_by(category=category)
    
    # Отримуємо новини з пагінацією
    news = query.order_by(desc(News.created_at)).paginate(
        page=page,
        per_page=current_app.config['NEWS_PER_PAGE'],
        error_out=False
    )
    
    return render_template('news/index.html',
                         title='Новини',
                         news=news,
                         current_category=category)

@news_bp.route('/<int:news_id>')
def view(news_id):
    """Перегляд окремої новини"""
    news_item = News.query.get_or_404(news_id)
    
    # Якщо новина не опублікована, її можуть бачити тільки адміністратори
    if not news_item.is_published and not (current_user.is_authenticated and current_user.is_admin):
        abort(404)
    
    return render_template('news/view.html',
                         title=news_item.title,
                         news=news_item)

@news_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """Створення нової новини"""
    if not current_user.is_admin:
        flash('У вас немає прав для створення новин', 'error')
        return redirect(url_for('news.index'))
    
    form = NewsForm()
    
    if form.validate_on_submit():
        news = News(
            title=form.title.data,
            content=form.content.data,
            category=form.category.data,
            summary=form.summary.data,
            is_published=bool(int(form.is_published.data)),
            author_id=current_user.id
        )
        db.session.add(news)
        
        # Зберігаємо головне зображення
        if 'main_image' in request.files:
            main_image = request.files['main_image']
            if main_image:
                image = save_news_image(main_image)
                if image:
                    news.images.append(image)
                    current_app.logger.info(f"Головне зображення збережено: {image.filename}")
        
        # Зберігаємо додаткові зображення для галереї
        if 'gallery_images' in request.files:
            files = request.files.getlist('gallery_images')
            for file in files:
                if file:
                    image = save_news_image(file)
                    if image:
                        news.images.append(image)
                        current_app.logger.info(f"Додаткове зображення збережено: {image.filename}")
        
        db.session.commit()
        
        flash('Новину успішно створено!', 'success')
        return redirect(url_for('news.view', news_id=news.id))
    
    return render_template('news/create.html',
                         title='Створення новини',
                         form=form)

@news_bp.route('/edit/<int:news_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(news_id):
    """Редагування новини"""
    
    news = News.query.get_or_404(news_id)
    form = NewsForm(obj=news)
    
    if form.validate_on_submit():
        news.title = form.title.data
        news.content = form.content.data
        news.category = form.category.data
        news.summary = form.summary.data
        news.is_published = bool(int(form.is_published.data))
        news.updated_at = datetime.utcnow()
        
        # Зберігаємо нові зображення
        files = request.files.getlist('images')
        for file in files:
            if file:
                image = save_news_image(file)
                if image:
                    news.images.append(image)
        
        db.session.commit()
        
        flash('Новину успішно оновлено!', 'success')
        return redirect(url_for('news.view', news_id=news.id))
    
    return render_template('news/edit.html',
                         title='Редагування новини',
                         form=form,
                         news=news)

@news_bp.route('/delete/<int:news_id>', methods=['POST'])
@login_required
@admin_required
def delete(news_id):
    """Видалення новини"""
    
    news = News.query.get_or_404(news_id)
    
    try:
        # Налаштування Cloudinary
        cloudinary.config(
            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=current_app.config['CLOUDINARY_API_KEY'],
            api_secret=current_app.config['CLOUDINARY_API_SECRET']
        )
        
        # Видаляємо зображення
        for image in news.images:
            if image.cloudinary_public_id:
                try:
                    cloudinary.uploader.destroy(image.cloudinary_public_id)
                    current_app.logger.info(f"Зображення видалено з Cloudinary: {image.cloudinary_public_id}")
                except Exception as e:
                    current_app.logger.error(f"Помилка видалення зображення з Cloudinary: {str(e)}")
            db.session.delete(image)
        
        db.session.delete(news)
        db.session.commit()
        
        flash('Новину успішно видалено!', 'success')
        return redirect(url_for('news.index'))
        
    except Exception as e:
        current_app.logger.error(f"Помилка видалення новини: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@news_bp.route('/image/delete/<int:image_id>', methods=['POST'])
@login_required
@admin_required
def delete_image(image_id):
    """Видалення зображення з новини"""
    
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
        
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Помилка видалення зображення: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
