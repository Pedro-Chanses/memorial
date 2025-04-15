from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, MultipleFileField, FileField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import FileAllowed

class OwnWorkForm(FlaskForm):
    """Форма для створення та редагування власних робіт"""
    title = StringField('Заголовок', validators=[
        Optional(),
        Length(max=200, message="Максимальна довжина заголовку - 200 символів")
    ])
    
    content = TextAreaField('Опис роботи', validators=[
        Optional()
    ])
    
    category = SelectField('Категорія', choices=[
        ('monument', 'Пам\'ятник'),
        ('sculpture', 'Скульптура'),
        ('memorial', 'Меморіал'),
        ('tombstone', 'Надгробок'),
        ('other', 'Інше')
    ], validators=[Optional()], default='monument')
    
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
