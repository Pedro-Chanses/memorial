from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class ContactForm(FlaskForm):
    name = StringField('Ваше ім\'я', validators=[
        DataRequired(message='Це поле обов\'язкове'),
        Length(min=2, max=100, message='Ім\'я повинно бути від 2 до 100 символів')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Це поле обов\'язкове'),
        Email(message='Введіть коректну email адресу')
    ])
    
    subject = StringField('Тема', validators=[
        DataRequired(message='Це поле обов\'язкове'),
        Length(min=2, max=200, message='Тема повинна бути від 2 до 200 символів')
    ])
    
    message = TextAreaField('Повідомлення', validators=[
        DataRequired(message='Це поле обов\'язкове'),
        Length(min=10, message='Повідомлення повинно містити щонайменше 10 символів')
    ])
    
    submit = SubmitField('Надіслати')
