from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, session
import base64
from werkzeug.utils import secure_filename
import time
import cloudinary
import cloudinary.uploader
import cloudinary.utils
import traceback

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
from flask_login import login_required, current_user
from models import db, User, News, Image, Monument, MonumentImage, OwnWork
from sqlalchemy import text
from functools import wraps
from werkzeug.utils import secure_filename
import os
import time
import cloudinary
import cloudinary.uploader
import cloudinary.utils
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Будь ласка, увійдіть в систему.', 'error')
            return redirect(url_for('auth.login'))
        
        # Перевіряємо статус адміністратора
        if not current_user.check_admin_status():
            flash('У вас немає прав для доступу до цієї сторінки.', 'error')
            return redirect(url_for('main.index'))
            
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def index():
    """Головна сторінка адмін-панелі"""
    stats = {
        'users': User.query.count(),
        'news': News.query.count(),
        'own_works': OwnWork.query.count(),
        'images': Image.query.count(),
        'monuments': Monument.query.count(),
        'monument_images': MonumentImage.query.count()
    }
    
    # Події видалені
    recent_events = []
    
    # Останні новини
    recent_news = News.query.order_by(News.created_at.desc()).limit(5).all()
    
    # Останні власні роботи
    recent_own_works = OwnWork.query.order_by(OwnWork.created_at.desc()).limit(5).all()
    
    # Останні користувачі
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/index.html',
                         title='Адмін-панель',
                         stats=stats,
                         recent_events=recent_events,
                         recent_news=recent_news,
                         recent_own_works=recent_own_works,
                         recent_users=recent_users)

@admin_bp.route('/users')
@admin_required
def users():
    """Управління користувачами"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html',
                         title='Користувачі',
                         users=users)




@admin_bp.route('/news')
@admin_required
def news():
    """Управління новинами"""
    news_items = News.query.order_by(News.created_at.desc()).all()
    return render_template('admin/news.html',
                         title='Новини',
                         news=news_items)

@admin_bp.route('/own-works')
@admin_required
def own_works():
    """Управління власними роботами"""
    own_works_items = OwnWork.query.order_by(OwnWork.created_at.desc()).all()
    return render_template('admin/own_works.html',
                         title='Власні роботи',
                         own_works=own_works_items)



@admin_bp.route('/images')
@admin_required
def images():
    """Управління зображеннями галереї"""
    # Вибираємо тільки зображення галереї
    images = Image.query.filter_by(is_gallery=True).order_by(Image.created_at.desc()).all()
    
    # Логування для діагностики
    current_app.logger.info(f"Total gallery images found: {len(images)}")
    for img in images:
        current_app.logger.info(f"Gallery Image ID: {img.id}, URL: {img.filename}, Thumbnail: {img.thumbnail}")
        current_app.logger.info(f"Image properties: image_url={img.image_url}, thumbnail_url={img.thumbnail_url}")
        current_app.logger.info(f"Image flags: is_gallery={img.is_gallery}, is_news={img.is_news}")
        current_app.logger.info(f"Image cloudinary_public_id: {img.cloudinary_public_id}")
    
    return render_template('admin/images.html',
                         title='Зображення галереї',
                         images=images)

@admin_bp.route('/monuments')
@admin_required
def monuments():
    """Управління пам'ятниками"""
    # Отримуємо параметр пошуку з URL
    search_query = request.args.get('search', '')
    
    # Якщо є пошуковий запит, фільтруємо пам'ятники
    if search_query:
        # Шукаємо за артикулом (точний збіг) або за назвою (частковий збіг)
        monuments = Monument.query.filter(
            db.or_(
                Monument.article.ilike(f"%{search_query}%"),
                Monument.name.ilike(f"%{search_query}%")
            )
        ).order_by(Monument.created_at.desc()).all()
    else:
        # Якщо немає пошукового запиту, показуємо всі пам'ятники
        monuments = Monument.query.order_by(Monument.created_at.desc()).all()
    
    return render_template('admin/monuments.html',
                         title='Пам\'ятники',
                         monuments=monuments,
                         search_query=search_query)

