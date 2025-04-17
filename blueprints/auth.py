from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from forms.auth import LoginForm, RegisterForm
from extensions import db
from utils.gmail_oauth import create_oauth_flow, get_google_user_info
import functools
import json

auth_bp = Blueprint('auth', __name__)

def no_cache(view):
    @functools.wraps(view)
    def no_cache_impl(*args, **kwargs):
        response = current_app.make_response(view(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    return no_cache_impl

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'GET':
        next_url = request.args.get('next')
        if next_url:
            session['next_url'] = next_url
            
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_url = session.pop('next_url', None)
            flash(f'Ласкаво просимо, {user.first_name}!', 'success')
            return redirect(next_url or url_for('main.index'))
        flash('Невірний email або пароль', 'danger')
    return render_template('auth/login.html', title='Вхід', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Цей email вже зареєстрований', 'danger')
            return render_template('auth/register.html', title='Реєстрація', form=form)
        
        # Створюємо username з email
        username = form.email.data.split('@')[0]
        
        user = User(
            username=username,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        # Розділяємо повне ім'я на first_name та last_name
        name_parts = form.name.data.split()
        user.first_name = name_parts[0]
        user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        
        db.session.add(user)
        db.session.commit()
        
        flash('Ви успішно зареєструвалися! Тепер можете увійти.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Реєстрація', form=form)

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    # Перевіряємо, чи це не помилковий виклик після редагування пам'ятника
    if request.referrer and ('/admin/monuments/' in request.referrer or '/admin/monuments' in request.referrer):
        print(f"\n!!! LOGOUT CALLED FROM MONUMENTS PAGE OR EDIT PAGE !!!")
        print(f"Referrer: {request.referrer}")
        print(f"Preventing logout and redirecting back to /admin/monuments")
        
        # Зберігаємо ідентифікатор адміністратора в сесії
        if current_user.is_authenticated and current_user.is_admin:
            session['admin_id'] = current_user.id
            session['admin_username'] = current_user.username
            session.permanent = True
            print(f"Збережено дані адміністратора в сесії: {session}")
        
        flash('Помилка при редагуванні пам\'ятника. Спробуйте ще раз.', 'error')
        return redirect('/admin/monuments')
    
    # Перевіряємо, чи це не автоматичний виклик виходу з системи
    if request.method == 'GET' and not request.args.get('confirmed') and not request.referrer:
        print("\n!!! AUTOMATIC LOGOUT DETECTED !!!")
        print("Preventing automatic logout and redirecting to admin panel")
        
        # Зберігаємо ідентифікатор адміністратора в сесії
        if current_user.is_authenticated and current_user.is_admin:
            session['admin_id'] = current_user.id
            session['admin_username'] = current_user.username
            session.permanent = True
            print(f"Збережено дані адміністратора в сесії: {session}")
            return redirect('/admin')
        
    print("\nPerforming normal logout procedure...")
    # Спочатку зберігаємо інформацію про користувача для логування
    user_info = {
        'username': current_user.username if current_user.is_authenticated else 'Not authenticated',
        'id': current_user.id if current_user.is_authenticated else None,
        'is_admin': current_user.is_admin if current_user.is_authenticated else False
    }
    
    # Потім виходимо з системи
    logout_user()
    
    # Очищуємо сесію після виходу з системи
    # Спеціально зберігаємо список ключів, щоб уникнути помилки зміни розміру під час ітерації
    session_keys = list(session.keys())
    for key in session_keys:
        session.pop(key, None)
    
    # Видаляємо cookie для сесії
    for cookie in request.cookies:
        if cookie.startswith('session') or cookie.startswith('remember_token') or cookie.startswith('google_'):
            response = redirect(url_for('main.index'))
            response.delete_cookie(cookie)
    
    # Очищаємо всю сесію
    session.clear()
    flash('Ви успішно вийшли з системи.', 'success')
    
    # Створюємо відповідь з видаленням cookie
    response = redirect(url_for('main.index'))
    response.delete_cookie('session')
    response.delete_cookie('remember_token')
    
    # Видаляємо всі можливі Google cookie
    for cookie_name in ['google_oauth', 'google_auth', 'google_token', 'credentials']:
        response.delete_cookie(cookie_name)
    
    return response

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', title='Профіль')

@auth_bp.route('/authorize')
def authorize():
    """Початок процесу авторизації через Google"""
    # Визначаємо, чи це для Gmail API чи для звичайної авторизації
    for_gmail = request.args.get('for_gmail', 'false').lower() == 'true'
    
    # Створюємо flow з правильним redirect_uri
    flow = create_oauth_flow(for_gmail=for_gmail)
    
    # Логуємо, який redirect_uri використовується (для діагностики)
    current_app.logger.info(f"OAUTH DEBUG - Using redirect_uri: {flow.redirect_uri}")
    print(f"OAUTH DEBUG - Using redirect_uri: {flow.redirect_uri}")
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    session['state'] = state
    session['for_gmail'] = for_gmail
    return redirect(authorization_url)

@auth_bp.route('/oauth2callback')
@no_cache
def oauth2callback():
    """Обробка відповіді від Google"""
    try:
        # Отримуємо стан сесії
        state = session.get('state')
        for_gmail = session.pop('for_gmail', False)
        
        # Створюємо flow
        flow = create_oauth_flow(for_gmail=for_gmail)
        
        # Отримуємо токен
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        
        if not for_gmail:  # Якщо це звичайна авторизація
            # Отримуємо інформацію про користувача
            user_info = get_google_user_info(credentials)
            if not user_info:
                flash('Помилка отримання даних користувача', 'danger')
                return redirect(url_for('auth.login'))
                
            # Виводимо отриману інформацію для налагодження
            current_app.logger.info(f"Google user info: {user_info}")
            
            # Перевіряємо чи користувач вже існує
            user = User.query.filter_by(email=user_info['email']).first()
            if not user:
                # Створюємо нового користувача
                username = user_info['email'].split('@')[0]  # Створюємо username з email
                # Розділяємо повне ім'я на first_name та last_name
                full_name = user_info.get('name', '').split(' ', 1)
                first_name = full_name[0] if full_name else username
                last_name = full_name[1] if len(full_name) > 1 else ''
                
                # Перевіряємо чи email в списку адмінів
                admin_emails = current_app.config.get('ADMIN_EMAILS', [])
                is_admin = user_info['email'] in admin_emails
                
                user = User(
                    username=username,
                    email=user_info['email'],
                    password_hash=generate_password_hash('google-oauth2'),
                    avatar_url=user_info.get('picture'),
                    first_name=first_name,
                    last_name=last_name,
                    is_admin=is_admin,  # Встановлюємо права адміна
                    is_active=True
                )
                
                db.session.add(user)
                db.session.commit()
            else:
                # Оновлюємо існуючого користувача
                if 'name' in user_info:
                    # Розділяємо повне ім'я на first_name та last_name
                    full_name = user_info['name'].split(' ', 1)
                    user.first_name = full_name[0] if full_name else user.username
                    user.last_name = full_name[1] if len(full_name) > 1 else ''
                if 'picture' in user_info:
                    user.avatar_url = user_info['picture']
                    
                # Перевіряємо чи email в списку адмінів
                admin_emails = current_app.config.get('ADMIN_EMAILS', [])
                user.is_admin = user_info['email'] in admin_emails
                
                db.session.commit()
            
            # Логінимо користувача
            login_user(user, remember=True)
            
            # Перевіряємо статус адміністратора
            user.check_admin_status()
            
            flash('Ви успішно увійшли через Google!', 'success')
            
            # Перенаправляємо на головну сторінку
            return redirect(url_for('main.index'))
        
        # Зберігаємо облікові дані для Gmail API
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        return redirect(url_for('main.contact'))
        
    except Exception as e:
        current_app.logger.error(f"OAuth callback error: {str(e)}")
        flash(f'Помилка авторизації: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))
