from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import current_user, login_required
from flask_mail import Message
from models import db, News, User, Image, Monument
from forms.contact import ContactForm
from datetime import datetime
from sqlalchemy import func
import logging

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Отримуємо останні новини
    latest_news = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).limit(3).all()
    
    # Події та філії видалені
    upcoming_events = []
    branches = []
    
    # Отримуємо популярні пам'ятники
    # Спочатку намагаємося отримати популярні пам'ятники
    popular_monuments = Monument.query.filter_by(is_active=True, is_popular=True).order_by(func.random()).limit(3).all()
    
    # Якщо немає популярних пам'ятників, отримуємо будь-які активні пам'ятники
    if not popular_monuments:
        popular_monuments = Monument.query.filter_by(is_active=True).order_by(func.random()).limit(3).all()
    
    # Збираємо статистику пам'ятників
    stats = {
        'monuments': Monument.query.filter_by(is_active=True).count(),
        'users': User.query.filter_by(is_active=True).count(),
        'years': datetime.now().year - 2020,  # Припустимо, компанія заснована в 2020
        'categories': len(set([m.category for m in Monument.query.with_entities(Monument.category).distinct().all() if m.category]))
    }
    
    return render_template('main/index.html',
                         title='Головна',
                         latest_news=latest_news,
                         upcoming_events=upcoming_events,
                         branches=branches,
                         popular_monuments=popular_monuments,
                         stats=stats)


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    from utils.gmail_oauth import get_gmail_service, create_message
    
    form = ContactForm()
    if form.validate_on_submit():
        try:
            # Отримуємо Gmail сервіс
            service = get_gmail_service()
            if not service:
                # Якщо немає авторизації, перенаправляємо на сторінку авторизації Google
                return redirect(url_for('auth.authorize'))
            
            # Створюємо повідомлення
            message = create_message(
                sender='me',  # 'me' означає авторизований email
                to=current_app.config['GOOGLE_EMAIL'],
                subject=f'Нове повідомлення: {form.subject.data}',
                message_text=f"""
                Від: {form.name.data} ({form.email.data})
                Телефон: {form.phone.data}
                
                {form.message.data}
                """
            )
            
            # Відправляємо повідомлення
            service.users().messages().send(userId='me', body=message).execute()
            
            flash('Ваше повідомлення успішно надіслано!', 'success')
            return redirect(url_for('main.contact'))
            
        except Exception as e:
            current_app.logger.error(f'Помилка відправки повідомлення: {str(e)}')
            flash('На жаль, сталася помилка при відправці повідомлення. Будь ласка, спробуйте пізніше.', 'danger')
    
    return render_template('main/contact.html', title='Контакти', form=form)

@main_bp.route('/gallery')
def gallery():
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')
    
    # Базовий запит
    query = Image.query.filter_by(is_gallery=True)
    
    # Сортування
    if sort == 'oldest':
        query = query.order_by(Image.created_at.asc())
    elif sort == 'popular':
        query = query.order_by(Image.views.desc())
    else:  # newest
        query = query.order_by(Image.created_at.desc())
    
    # Пагінація
    images = query.paginate(page=page, per_page=12, error_out=False)
    
    return render_template('main/gallery.html',
                         title='Галерея',
                         images=images)

@main_bp.route('/support')
def support():
    return render_template('main/support.html', title='Підтримати проект')

@main_bp.route('/help')
def help():
    return render_template('main/help.html', title='Допомога')

@main_bp.route('/privacy')
def privacy():
    return render_template('main/privacy.html', title='Політика конфіденційності')

@main_bp.route('/catalog')
def catalog():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', None)
    sort = request.args.get('sort', 'newest')
    
    # Базовий запит
    query = Monument.query.filter_by(is_active=True)
    
    # Фільтрація за категорією
    if category:
        query = query.filter_by(category=category)
    
    # Сортування
    if sort == 'price_asc':
        query = query.order_by(Monument.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Monument.price.desc())
    elif sort == 'oldest':
        query = query.order_by(Monument.created_at.asc())
    else:  # newest
        query = query.order_by(Monument.created_at.desc())
    
    # Пагінація
    monuments = query.paginate(page=page, per_page=12, error_out=False)
    
    # Отримуємо всі категорії для фільтра
    categories = db.session.query(Monument.category).filter(Monument.category != None, Monument.is_active == True).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('main/catalog.html',
                         title='Каталог пам\'ятників',
                         monuments=monuments,
                         categories=categories,
                         current_category=category,
                         current_sort=sort)

