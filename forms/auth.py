from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запам\'ятати мене')
    submit = SubmitField('Увійти')

class RegisterForm(FlaskForm):
    name = StringField('Повне ім\'я', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Ім\'я повинно бути від 2 до 100 символів')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Будь ласка, введіть коректний email')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(),
        Length(min=6, message='Пароль повинен бути не менше 6 символів')
    ])
    password2 = PasswordField(
        'Повторіть пароль',
        validators=[
            DataRequired(),
            EqualTo('password', message='Паролі повинні співпадати')
        ]
    )
    submit = SubmitField('Зареєструватися')
