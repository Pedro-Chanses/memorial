from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user

# Створюємо Blueprint для подій
events_bp = Blueprint('events', __name__)

# Заглушка для головної сторінки подій
@events_bp.route('/')
def index():
    return render_template('events/index.html', events=[])

# Заглушка для деталей події
@events_bp.route('/<int:event_id>')
def event_details(event_id):
    return render_template('events/event_details.html', event=None)

# Заглушка для створення події
@events_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_event():
    flash('Функціонал подій тимчасово недоступний', 'warning')
    return redirect(url_for('main.index'))

# Заглушка для редагування події
@events_bp.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    flash('Функціонал подій тимчасово недоступний', 'warning')
    return redirect(url_for('main.index'))

# Заглушка для видалення події
@events_bp.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    flash('Функціонал подій тимчасово недоступний', 'warning')
    return redirect(url_for('main.index'))

# Заглушка для реєстрації на подію
@events_bp.route('/register/<int:event_id>', methods=['GET', 'POST'])
@login_required
def register_for_event(event_id):
    flash('Функціонал подій тимчасово недоступний', 'warning')
    return redirect(url_for('main.index'))
