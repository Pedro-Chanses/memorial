from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, FileField, MultipleFileField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import FileAllowed

class EventForm(FlaskForm):
    """Форма для створення та редагування подій"""
    title = StringField('Назва', validators=[
        DataRequired(message="Це поле обов'язкове"),
        Length(min=3, max=128, message="Назва повинна бути від 3 до 128 символів")
    ])
    
    description = TextAreaField('Опис', validators=[
        DataRequired(message="Це поле обов'язкове"),
        Length(min=10, message="Опис повинен містити щонайменше 10 символів")
    ])
    
    event_type = SelectField('Тип події', choices=[
        ('competition', 'Змагання'),
        ('seminar', 'Семінар'),
        ('training', 'Тренування'),
        ('exam', 'Атестація'),
        ('other', 'Інше')
    ], validators=[DataRequired(message="Оберіть тип події")])
    
    start_date = DateTimeField('Дата початку', 
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired(message="Вкажіть дату початку")]
    )
    
    end_date = DateTimeField('Дата завершення',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired(message="Вкажіть дату завершення")]
    )
    
    location = StringField('Місце проведення', validators=[
        DataRequired(message="Вкажіть місце проведення"),
        Length(max=128, message="Максимальна довжина - 128 символів")
    ])
    
    branch_id = SelectField('Філія', coerce=int, validators=[
        Optional()
    ])
    
    images = MultipleFileField('Зображення', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Дозволені тільки зображення')
    ])

class EventParticipationForm(FlaskForm):
    """Форма для реєстрації на подію"""
    category = StringField('Категорія', validators=[
        DataRequired(message="Вкажіть категорію участі"),
        Length(max=64, message="Максимальна довжина - 64 символи")
    ])
    
    notes = TextAreaField('Примітки', validators=[
        Optional(),
        Length(max=500, message="Максимальна довжина - 500 символів")
    ])
