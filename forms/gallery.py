from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, MultipleFileField, SelectField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import FileAllowed

class ImageUploadForm(FlaskForm):
    """Форма для завантаження зображень"""
    images = MultipleFileField('Зображення', validators=[
        DataRequired(message="Оберіть хоча б одне зображення"),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Дозволені тільки зображення')
    ])
    
    description = TextAreaField('Опис', validators=[
        Optional(),
        Length(max=500, message="Максимальна довжина - 500 символів")
    ])
    
    category = SelectField('Категорія', choices=[
        ('training', 'Тренування'),
        ('competition', 'Змагання'),
        ('seminar', 'Семінари'),
        ('events', 'Події'),
        ('other', 'Інше')
    ], validators=[DataRequired(message="Оберіть категорію")])

class ImageEditForm(FlaskForm):
    """Форма для редагування інформації про зображення"""
    description = TextAreaField('Опис', validators=[
        Optional(),
        Length(max=500, message="Максимальна довжина - 500 символів")
    ])
    
    category = SelectField('Категорія', choices=[
        ('training', 'Тренування'),
        ('competition', 'Змагання'),
        ('seminar', 'Семінари'),
        ('events', 'Події'),
        ('other', 'Інше')
    ], validators=[DataRequired(message="Оберіть категорію")])