@main_bp.route('/monuments')
def monuments():
    """Сторінка з усіма пам'ятниками"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Отримуємо всі активні пам'ятники з пагінацією
    # Отримуємо всі активні пам'ятники
    monuments_query = Monument.query.filter_by(is_active=True)
    
    # Фільтрація за пошуком
    search_query = request.args.get('q')
    if search_query:
        monuments_query = monuments_query.filter(
            (Monument.name.ilike(f'%{search_query}%')) | 
            (Monument.article.ilike(f'%{search_query}%')) |
            (Monument.description.ilike(f'%{search_query}%'))
        )
    
    # Сортування
    sort = request.args.get('sort', 'display_order')
    if sort == 'price_asc':
        monuments_query = monuments_query.order_by(Monument.price.asc())
    elif sort == 'price_desc':
        monuments_query = monuments_query.order_by(Monument.price.desc())
    elif sort == 'newest':
        monuments_query = monuments_query.order_by(Monument.created_at.desc())
    elif sort == 'popular':
        monuments_query = monuments_query.order_by(Monument.views_count.desc())
    else:  # За замовчуванням - за порядком відображення
        monuments_query = monuments_query.order_by(Monument.display_order.desc())
    
    # Пагінація
    monuments_pagination = monuments_query.paginate(page=page, per_page=per_page)
    
    return render_template('main/monuments.html',
                         title='Каталог пам\'ятників',
                         monuments=monuments_pagination,
                         search_query=search_query,
                         sort=sort)

@main_bp.route('/monuments/category/<category>')
def monuments_category(category):
    """Сторінка з пам'ятниками певної категорії"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Отримуємо всі активні пам'ятники з вказаної категорії з пагінацією
    # Отримуємо всі активні пам'ятники з вказаної категорії
    monuments_query = Monument.query.filter_by(is_active=True, category=f'/{category}')
    
    # Фільтрація за пошуком
    search_query = request.args.get('q')
    if search_query:
        monuments_query = monuments_query.filter(
            (Monument.name.ilike(f'%{search_query}%')) | 
            (Monument.article.ilike(f'%{search_query}%')) |
            (Monument.description.ilike(f'%{search_query}%'))
        )
    
    # Сортування
    sort = request.args.get('sort', 'display_order')
    if sort == 'price_asc':
        monuments_query = monuments_query.order_by(Monument.price.asc())
    elif sort == 'price_desc':
        monuments_query = monuments_query.order_by(Monument.price.desc())
    elif sort == 'newest':
        monuments_query = monuments_query.order_by(Monument.created_at.desc())
    elif sort == 'popular':
        monuments_query = monuments_query.order_by(Monument.views_count.desc())
    else:  # За замовчуванням - за порядком відображення
        monuments_query = monuments_query.order_by(Monument.display_order.desc())
    
    # Отримуємо назву категорії
    category_names = {
        'odinarni-kombinovani': 'Одинарні комбіновані',
        'odinarni-prosti': 'Одинарні прості',
        'dityachi-pamyatniki': 'Дитячі пам\'ятники',
        'evropeyski-pamyatniki': 'Європейські пам\'ятники',
        'pamyatniki-dlya-viyskovikh': 'Пам\'ятники для військових',
        'podviyni-pamyatniki': 'Подвійні пам\'ятники',
        'suputni-tovari': 'Аксесуари',
        'khresti': 'Хрести'
    }
    category_name = category_names.get(category, 'Пам\'ятники')
    
    # Пагінація
    monuments_pagination = monuments_query.paginate(page=page, per_page=per_page)
    
    return render_template('main/monuments_category.html',
                         title=f'Категорія: {category_name}',
                         category_name=category_name,
                         category=category,
                         monuments=monuments_pagination,
                         search_query=search_query,
                         sort=sort)

@main_bp.route('/catalog/<int:monument_id>')
def monument_detail(monument_id):
    """Сторінка деталей пам'ятника"""
    # Отримуємо пам'ятник за ID
    monument = Monument.query.get_or_404(monument_id)
    
    # Збільшуємо лічильник переглядів
    monument.views_count = (monument.views_count or 0) + 1
    db.session.commit()
    
    # Отримуємо схожі пам'ятники
    similar_monuments = Monument.query.filter(
        Monument.id != monument.id,
        Monument.is_active == True,
        Monument.category == monument.category
    ).order_by(func.random()).limit(4).all()
    
    # Отримуємо пов'язані пам'ятники, якщо вони вказані
    related_products = {}
    if monument.related_products:
        # Перевіряємо, чи related_products є рядком або списком
        if isinstance(monument.related_products, str):
            related_ids = [int(id.strip()) for id in monument.related_products.split(',') if id.strip().isdigit()]
        else:
            related_ids = monument.related_products
            
        if related_ids:
            # Отримуємо пов'язані пам'ятники
            related_monuments = Monument.query.filter(
                Monument.id.in_(related_ids),
                Monument.is_active == True
            ).all()
            
            # Створюємо словник з пов'язаними товарами
            for related in related_monuments:
                related_products[related.id] = related
    
    return render_template('main/monument_detail.html',
                         title=monument.seo_title or f'Пам\'ятник {monument.name}',
                         monument=monument,
                         similar_monuments=similar_monuments,
                         related_products=related_products)



