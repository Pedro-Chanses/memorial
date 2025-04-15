from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Post, Category, Image, Application
from forms.posts import PostForm, ApplicationForm
import os
from datetime import datetime
from sqlalchemy import desc

posts_bp = Blueprint('posts', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@posts_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = PostForm()
    
    # Отримуємо всі категорії
    categories = Category.query.all()
    form.category.choices = [(c.id, c.name) for c in categories]
    
    # Встановлюємо категорію "Загальна" за замовчуванням
    if request.method == 'GET':
        general_category = Category.query.filter_by(name='Загальна').first()
        if general_category:
            form.category.data = general_category.id
    
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            body=form.body.data,
            location=form.location.data,
            contact_info=form.contact_info.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            category_id=form.category.data,
            author=current_user
        )
        db.session.add(post)
        db.session.flush()  # Отримуємо ID поста перед збереженням зображень
        
        # Обробка зображень
        if form.images.data:
            for image_file in form.images.data:
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    
                    # Зберігаємо файл
                    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    image_file.save(image_path)
                    
                    # Створюємо запис в базі даних
                    image = Image(filename=filename, post=post)
                    db.session.add(image)
        
        try:
            db.session.commit()
            flash('Оголошення успішно створено!', 'success')
            return redirect(url_for('posts.view', post_id=post.id))
        except Exception as e:
            db.session.rollback()
            flash('Помилка при створенні оголошення. Спробуйте ще раз.', 'danger')
            current_app.logger.error(f'Error creating post: {str(e)}')
    
    return render_template('posts/create.html', title='Створити оголошення', form=form)

@posts_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search_query = request.args.get('q')
    
    # Базовий запит
    query = Post.query.filter_by(is_active=True)
    
    # Фільтрація за категорією
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Пошук за ключовими словами
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Post.title.ilike(search),
                Post.body.ilike(search),
                Post.location.ilike(search)
            )
        )
    
    # Сортування за датою створення
    query = query.order_by(Post.created_at.desc())
    
    # Пагінація
    posts = query.paginate(
        page=page,
        per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    
    # Отримання всіх категорій для фільтра
    categories = Category.query.all()
    
    return render_template('posts/index.html',
                         title='Проекти',
                         posts=posts,
                         categories=categories,
                         current_category=category_id,
                         search_query=search_query)

@posts_bp.route('/<int:post_id>')
def view(post_id):
    post = Post.query.get_or_404(post_id)
    form = ApplicationForm()
    
    # Збільшуємо лічильник переглядів
    post.views += 1
    db.session.commit()
    
    # Отримуємо схожі оголошення
    similar_posts = Post.query.filter(
        Post.category_id == post.category_id,
        Post.id != post.id,
        Post.is_active == True
    ).order_by(desc(Post.created_at)).limit(3).all()
    
    # Конвертуємо images в список для шаблону
    post.images = list(post.images)
    
    return render_template('posts/view.html',
                         title=post.title,
                         post=post,
                         form=form,
                         similar_posts=similar_posts)

@posts_bp.route('/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin:
        flash('У вас немає прав для редагування цього оголошення.', 'danger')
        return redirect(url_for('posts.view', post_id=post.id))
    
    form = PostForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.body.data
        post.location = form.location.data
        post.contact_info = form.contact_info.data
        post.start_date = form.start_date.data
        post.end_date = form.end_date.data
        post.category_id = form.category.data
        
        # Обробка нових зображень
        for image_file in request.files.getlist('images'):
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                image_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                
                image = Image(filename=filename, post=post)
                db.session.add(image)
        
        db.session.commit()
        flash('Оголошення успішно оновлено!', 'success')
        return redirect(url_for('posts.view', post_id=post.id))
    
    elif request.method == 'GET':
        form.title.data = post.title
        form.body.data = post.body
        form.location.data = post.location
        form.contact_info.data = post.contact_info
        form.start_date.data = post.start_date
        form.end_date.data = post.end_date
        form.category.data = post.category_id
    
    return render_template('posts/edit.html',
                         title='Редагувати оголошення',
                         form=form,
                         post=post)

@posts_bp.route('/<int:post_id>/apply', methods=['POST'])
@login_required
def apply(post_id):
    post = Post.query.get_or_404(post_id)
    form = ApplicationForm()
    
    if form.validate_on_submit():
        # Перевіряємо чи вже подана заявка
        existing_application = Application.query.filter_by(
            user_id=current_user.id,
            post_id=post.id
        ).first()
        
        if existing_application:
            flash('Ви вже подали заявку на це оголошення!', 'warning')
        else:
            application = Application(
                volunteer=current_user,
                post=post,
                message=form.message.data
            )
            db.session.add(application)
            db.session.commit()
            flash('Вашу заявку успішно надіслано!', 'success')
    
    return redirect(url_for('posts.view', post_id=post.id))

@posts_bp.route('/category/<int:category_id>')
def by_category(category_id):
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(
        category_id=category_id,
        is_active=True
    ).order_by(desc(Post.created_at)).paginate(
        page=page,
        per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    return render_template('posts/by_category.html',
                         title=f'Категорія: {category.name}',
                         category=category,
                         posts=posts.items,
                         pagination=posts)

@posts_bp.route('/image/<int:image_id>', methods=['DELETE'])
@login_required
def delete_image(image_id):
    image = Image.query.get_or_404(image_id)
    
    # Перевіряємо права доступу
    if image.post.author != current_user and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Видаляємо файл
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename))
        
        # Видаляємо запис з бази даних
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'message': 'Image deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@posts_bp.route('/<int:post_id>', methods=['DELETE'])
@login_required
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Перевіряємо права доступу
    if post.author != current_user and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Видаляємо всі зображення
        for image in post.images:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], image.filename))
            except:
                pass  # Ігноруємо помилки видалення файлів
        
        # Видаляємо пост та всі пов'язані дані
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Post deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