# CRUD для власних робіт

@admin_bp.route('/own-works/create', methods=['GET', 'POST'])
@admin_required
def create_own_work():
    """Створення нової власної роботи"""
    from forms.own_work import OwnWorkForm
    
    form = OwnWorkForm()
    
    if form.validate_on_submit():
        # Створюємо нову власну роботу
        own_work = OwnWork(
            title=form.title.data,
            content=form.content.data,
            summary=form.summary.data,
            category=form.category.data,
            is_published=form.is_published.data,
            author_id=current_user.id
        )
        
        db.session.add(own_work)
        db.session.commit()
        
        # Зберігаємо зображення
        if form.images.data and any(form.images.data):
            for image_file in form.images.data:
                if image_file and allowed_file(image_file.filename):
                    try:
                        # Налаштування Cloudinary
                        cloudinary.config(
                            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
                            api_key=current_app.config['CLOUDINARY_API_KEY'],
                            api_secret=current_app.config['CLOUDINARY_API_SECRET']
                        )
                        
                        # Генеруємо унікальне ім'я файлу
                        timestamp = int(time.time())
                        public_id = f"own_works/{own_work.id}/{timestamp}"
                        
                        # Завантажуємо зображення в Cloudinary
                        upload_result = cloudinary.uploader.upload(
                            image_file,
                            public_id=public_id,
                            folder="own_works"
                        )
                        
                        # Зберігаємо інформацію про зображення в базі даних
                        image = Image(
                            filename=upload_result['secure_url'],
                            cloudinary_public_id=public_id,
                            is_own_work=True,
                            own_work_id=own_work.id
                        )
                        
                        db.session.add(image)
                    except Exception as e:
                        current_app.logger.error(f"Помилка завантаження зображення: {str(e)}")
                        traceback.print_exc()
        
        db.session.commit()
        flash('Власну роботу успішно створено', 'success')
        return redirect(url_for('admin.own_works'))
    
    return render_template('admin/own_work_form.html',
                         title='Створення власної роботи',
                         form=form,
                         action='create')

