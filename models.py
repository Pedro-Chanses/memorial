from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from flask import current_app
from sqlalchemy.ext.hybrid import hybrid_property

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    avatar_url = db.Column(db.String(255))
    news_posts = db.relationship('News', backref='author', lazy='dynamic',
                              foreign_keys='News.author_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def name(self):
        """Повертає повне ім'я користувача"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username

    def check_admin_status(self):
        """Перевіряє чи користувач має бути адміністратором"""
        admin_emails = current_app.config.get('ADMIN_EMAILS', [])
        if self.email in admin_emails and not self.is_admin:
            self.is_admin = True
            db.session.commit()
        return self.is_admin

class News(db.Model):
    """Модель новин"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category = db.Column(db.String(32), default='news')  # Категорія новини
    images = db.relationship('Image', backref='news', lazy='dynamic',
                           foreign_keys='Image.news_id')
    
    @property
    def image_url(self):
        """Повертає URL першого зображення новини"""
        first_image = self.images.first()
        if first_image:
            if first_image.cloudinary_public_id:
                url = first_image.filename  # В filename зберігається повний URL з Cloudinary
                # Переконуємося, що URL використовує HTTPS
                if url and url.startswith('http:'):
                    url = url.replace('http:', 'https:')
                return url
            return first_image.filename
        return None
    
    @property
    def thumbnail_url(self):
        """Повертає URL мініатюри першого зображення новини"""
        first_image = self.images.first()
        if first_image:
            if first_image.cloudinary_public_id:
                url = first_image.thumbnail  # В thumbnail зберігається URL мініатюри з Cloudinary
                # Переконуємося, що URL використовує HTTPS
                if url and url.startswith('http:'):
                    url = url.replace('http:', 'https:')
                return url
            return first_image.thumbnail
        return None
    
    def __repr__(self):
        return f'<News {self.title}>'

class Image(db.Model):
    """Модель зображень"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # URL оригінального зображення
    thumbnail = db.Column(db.String(255), nullable=True)  # URL мініатюри (опціонально)
    cloudinary_public_id = db.Column(db.String(255))  # ID зображення в Cloudinary
    is_news = db.Column(db.Boolean, default=False)
    is_gallery = db.Column(db.Boolean, default=False)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id', ondelete='CASCADE'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    views = db.Column(db.Integer, default=0)
    
    @property
    def image_url(self):
        """Повертає URL зображення"""
        if self.cloudinary_public_id:
            url = self.filename  # В filename зберігається повний URL з Cloudinary
            # Переконуємося, що URL використовує HTTPS
            if url and url.startswith('http:'):
                url = url.replace('http:', 'https:')
            return url
        return self.filename
    
    @property
    def thumbnail_url(self):
        """Повертає URL мініатюри зображення"""
        if self.cloudinary_public_id:
            url = self.thumbnail  # В thumbnail зберігається URL мініатюри з Cloudinary
            # Переконуємося, що URL використовує HTTPS
            if url and url.startswith('http:'):
                url = url.replace('http:', 'https:')
            return url
        return self.thumbnail

class Category(db.Model):
    """Модель категорій для галереї та новин"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(32))  # 'gallery' або 'news'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Notification(db.Model):
    """Модель сповіщень"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(128), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(20))

class Monument(db.Model):
    """Модель пам'ятників"""
    __tablename__ = 'monument'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    article = db.Column(db.String(20), unique=True, index=True)  # Артикул пам'ятника
    price = db.Column(db.Integer)
    description = db.Column(db.Text)
    category = db.Column(db.String(64))
    main_image = db.Column(db.String(255))  # Шлях до головного зображення
    original_link = db.Column(db.String(255))  # Оригінальне посилання
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Додаткові поля для пам'ятників
    dimensions = db.Column(db.String(128))  # Розміри
    material = db.Column(db.String(128))  # Матеріал
    color = db.Column(db.String(64))  # Колір
    weight = db.Column(db.Float)  # Вага
    availability = db.Column(db.String(64))  # Наявність
    production_time = db.Column(db.String(64))  # Час виготовлення
    
    # Поля для знижок та акцій
    is_popular = db.Column(db.Boolean, default=False)  # Популярний товар
    discount_percent = db.Column(db.Integer)  # Відсоток знижки
    old_price = db.Column(db.Integer)  # Стара ціна
    
    # SEO поля
    seo_title = db.Column(db.String(255))
    seo_description = db.Column(db.Text)
    seo_keywords = db.Column(db.String(255))
    
    # Додаткові характеристики
    style = db.Column(db.String(128))  # Стиль
    warranty = db.Column(db.String(64))  # Гарантія
    installation_included = db.Column(db.Boolean, default=False)  # Чи включена установка
    delivery_info = db.Column(db.Text)  # Інформація про доставку
    
    # Статистика
    views_count = db.Column(db.Integer, default=0)
    orders_count = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float)
    
    # Додаткові опції
    is_new = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer)
    related_products = db.Column(db.String(255))  # Список ID пов'язаних продуктів
    custom_fields = db.Column(db.JSON)  # Додаткові поля у форматі JSON
    
    # Зображення пам'ятника
    images = db.relationship('MonumentImage', backref='monument', lazy='dynamic',
                           cascade='all, delete-orphan')
    
    @hybrid_property
    def formatted_price(self):
        """Повертає ціну у форматованому вигляді"""
        if self.price:
            return f"{self.price:,} грн".replace(',', ' ')
        return "Ціна за запитом"
    
    @hybrid_property
    def formatted_old_price(self):
        """Повертає стару ціну у форматованому вигляді"""
        if self.old_price:
            return f"{self.old_price:,} грн".replace(',', ' ')
        return ""
    
    @hybrid_property
    def has_discount(self):
        """Перевіряє, чи є знижка на пам'ятник"""
        return bool(self.discount_percent and self.old_price)
    
    @hybrid_property
    def category_name(self):
        """Повертає назву категорії у зручному вигляді"""
        category_names = {
            '/odinarni-kombinovani': 'Одинарні комбіновані',
            '/dityachi-pamyatniki': 'Дитячі пам\'ятники',
            '/evropeyski-pamyatniki': 'Європейські пам\'ятники',
            '/odinarni-prosti': 'Одинарні прості',
            '/pamyatniki-dlya-viyskovikh': 'Пам\'ятники для військових',
            '/podviyni-pamyatniki': 'Подвійні пам\'ятники',
            '/suputni-tovari': 'Аксесуари',
            '/khresti': 'Хрести',
            '/index': 'Загальна категорія',
        }
        return category_names.get(self.category, self.category)
    
    def get_similar_monuments(self, limit=4):
        """Отримує схожі пам'ятники з тієї ж категорії"""
        return Monument.query.filter(
            Monument.category == self.category,
            Monument.id != self.id,
            Monument.is_active == True
        ).order_by(db.func.random()).limit(limit).all()
    
    def __repr__(self):
        return f'<Monument {self.name}>'

class MonumentImage(db.Model):
    """Модель зображень пам'ятників"""
    id = db.Column(db.Integer, primary_key=True)
    monument_id = db.Column(db.Integer, db.ForeignKey('monument.id', ondelete='CASCADE'))
    filename = db.Column(db.String(255), nullable=False)  # Шлях до файлу
    is_main = db.Column(db.Boolean, default=False)  # Чи є головним зображенням
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MonumentImage {self.filename}>'
