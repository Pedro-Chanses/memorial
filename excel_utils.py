import pandas as pd
import os
import io
from datetime import datetime
from models import Monument, MonumentImage, db
from flask import current_app
import cloudinary
import cloudinary.uploader
import cloudinary.utils
from werkzeug.utils import secure_filename
import time

def export_monuments_to_excel():
    """Експортує дані пам'ятників у Excel файл"""
    # Отримуємо всі пам'ятники з бази даних
    monuments = Monument.query.all()
    
    # Створюємо DataFrame з даними пам'ятників
    data = []
    for monument in monuments:
        # Основна інформація
        monument_data = {
            'id': monument.id,
            'article': monument.article,
            'name': monument.name,
            'price': monument.price,
            'description': monument.description,
            'category': monument.category,
            'dimensions': monument.dimensions,
            'material': monument.material,
            'color': monument.color,
            'weight': monument.weight,
            'availability': monument.availability,
            'production_time': monument.production_time,
            'is_popular': monument.is_popular,
            'discount_percent': monument.discount_percent,
            'old_price': monument.old_price,
            'is_active': monument.is_active,
            'main_image': monument.main_image,
            'seo_title': monument.seo_title,
            'seo_description': monument.seo_description,
            'seo_keywords': monument.seo_keywords,
            'style': monument.style,
            'warranty': monument.warranty,
            'installation_included': monument.installation_included,
            'delivery_info': monument.delivery_info,
            'is_new': monument.is_new,
            'is_featured': monument.is_featured,
            'display_order': monument.display_order,
            'related_products': monument.related_products,
            'created_at': monument.created_at.strftime('%Y-%m-%d %H:%M:%S') if monument.created_at else None,
            'updated_at': monument.updated_at.strftime('%Y-%m-%d %H:%M:%S') if monument.updated_at else None
        }
        
        # Додаємо URLs зображень (до 5 зображень)
        images = MonumentImage.query.filter_by(monument_id=monument.id).all()
        for i, image in enumerate(images[:5]):
            monument_data[f'image_{i+1}'] = image.filename
        
        data.append(monument_data)
    
    # Створюємо DataFrame
    df = pd.DataFrame(data)
    
    # Створюємо Excel файл у пам'яті
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Пам\'ятники', index=False)
        
        # Автоналаштування ширини стовпців
        worksheet = writer.sheets['Пам\'ятники']
        # Використовуємо правильний спосіб отримання імен стовпців для Excel
        from openpyxl.utils import get_column_letter
        for i, col in enumerate(df.columns):
            col_letter = get_column_letter(i+1)
            max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.column_dimensions[col_letter].width = min(max_length, 50)  # Обмежуємо максимальну ширину
    
    output.seek(0)
    return output