@admin_bp.route('/own-works/<int:own_work_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_own_work(own_work_id):
    """Редагування власної роботи"""
    from forms.own_work import OwnWorkForm
    
    own_work = OwnWork.query.get_or_404(own_work_id)
    form = OwnWorkForm(obj=own_work)
    
    if form.validate_on_submit():
        # Оновлюємо дані власної роботи
        own_work.title = form.title.data
        own_work.content = form.content.data
        own_work.summary = form.summary.data
        own_work.category = form.category.data
        own_work.is_published = form.is_published.data
        own_work.updated_at = datetime.utcnow()
        
        # Зберігаємо зображення
        if form.images.data and any(form.images.data):
            for image_file in form.images.data:
                if image_file and allowed_file(image_file.filename):
                    try:
                        # Налаштування Cloudinary
                        cloudinary.config(
                            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
                            api_key=current_app.config['CLOUDINARY_API_KEY'],
                            api_secret=current_app.config['CLOUDINARY_API_SECRET']
                        )
                        
                        # Генеруємо унікальне ім'я файлу
                        timestamp = int(time.time())
                        public_id = f"own_works/{own_work.id}/{timestamp}"
                        
                        # Завантажуємо зображення в Cloudinary
                        upload_result = cloudinary.uploader.upload(
                            image_file,
                            public_id=public_id,
                            folder="own_works"
                        )
                        
                        # Зберігаємо інформацію про зображення в базі даних
                        image = Image(
                            filename=upload_result['secure_url'],
                            cloudinary_public_id=public_id,
                            is_own_work=True,
                            own_work_id=own_work.id
                        )
                        
                        db.session.add(image)
                    except Exception as e:
                        current_app.logger.error(f"Помилка завантаження зображення: {str(e)}")
                        traceback.print_exc()
        
        db.session.commit()
        flash('Власну роботу успішно оновлено', 'success')
        return redirect(url_for('admin.own_works'))
    
    # Отримуємо існуючі зображення для відображення
    images = Image.query.filter_by(is_own_work=True, own_work_id=own_work.id).all()
    
    return render_template('admin/own_work_form.html',
                         title='Редагування власної роботи',
                         form=form,
                         action='edit',
                         own_work=own_work,
                         images=images)

@admin_bp.route('/own-works/<int:own_work_id>/delete', methods=['POST'])
@admin_required
def delete_own_work(own_work_id):
    """Видалення власної роботи"""
    own_work = OwnWork.query.get_or_404(own_work_id)
    
    # Видаляємо зображення з Cloudinary
    images = Image.query.filter_by(is_own_work=True, own_work_id=own_work.id).all()
    
    for image in images:
        try:
            if image.cloudinary_public_id:
                # Налаштування Cloudinary
                cloudinary.config(
                    cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
                    api_key=current_app.config['CLOUDINARY_API_KEY'],
                    api_secret=current_app.config['CLOUDINARY_API_SECRET']
                )
                
                # Видаляємо зображення з Cloudinary
                cloudinary.uploader.destroy(image.cloudinary_public_id)
        except Exception as e:
            current_app.logger.error(f"Помилка видалення зображення з Cloudinary: {str(e)}")
        
        # Видаляємо запис про зображення з бази даних
        db.session.delete(image)
    
    # Видаляємо власну роботу
    db.session.delete(own_work)
    db.session.commit()
    
    flash('Власну роботу успішно видалено', 'success')
    return redirect(url_for('admin.own_works'))

# CRUD для новин
@admin_bp.route('/news/create', methods=['GET', 'POST'])
@admin_required
def create_news():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image = request.files.get('image')
        
        if not title or not content:
            flash('Заповніть всі обов\'язкові поля', 'error')
            return redirect(url_for('admin.create_news'))
            
        news = News(
            title=title,
            content=content,
            author_id=current_user.id
        )
        db.session.add(news)
        
        if image:
            try:
                # Налаштування Cloudinary
                cloudinary.config(
                    cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
                    api_key=current_app.config['CLOUDINARY_API_KEY'],
                    api_secret=current_app.config['CLOUDINARY_API_SECRET']
                )
                
                # Генеруємо унікальне ім'я файлу
                filename = secure_filename(image.filename)
                public_id = f"news_{int(time.time())}_{filename}"
                
                # Завантажуємо файл до Cloudinary
                upload_result = cloudinary.uploader.upload(
                    image,
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
                
                # Створюємо запис в базі даних
                new_image = Image(
                    filename=upload_result['secure_url'],
                    thumbnail=thumbnail_url,
                    cloudinary_public_id=upload_result['public_id'],
                    is_news=True
                )
                news.images.append(new_image)
                current_app.logger.info(f"Зображення успішно завантажено: {filename}")
                
            except Exception as e:
                current_app.logger.error(f"Помилка завантаження зображення: {str(e)}")
                flash(f'Помилка завантаження зображення', 'error')
        
        db.session.commit()
        flash('Новину успішно створено', 'success')
        return redirect(url_for('admin.news'))
        
    return render_template('admin/news_form.html', title='Створити новину')

@admin_bp.route('/news/<int:news_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_news(news_id):
    news = News.query.get_or_404(news_id)
    
    if request.method == 'POST':
        news.title = request.form.get('title')
        news.content = request.form.get('content')
        
        image = request.files.get('image')
        if image:
            try:
                # Налаштування Cloudinary
                cloudinary.config(
                    cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
                    api_key=current_app.config['CLOUDINARY_API_KEY'],
                    api_secret=current_app.config['CLOUDINARY_API_SECRET']
                )
                
                # Видаляємо всі старі зображення новини
                for old_image in news.images:
                    if old_image.cloudinary_public_id:
                        try:
                            cloudinary.uploader.destroy(old_image.cloudinary_public_id)
                            current_app.logger.info(f"Зображення видалено з Cloudinary: {old_image.cloudinary_public_id}")
                        except Exception as e:
                            current_app.logger.error(f"Помилка видалення зображення з Cloudinary: {str(e)}")
                    db.session.delete(old_image)
                
                # Генеруємо унікальне ім'я файлу
                filename = secure_filename(image.filename)
                public_id = f"news_{int(time.time())}_{filename}"
                
                # Завантажуємо файл до Cloudinary
                upload_result = cloudinary.uploader.upload(
                    image,
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
                
                # Створюємо новий запис в базі даних
                new_image = Image(
                    filename=upload_result['secure_url'],
                    thumbnail=thumbnail_url,
                    cloudinary_public_id=upload_result['public_id'],
                    is_news=True
                )
                news.images.append(new_image)
                current_app.logger.info(f"Зображення успішно завантажено: {filename}")
                
            except Exception as e:
                current_app.logger.error(f"Помилка завантаження зображення: {str(e)}")
                flash(f'Помилка завантаження зображення', 'error')
            
        db.session.commit()
        flash('Новину успішно оновлено', 'success')
        return redirect(url_for('admin.news'))
        
    return render_template('admin/news_form.html', title='Редагувати новину', news=news)

@admin_bp.route('/news/<int:news_id>/delete', methods=['POST'])
@admin_required
def delete_news(news_id):
    news = News.query.get_or_404(news_id)
    
    try:
        # Налаштування Cloudinary
        cloudinary.config(
            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=current_app.config['CLOUDINARY_API_KEY'],
            api_secret=current_app.config['CLOUDINARY_API_SECRET']
        )
        
        # Видаляємо всі зображення новини
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
        flash('Новину успішно видалено', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Помилка видалення новини: {str(e)}")
        flash('Помилка видалення новини', 'error')
        
    return redirect(url_for('admin.news'))

# CRUD для галереї
@admin_bp.route('/gallery/preview', methods=['POST'])
@admin_required
def preview_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
        
    image = request.files['image']
    if not image.filename:
        return jsonify({'error': 'No selected file'}), 400
        
    # Перевіряємо розширення файлу
    if not allowed_file(image.filename):
        return jsonify({'error': 'Invalid file type'}), 400
        
    try:
        # Зчитуємо зображення в base64
        image_data = base64.b64encode(image.read()).decode('utf-8')
        return jsonify({
            'preview': f'data:image/jpeg;base64,{image_data}',
            'filename': image.filename
        })
    except Exception as e:
        current_app.logger.error(f'Error creating preview: {str(e)}')
        return jsonify({'error': 'Failed to create preview'}), 500

def save_gallery_image(file, description=None):
    """Зберігає зображення для галереї"""
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
        
        # Генеруємо унікальне ім'я файлу
        filename = secure_filename(file.filename)
        public_id = f"gallery_{int(time.time())}_{filename}"
        
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
            fetch_format="auto",
            secure=True
        )[0]
        
        # Переконуємося, що URL використовує HTTPS
        if thumbnail_url.startswith('http:'):
            thumbnail_url = thumbnail_url.replace('http:', 'https:', 1)
        
        # Створюємо запис в базі даних
        image = Image(
            filename=upload_result['secure_url'],
            thumbnail=thumbnail_url,
            cloudinary_public_id=upload_result['public_id'],
            description=description,
            is_gallery=True  # Важливо встановити цей прапорець
        )
        
        # Логування для діагностики
        current_app.logger.info(f"Image created: ID={image.id}, is_gallery={image.is_gallery}, URL={image.filename}")
        
        current_app.logger.info(f"Created image record: filename={image.filename}, thumbnail={image.thumbnail}")
        
        return image
        
    except Exception as e:
        current_app.logger.error(f"Error uploading image: {str(e)}")
        current_app.logger.exception("Full error details:")
        return None

@admin_bp.route('/gallery/upload', methods=['GET', 'POST'])
@admin_required
def upload_image():
    if request.method == 'POST':
        images = request.files.getlist('images')
        description = request.form.get('description')
        
        try:
            # Налаштування Cloudinary
            cloudinary.config(
                cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
                api_key=current_app.config['CLOUDINARY_API_KEY'],
                api_secret=current_app.config['CLOUDINARY_API_SECRET']
            )
            
            for image in images:
                if image:
                    # Перевіряємо розмір файлу (5MB)
                    if len(image.read()) > 5 * 1024 * 1024:
                        flash(f'Файл {image.filename} занадто великий. Максимальний розмір - 5MB', 'error')
                        continue
                    
                    # Повертаємо курсор на початок файлу
                    image.seek(0)
                    
                    # Генеруємо унікальне ім'я файлу
                    filename = secure_filename(image.filename)
                    public_id = f"gallery_{int(time.time())}_{filename}"
                    
                    # Завантажуємо файл до Cloudinary
                    upload_result = cloudinary.uploader.upload(
                        image,
                        public_id=public_id,
                        folder="okinava",
                        overwrite=True,
                        resource_type="image"
                    )
                    
                    current_app.logger.info(f"Cloudinary upload result: {upload_result}")
                    
                    # Створюємо URL для мініатюри
                    thumbnail_url = cloudinary.utils.cloudinary_url(
                        upload_result['public_id'],
                        width=400,
                        height=300,
                        crop="fill",
                        quality="auto",
                        fetch_format="auto",
                        secure=True
                    )[0]
                    
                    # Переконуємося, що URL використовує HTTPS
                    if thumbnail_url.startswith('http:'):
                        thumbnail_url = thumbnail_url.replace('http:', 'https:', 1)
                    
                    current_app.logger.info(f"Generated thumbnail URL: {thumbnail_url}")
                    
                    # Створюємо запис в базі даних
                    new_image = Image(
                        filename=upload_result['secure_url'],
                        thumbnail=thumbnail_url,
                        cloudinary_public_id=upload_result['public_id'],
                        description=description,
                        is_gallery=True
                    )
                    
                    current_app.logger.info(f"Created image record: filename={new_image.filename}, thumbnail={new_image.thumbnail}")
                    current_app.logger.info(f"Image properties: image_url={new_image.image_url}, thumbnail_url={new_image.thumbnail_url}")
                    
                    db.session.add(new_image)
                    current_app.logger.info(f"Зображення успішно завантажено: {filename}")
            
            db.session.commit()
            flash('Зображення успішно завантажено', 'success')
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error uploading images: {str(e)}")
            current_app.logger.exception("Full error details:")
            flash('Помилка завантаження зображень', 'error')
        
        return redirect(url_for('admin.images'))
        
    return render_template('admin/gallery_upload.html', title='Завантажити зображення')

@admin_bp.route('/gallery/<int:image_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_image(image_id):
    image = Image.query.get_or_404(image_id)
    
    if request.method == 'POST':
        image.description = request.form.get('description')
        image.is_gallery = request.form.get('is_gallery', type=bool)
        
        db.session.commit()
        flash('Інформацію про зображення оновлено', 'success')
        return redirect(url_for('admin.images'))
        
    return render_template('admin/gallery_edit.html', title='Редагувати зображення', image=image)

@admin_bp.route('/gallery/delete/<int:image_id>', methods=['POST'])
@admin_required
def delete_image(image_id):
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
            cloudinary.uploader.destroy(image.cloudinary_public_id)
            current_app.logger.info(f"Зображення видалено з Cloudinary: {image.cloudinary_public_id}")
        
        # Видаляємо запис з бази даних
        db.session.delete(image)
        db.session.commit()
        
        flash('Зображення успішно видалено', 'success')
    except Exception as e:
        current_app.logger.error(f"Помилка видалення зображення: {str(e)}")
        flash('Помилка видалення зображення', 'error')
        
    return redirect(url_for('admin.images'))

@admin_bp.route('/user/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    """Зміна статусу адміністратора"""
    user = User.query.get_or_404(user_id)
    
    # Не можна забрати права у самого себе
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Ви не можете забрати права адміністратора у самого себе'}), 400
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_admin': user.is_admin
    })

@admin_bp.route('/user/<int:user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_active(user_id):
    """Блокування/розблокування користувача"""
    user = User.query.get_or_404(user_id)
    
    # Не можна заблокувати самого себе
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'Ви не можете заблокувати самого себе'}), 400
    
    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_active': user.is_active
    })


# Сторінка з поясненням артикулів пам'ятників
@admin_bp.route('/article-help')
@admin_required
def article_help():
    """Сторінка з поясненням артикулів пам'ятників"""
    return render_template('admin/article_help.html', active_page='monuments')


# CRUD для пам'ятників
@admin_bp.route('/monuments/create', methods=['GET', 'POST'])
@admin_required
def create_monument():
    """Створення нового пам'ятника"""
    if request.method == 'POST':
        name = request.form.get('name')
        article = request.form.get('article')
        price = request.form.get('price')
        description = request.form.get('description')
        category = request.form.get('category')
        dimensions = request.form.get('dimensions')
        material = request.form.get('material')
        color = request.form.get('color')
        images = request.files.getlist('images')
        
        if not name or not article:
            flash('Назва та артикул пам\'ятника обов\'язкові', 'error')
            return redirect(url_for('admin.create_monument'))
            
        # Перевіряємо, чи існує пам'ятник з таким артикулом
        existing_monument = Monument.query.filter_by(article=article).first()
        if existing_monument:
            flash(f'Пам\'ятник з артикулом {article} вже існує', 'error')
            return redirect(url_for('admin.create_monument'))
        
        # Обробка додаткових полів
        weight = request.form.get('weight')
        availability = request.form.get('availability')
        production_time = request.form.get('production_time')
        is_popular = 'is_popular' in request.form
        discount_percent = request.form.get('discount_percent')
        old_price = request.form.get('old_price')
        
        # SEO інформація
        seo_title = request.form.get('seo_title')
        seo_description = request.form.get('seo_description')
        seo_keywords = request.form.get('seo_keywords')
        
        # Додаткові характеристики
        style = request.form.get('style')
        warranty = request.form.get('warranty')
        installation_included = 'installation_included' in request.form
        delivery_info = request.form.get('delivery_info')
        
        # Відображення на сайті
        is_new = 'is_new' in request.form
        is_featured = 'is_featured' in request.form
        display_order = request.form.get('display_order')
        
        # Пов'язані пам'ятники
        related_products = request.form.get('related_products')
        
        # Створюємо новий пам'ятник
        monument = Monument(
            name=name,
            article=article.upper(),  # Зберігаємо артикул у верхньому регістрі
            price=int(price) if price and price.isdigit() else None,
            description=description,
            category=category,
            dimensions=dimensions,
            material=material,
            color=color,
            weight=float(weight) if weight and weight.strip() else None,
            availability=availability,
            production_time=production_time,
            is_popular=is_popular,
            discount_percent=int(discount_percent) if discount_percent and discount_percent.strip() else None,
            old_price=int(old_price) if old_price and old_price.strip() else None,
            
            # SEO інформація
            seo_title=seo_title,
            seo_description=seo_description,
            seo_keywords=seo_keywords,
            
            # Додаткові характеристики
            style=style,
            warranty=warranty,
            installation_included=installation_included,
            delivery_info=delivery_info,
            
            # Відображення на сайті
            is_new=is_new,
            is_featured=is_featured,
            display_order=int(display_order) if display_order and display_order.strip() else 0,
            
            # Пов'язані пам'ятники
            related_products=related_products,
            
            is_active=True
        )
        
        db.session.add(monument)
        db.session.flush()  # Отримуємо ID пам'ятника
        
        # Обробка зображень
        if images:
            for i, image in enumerate(images):
                if image and allowed_file(image.filename):
                    try:
                        # Налаштування Cloudinary
                        cloudinary.config(
                            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
                            api_key=current_app.config['CLOUDINARY_API_KEY'],
                            api_secret=current_app.config['CLOUDINARY_API_SECRET']
                        )
                        
                        # Генеруємо унікальне ім'я файлу
                        filename = secure_filename(image.filename)
                        # Додаємо артикул до назви зображення для кращої організації
                        public_id = f"{monument.article}_{monument.id}_{int(time.time())}_{i}"
                        
                        # Визначаємо папку в Cloudinary на основі категорії пам'ятника
                        category_folder = monument.category.replace('/', '_') if monument.category else 'other'
                        folder_path = f"monuments/{category_folder}"
                        
                        # Завантажуємо файл до Cloudinary
                        upload_result = cloudinary.uploader.upload(
                            image,
                            public_id=public_id,
                            folder=folder_path,
                            overwrite=True,
                            resource_type="image",
                            tags=[monument.article, category_folder]  # Додаємо теги для полегшення пошуку
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
                        
                        # Створюємо запис в базі даних
                        monument_image = MonumentImage(
                            monument_id=monument.id,
                            filename=upload_result['secure_url'],
                            is_main=(i == 0)  # Перше зображення - головне
                        )
                        
                        db.session.add(monument_image)
                        
                        # Оновлюємо головне зображення пам'ятника
                        if i == 0:
                            monument.main_image = upload_result['secure_url']
                        
                    except Exception as e:
                        current_app.logger.error(f"Помилка завантаження зображення: {str(e)}")
                        flash(f'Помилка завантаження зображення {image.filename}', 'error')
        
        db.session.commit()
        flash('Пам\'ятник успішно створено', 'success')
        return redirect(url_for('admin.monuments'))
    
    return render_template('admin/create_monument.html', title='Створення пам\'ятника')

@admin_bp.route('/monuments/<int:monument_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_monument(monument_id):
    """Перенаправлення на простий редактор пам'ятників"""
    # Зберігаємо ідентифікатор адміністратора в сесії
    if current_user.is_authenticated and current_user.is_admin:
        session['admin_id'] = current_user.id
        session['admin_username'] = current_user.username
        session.permanent = True
    
    # Перенаправляємо на простий редактор
    return redirect(url_for('simple_edit.edit_monument', monument_id=monument_id))

@admin_bp.route('/monuments/<int:monument_id>/delete', methods=['POST'])
@admin_required
def delete_monument(monument_id):
    """Видалення пам'ятника"""
    monument = Monument.query.get_or_404(monument_id)
    
    # Видаляємо зображення з Cloudinary
    for image in monument.images:
        try:
            if image.filename and 'cloudinary' in image.filename:
                # Отримуємо public_id з URL
                parts = image.filename.split('/')
                if len(parts) > 6:
                    public_id = f"monuments/{parts[-2]}/{parts[-1].split('.')[0]}"
                    
                    # Налаштування Cloudinary
                    cloudinary.config(
                        cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
                        api_key=current_app.config['CLOUDINARY_API_KEY'],
                        api_secret=current_app.config['CLOUDINARY_API_SECRET']
                    )
                    
                    # Видаляємо зображення з Cloudinary
                    cloudinary.uploader.destroy(public_id)
        except Exception as e:
            current_app.logger.error(f"Помилка видалення зображення з Cloudinary: {str(e)}")
    
    # Видаляємо пам'ятник з бази даних
    db.session.delete(monument)
    db.session.commit()
    
    flash('Пам\'ятник успішно видалено', 'success')
    return redirect(url_for('admin.monuments'))

@admin_bp.route('/monuments/<int:monument_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_monument_active(monument_id):
    """Зміна статусу активності пам'ятника"""
    try:
        monument = Monument.query.get_or_404(monument_id)
        monument.is_active = not monument.is_active
        db.session.commit()
        
        status = 'активовано' if monument.is_active else 'деактивовано'
        
        # Повертаємо JSON-відповідь замість перенаправлення
        return jsonify({
            'success': True,
            'is_active': monument.is_active,
            'message': f'Пам\'ятник успішно {status}',
            'status': status
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Помилка при зміні статусу пам'ятника: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Помилка: {str(e)}'
        }), 500

@admin_bp.route('/monuments/<int:monument_id>/images/<int:image_id>/set-main', methods=['POST'])
@admin_required
def set_main_image(monument_id, image_id):
    """Встановлення головного зображення для пам'ятника"""
    monument = Monument.query.get_or_404(monument_id)
    image = MonumentImage.query.get_or_404(image_id)
    
    # Перевіряємо, чи зображення належить цьому пам'ятнику
    if image.monument_id != monument.id:
        flash('Зображення не належить цьому пам\'ятнику', 'error')
        return redirect(url_for('admin.edit_monument', monument_id=monument.id))
    
    # Знімаємо позначку головного зображення з усіх зображень пам'ятника
    for img in monument.images:
        img.is_main = False
    
    # Встановлюємо нове головне зображення
    image.is_main = True
    monument.main_image = image.filename
    
    db.session.commit()
    flash('Головне зображення успішно змінено', 'success')
    
    return redirect(url_for('admin.edit_monument', monument_id=monument.id))

@admin_bp.route('/monuments/<int:monument_id>/images/<int:image_id>/delete', methods=['POST'])
@admin_required
def delete_monument_image(monument_id, image_id):
    """Видалення зображення пам'ятника"""
    monument = Monument.query.get_or_404(monument_id)
    image = MonumentImage.query.get_or_404(image_id)
    
    # Перевіряємо, чи зображення належить цьому пам'ятнику
    if image.monument_id != monument.id:
        flash('Зображення не належить цьому пам\'ятнику', 'error')
        return redirect(url_for('admin.edit_monument', monument_id=monument.id))
    
    # Якщо це головне зображення, скидаємо головне зображення пам'ятника
    if image.is_main:
        # Шукаємо інше зображення для встановлення як головне
        other_image = MonumentImage.query.filter(
            MonumentImage.monument_id == monument.id,
            MonumentImage.id != image.id
        ).first()
        
        if other_image:
            other_image.is_main = True
            monument.main_image = other_image.filename
        else:
            monument.main_image = None
    
    # Видаляємо зображення з Cloudinary
    try:
        if image.filename and 'cloudinary' in image.filename:
            # Отримуємо public_id з URL
            parts = image.filename.split('/')
            if len(parts) > 6:
                public_id = f"monuments/{parts[-2]}/{parts[-1].split('.')[0]}"
                
                # Налаштування Cloudinary
                cloudinary.config(
                    cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
                    api_key=current_app.config['CLOUDINARY_API_KEY'],
                    api_secret=current_app.config['CLOUDINARY_API_SECRET']
                )
                
                # Видаляємо зображення з Cloudinary
                cloudinary.uploader.destroy(public_id)
    except Exception as e:
        current_app.logger.error(f"Помилка видалення зображення з Cloudinary: {str(e)}")
    
    # Видаляємо зображення з бази даних
    db.session.delete(image)
    db.session.commit()
    
    flash('Зображення успішно видалено', 'success')
    return redirect(url_for('admin.edit_monument', monument_id=monument.id))
