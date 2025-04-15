from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
import io
from datetime import datetime
from functools import wraps

from models import db
from blueprints.admin import admin_required
from excel_utils import export_monuments_to_excel, import_monuments_from_excel

excel_bp = Blueprint('excel', __name__, url_prefix='/admin/excel')

@excel_bp.route('/')
@login_required
@admin_required
def index():
    """Сторінка імпорту/експорту Excel"""
    return render_template('admin/excel.html', title='Імпорт/Експорт Excel')

@excel_bp.route('/export')
@login_required
@admin_required
def export_monuments():
    """Експортує пам'ятники в Excel файл"""
    try:
        # Генеруємо Excel файл
        output = export_monuments_to_excel()
        
        # Створюємо ім'я файлу з датою
        filename = f"monuments_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Відправляємо файл користувачу
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        current_app.logger.error(f"Помилка експорту в Excel: {str(e)}")
        flash(f'Помилка експорту: {str(e)}', 'error')
        return redirect(url_for('excel.index'))

@excel_bp.route('/import', methods=['POST'])
@login_required
@admin_required
def import_monuments():
    """Імпортує пам'ятники з Excel файлу"""
    if 'excel_file' not in request.files:
        flash('Файл не вибрано', 'error')
        return redirect(url_for('excel.index'))
    
    file = request.files['excel_file']
    
    if file.filename == '':
        flash('Файл не вибрано', 'error')
        return redirect(url_for('excel.index'))
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('Дозволені тільки файли Excel (.xlsx, .xls)', 'error')
        return redirect(url_for('excel.index'))
    
    try:
        # Імпортуємо дані з Excel
        success, result = import_monuments_from_excel(file)
        
        if success:
            flash(f'Імпорт завершено успішно. Створено: {result["created"]}, Оновлено: {result["updated"]}, Помилок: {result["errors"]}', 'success')
            
            # Якщо є помилки, виводимо їх
            if result["errors"] > 0 and "error_messages" in result:
                for error in result["error_messages"][:10]:  # Показуємо перші 10 помилок
                    flash(error, 'warning')
                
                if len(result["error_messages"]) > 10:
                    flash(f'... і ще {len(result["error_messages"]) - 10} помилок', 'warning')
        else:
            flash(f'Помилка імпорту: {result}', 'error')
        
        return redirect(url_for('excel.index'))
    
    except Exception as e:
        current_app.logger.error(f"Помилка імпорту з Excel: {str(e)}")
        flash(f'Помилка імпорту: {str(e)}', 'error')
        return redirect(url_for('excel.index'))
