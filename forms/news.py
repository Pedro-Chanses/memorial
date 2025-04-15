from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, MultipleFileField, FileField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import FileAllowed

class NewsForm(FlaskForm):
    """Форма для створення та редагування новин"""
    title = StringField('Заголовок', validators=[
        DataRequired(message="Це поле обов'язкове"),
        Length(min=3, max=200, message="Довжина заголовку має бути від 3 до 200 символів")
    ])
    
    content = TextAreaField('Зміст', validators=[
        DataRequired(message="Це поле обов'язкове"),
        Length(min=10, message="Мінімальна довжина - 10 символів")
    ])
    
    category = SelectField('Категорія', choices=[
        ('announcement', 'Анонс'),
        ('news', 'Новина'),
        ('article', 'Стаття'),
        ('achievement', 'Досягнення'),
        ('other', 'Інше')
    ], validators=[DataRequired(message="Оберіть категорію")])
    
    main_image = FileField('Головне зображення', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Дозволені тільки зображення')
    ])
    
    gallery_images = MultipleFileField('Галерея зображень', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Дозволені тільки зображення')
    ])
    
    summary = TextAreaField('Короткий опис', validators=[
        Optional(),
        Length(max=500, message="Максимальна довжина - 500 символів")
    ])
    
    is_published = SelectField('Статус', choices=[
        ('1', 'Опублікувати'),
        ('0', 'Зберегти як чернетку')
    ], validators=[DataRequired()], default='1')
