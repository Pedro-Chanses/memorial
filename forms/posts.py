from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, MultipleFileField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import FileAllowed, FileSize
from datetime import datetime

class PostForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired(), Length(min=5, max=140)])
    body = TextAreaField('Опис', validators=[DataRequired(), Length(min=10)])
    location = StringField('Місце проведення', validators=[DataRequired(), Length(max=128)])
    contact_info = StringField('Контактна інформація', validators=[DataRequired(), Length(max=256)])
    start_date = DateTimeField('Дата початку', format='%d.%m.%Y %H:%M', validators=[Optional()])
    end_date = DateTimeField('Дата завершення', format='%d.%m.%Y %H:%M', validators=[Optional()])
    category = SelectField('Категорія', coerce=int, validators=[DataRequired()])
    images = MultipleFileField('Зображення', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Дозволені тільки зображення (JPG, JPEG, PNG, GIF)!'),
        FileSize(max_size=5 * 1024 * 1024, message='Максимальний розмір файлу - 5 МБ')
    ])
    submit = SubmitField('Створити проект')

    def validate_end_date(self, field):
        if field.data and self.start_date.data:
            if field.data < self.start_date.data:
                raise ValidationError('Дата завершення не може бути раніше дати початку')

    def validate_images(self, field):
        if field.data:
            if len(field.data) > 5:
                raise ValidationError('Можна завантажити максимум 5 зображень')
            
            for file in field.data:
                if file.content_length and file.content_length > 5 * 1024 * 1024:
                    raise ValidationError(f'Файл {file.filename} перевищує максимальний розмір 5 МБ')

class ApplicationForm(FlaskForm):
    message = TextAreaField('Повідомлення', validators=[
        DataRequired(),
        Length(min=10, max=500, message='Повідомлення повинно містити від 10 до 500 символів')
    ])
    submit = SubmitField('Відправити заявку')