def import_monuments_from_excel(file_stream):
    """Імпортує дані пам'ятників з Excel файлу"""
    try:
        # Читаємо Excel файл
        try:
            df = pd.read_excel(file_stream, engine='openpyxl')
        except Exception as e:
            current_app.logger.error(f"Помилка читання Excel файлу: {str(e)}")
            return False, f"Помилка читання Excel файлу: {str(e)}"
        
        # Перевіряємо наявність обов'язкових стовпців
        required_columns = ['article', 'name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Відсутні обов'язкові стовпці: {', '.join(missing_columns)}"
        
        # Статистика імпорту
        stats = {
            'created': 0,
            'updated': 0,
            'errors': 0,
            'error_messages': []
        }
        
        # Обробляємо кожен рядок
        for index, row in df.iterrows():
            try:
                # Перевіряємо, чи існує пам'ятник з таким артикулом
                if 'article' not in row or pd.isna(row['article']):
                    stats['errors'] += 1
                    stats['error_messages'].append(f"Рядок #{index+2}: Відсутній артикул")
                    continue
                    
                article = str(row['article']).strip()
                if not article:
                    stats['errors'] += 1
                    stats['error_messages'].append(f"Рядок #{index+2}: Порожній артикул")
                    continue
                
                existing_monument = Monument.query.filter_by(article=article).first()
                
                if existing_monument:
                    # Оновлюємо існуючий пам'ятник
                    update_monument_from_row(existing_monument, row)
                    stats['updated'] += 1
                else:
                    # Створюємо новий пам'ятник
                    try:
                        new_monument = create_monument_from_row(row)
                        if new_monument:
                            stats['created'] += 1
                        else:
                            stats['errors'] += 1
                            stats['error_messages'].append(f"Рядок #{index+2}: Помилка створення пам'ятника з артикулом {article}")
                    except Exception as create_error:
                        stats['errors'] += 1
                        stats['error_messages'].append(f"Рядок #{index+2}: Помилка створення пам'ятника - {str(create_error)}")
            
            except Exception as e:
                stats['errors'] += 1
                stats['error_messages'].append(f"Рядок #{index+2}: Помилка обробки - {str(e)}")
        
        # Зберігаємо зміни в базі даних
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Помилка збереження в базу даних: {str(e)}")
            return False, f"Помилка збереження в базу даних: {str(e)}"
        
        return True, stats
    
    except Exception as e:
        current_app.logger.error(f"Помилка імпорту з Excel: {str(e)}")
        return False, str(e)

def update_monument_from_row(monument, row):
    """Оновлює існуючий пам'ятник даними з рядка Excel"""
    try:
        # Оновлюємо текстові поля
        text_fields = ['name', 'description', 'category', 'dimensions', 'material', 'color', 
                       'availability', 'production_time', 'seo_title', 'seo_description', 
                       'seo_keywords', 'style', 'warranty', 'delivery_info', 'related_products']
        
        for field in text_fields:
            if field in row and not pd.isna(row[field]):
                setattr(monument, field, str(row[field]).strip())
        
        # Оновлюємо числові поля
        numeric_fields = ['price', 'weight', 'discount_percent', 'old_price', 'display_order']
        for field in numeric_fields:
            if field in row and not pd.isna(row[field]):
                try:
                    # Спочатку перетворюємо в рядок, щоб видалити можливі невидимі символи
                    str_value = str(row[field]).strip().replace(',', '.')
                    value = float(str_value)
                    if field in ['price', 'discount_percent', 'old_price', 'display_order']:
                        value = int(value)
                    setattr(monument, field, value)
                except (ValueError, TypeError) as e:
                    current_app.logger.warning(f"Помилка перетворення числового поля {field}: {str(e)}")
        
        # Оновлюємо булеві поля
        boolean_fields = ['is_popular', 'is_active', 'installation_included', 'is_new', 'is_featured']
        for field in boolean_fields:
            if field in row and not pd.isna(row[field]):
                try:
                    value = str(row[field]).lower().strip()
                    setattr(monument, field, value in ['true', '1', 'так', 'yes', 'y', 'т', '+'])
                except Exception as e:
                    current_app.logger.warning(f"Помилка перетворення булевого поля {field}: {str(e)}")
        
        # Оновлюємо зображення, якщо вони вказані
        for i in range(1, 6):  # Перевіряємо до 5 зображень
            image_field = f'image_{i}'
            if image_field in row and not pd.isna(row[image_field]):
                image_url = str(row[image_field]).strip()
                if image_url and (image_url.startswith('http') or image_url.startswith('https')):
                    try:
                        # Перевіряємо, чи існує таке зображення
                        existing_image = MonumentImage.query.filter_by(monument_id=monument.id, filename=image_url).first()
                        if not existing_image:
                            # Створюємо новий запис для зображення
                            new_image = MonumentImage(
                                monument_id=monument.id,
                                filename=image_url,
                                is_main=(i == 1)  # Перше зображення - головне
                            )
                            db.session.add(new_image)
                        
                        # Якщо це перше зображення, встановлюємо його як головне
                        if i == 1:
                            monument.main_image = image_url
                    except Exception as e:
                        current_app.logger.warning(f"Помилка додавання зображення {image_field}: {str(e)}")
        
        # Оновлюємо дату оновлення
        monument.updated_at = datetime.now()
        
        # Додаємо до сесії
        db.session.add(monument)
        return True
    except Exception as e:
        current_app.logger.error(f"Помилка оновлення пам'ятника: {str(e)}")
        return False

def create_monument_from_row(row):
    """Створює новий пам'ятник з даних рядка Excel"""
    try:
        # Перевіряємо наявність обов'язкових полів
        article = str(row['article']).strip() if not pd.isna(row['article']) else None
        name = str(row['name']).strip() if not pd.isna(row['name']) else None
        
        if not article or not name:
            return None
        
        # Створюємо новий пам'ятник
        monument = Monument(
            article=article,
            name=name,
            is_active=True  # За замовчуванням активний
        )
        
        # Заповнюємо текстові поля
        text_fields = ['description', 'category', 'dimensions', 'material', 'color', 
                      'availability', 'production_time', 'seo_title', 'seo_description', 
                      'seo_keywords', 'style', 'warranty', 'delivery_info', 'related_products']
        
        for field in text_fields:
            if field in row and not pd.isna(row[field]):
                setattr(monument, field, str(row[field]).strip())
        
        # Заповнюємо числові поля
        numeric_fields = ['price', 'weight', 'discount_percent', 'old_price', 'display_order']
        for field in numeric_fields:
            if field in row and not pd.isna(row[field]):
                try:
                    # Спочатку перетворюємо в рядок, щоб видалити можливі невидимі символи
                    str_value = str(row[field]).strip().replace(',', '.')
                    value = float(str_value)
                    if field in ['price', 'discount_percent', 'old_price', 'display_order']:
                        value = int(value)
                    setattr(monument, field, value)
                except (ValueError, TypeError) as e:
                    current_app.logger.warning(f"Помилка перетворення числового поля {field}: {str(e)}")
        
        # Заповнюємо булеві поля
        boolean_fields = ['is_popular', 'is_active', 'installation_included', 'is_new', 'is_featured']
        for field in boolean_fields:
            if field in row and not pd.isna(row[field]):
                try:
                    value = str(row[field]).lower().strip()
                    setattr(monument, field, value in ['true', '1', 'так', 'yes', 'y', 'т', '+'])
                except Exception as e:
                    current_app.logger.warning(f"Помилка перетворення булевого поля {field}: {str(e)}")
        
        # Додаємо до бази даних
        db.session.add(monument)
        db.session.flush()  # Отримуємо ID
        
        # Додаємо зображення, якщо вони вказані
        for i in range(1, 6):  # Перевіряємо до 5 зображень
            image_field = f'image_{i}'
            if image_field in row and not pd.isna(row[image_field]):
                image_url = str(row[image_field]).strip()
                if image_url and (image_url.startswith('http') or image_url.startswith('https')):
                    try:
                        # Створюємо новий запис для зображення
                        new_image = MonumentImage(
                            monument_id=monument.id,
                            filename=image_url,
                            is_main=(i == 1)  # Перше зображення - головне
                        )
                        db.session.add(new_image)
                        
                        # Якщо це перше зображення, встановлюємо його як головне
                        if i == 1:
                            monument.main_image = image_url
                    except Exception as e:
                        current_app.logger.warning(f"Помилка додавання зображення {image_field}: {str(e)}")
        
        # Встановлюємо дату створення
        monument.created_at = datetime.now()
        monument.updated_at = datetime.now()
        
        return monument
    
    except Exception as e:
        current_app.logger.error(f"Помилка створення пам'ятника з Excel: {str(e)}")
        db.session.rollback()
        return None
