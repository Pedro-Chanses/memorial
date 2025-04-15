from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Event, EventParticipant, Branch, Image
from forms.events import EventForm, EventParticipationForm
import os
from datetime import datetime
from sqlalchemy import desc
from PIL import Image as PILImage
import uuid

events_bp = Blueprint('events', __name__)

def save_image(file, event_id):
    """Зберігає завантажене зображення"""
    if not file:
        return None
        
    filename = secure_filename(file.filename)
    # Генеруємо унікальне ім'я файлу
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'events', unique_filename)
    
    # Створюємо директорію, якщо її немає
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Зберігаємо та оптимізуємо зображення
    img = PILImage.open(file)
    img.thumbnail((1200, 1200))  # Максимальний розмір
    img.save(file_path, optimize=True, quality=85)
    
    # Створюємо запис в базі даних
    image = Image(
        filename=unique_filename,
        event_id=event_id
    )
    db.session.add(image)
    return image

@events_bp.route('/')
def index():
    """Список всіх подій"""
    page = request.args.get('page', 1, type=int)
    type_filter = request.args.get('type')
    branch_filter = request.args.get('branch', type=int)
    
    # Базовий запит
    query = Event.query.filter_by(is_active=True)
    
    # Застосовуємо фільтри
    if type_filter:
        query = query.filter_by(event_type=type_filter)
    if branch_filter:
        query = query.filter_by(branch_id=branch_filter)
    
    # Отримуємо події з пагінацією
    events = query.order_by(Event.start_date.desc()).paginate(
        page=page,
        per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    
    # Отримуємо всі філії для фільтра
    branches = Branch.query.filter_by(is_active=True).all()
    
    return render_template('events/index.html',
                         title='Події',
                         events=events,
                         branches=branches,
                         current_type=type_filter,
                         current_branch=branch_filter)

@events_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Створення нової події"""
    if not current_user.is_admin and not current_user.is_coach:
        flash('У вас немає прав для створення подій', 'error')
        return redirect(url_for('events.index'))
    
    form = EventForm()
    
    # Заповнюємо список філій
    branches = Branch.query.filter_by(is_active=True).all()
    form.branch_id.choices = [(0, 'Оберіть філію')] + [(b.id, b.name) for b in branches]
    
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            event_type=form.event_type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            location=form.location.data,
            branch_id=form.branch_id.data if form.branch_id.data != 0 else None,
            organizer_id=current_user.id
        )
        db.session.add(event)
        db.session.commit()
        
        # Зберігаємо зображення
        if form.images.data:
            for file in form.images.data:
                if file:
                    save_image(file, event.id)
            db.session.commit()
        
        flash('Подію успішно створено!', 'success')
        return redirect(url_for('events.view', event_id=event.id))
    
    return render_template('events/create.html',
                         title='Створення події',
                         form=form)

@events_bp.route('/<int:event_id>')
def view(event_id):
    """Перегляд події"""
    event = Event.query.get_or_404(event_id)
    
    # Перевіряємо чи користувач вже зареєстрований
    user_registered = False
    if current_user.is_authenticated:
        user_registered = EventParticipant.query.filter_by(
            event_id=event.id,
            user_id=current_user.id
        ).first() is not None
    
    return render_template('events/view.html',
                         title=event.title,
                         event=event,
                         user_registered=user_registered)

@events_bp.route('/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(event_id):
    """Редагування події"""
    event = Event.query.get_or_404(event_id)
    
    # Перевірка прав
    if not current_user.is_admin and event.organizer_id != current_user.id:
        flash('У вас немає прав для редагування цієї події', 'error')
        return redirect(url_for('events.view', event_id=event.id))
    
    form = EventForm(obj=event)
    
    # Заповнюємо список філій
    branches = Branch.query.filter_by(is_active=True).all()
    form.branch_id.choices = [(0, 'Оберіть філію')] + [(b.id, b.name) for b in branches]
    
    if form.validate_on_submit():
        event.title = form.title.data
        event.description = form.description.data
        event.event_type = form.event_type.data
        event.start_date = form.start_date.data
        event.end_date = form.end_date.data
        event.location = form.location.data
        event.branch_id = form.branch_id.data if form.branch_id.data != 0 else None
        
        # Зберігаємо нові зображення
        if form.images.data:
            for file in form.images.data:
                if file:
                    save_image(file, event.id)
        
        db.session.commit()
        flash('Подію успішно оновлено!', 'success')
        return redirect(url_for('events.view', event_id=event.id))
    
    return render_template('events/edit.html',
                         title=f'Редагування події: {event.title}',
                         form=form,
                         event=event)

@events_bp.route('/<int:event_id>/register', methods=['GET', 'POST'])
@login_required
def register(event_id):
    """Реєстрація на подію"""
    event = Event.query.get_or_404(event_id)
    
    # Перевіряємо чи не пізно реєструватися
    if event.start_date < datetime.utcnow():
        flash('Реєстрація на цю подію вже закрита', 'error')
        return redirect(url_for('events.view', event_id=event.id))
    
    # Перевіряємо чи користувач вже зареєстрований
    if EventParticipant.query.filter_by(
        event_id=event.id,
        user_id=current_user.id
    ).first():
        flash('Ви вже зареєстровані на цю подію', 'info')
        return redirect(url_for('events.view', event_id=event.id))
    
    form = EventParticipationForm()
    
    if form.validate_on_submit():
        participant = EventParticipant(
            event_id=event.id,
            user_id=current_user.id,
            category=form.category.data,
            status='registered'
        )
        db.session.add(participant)
        db.session.commit()
        
        flash('Ви успішно зареєструвалися на подію!', 'success')
        return redirect(url_for('events.view', event_id=event.id))
    
    return render_template('events/register.html',
                         title=f'Реєстрація на подію: {event.title}',
                         form=form,
                         event=event)

@events_bp.route('/<int:event_id>/delete', methods=['POST'])
@login_required
def delete(event_id):
    """Видалення події"""
    event = Event.query.get_or_404(event_id)
    
    # Перевірка прав
    if not current_user.is_admin and event.organizer_id != current_user.id:
        flash('У вас немає прав для видалення цієї події', 'error')
        return redirect(url_for('events.view', event_id=event.id))
    
    # Видаляємо зображення
    for image in event.images:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'events', image.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.session.delete(event)
    db.session.commit()
    
    flash('Подію успішно видалено!', 'success')
    return redirect(url_for('events.index'))
