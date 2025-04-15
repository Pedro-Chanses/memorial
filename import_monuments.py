import json
import os
import re
import random
import string
from flask import Flask
from models import Monument, MonumentImage, db
from app import create_app

def extract_dimensions(name):
    """Витягує розміри з назви пам'ятника"""
    dimensions_pattern = r'(\d+)\s*[хx*]\s*(\d+)'
    match = re.search(dimensions_pattern, name)
    if match:
        return f"{match.group(1)}x{match.group(2)}"
    return None

def extract_color(name):
    """Витягує колір з назви пам'ятника"""
    colors = ['сірий', 'чорний', 'білий', 'коричневий', 'червоний', 'зелений', 'синій']
    for color in colors:
        if color in name.lower():
            return color
    return None

# Словник префіксів артикулів для категорій
# Цей словник використовується для генерації артикулів і пояснення їх значення
ARTICLE_PREFIXES = {
    '/odinarni-kombinovani': {'prefix': 'OK', 'description': 'Одинарні комбіновані пам\'ятники'},
    '/odinarni-prosti': {'prefix': 'OP', 'description': 'Одинарні прості пам\'ятники'},
    '/dityachi-pamyatniki': {'prefix': 'DP', 'description': 'Дитячі пам\'ятники'},
    '/evropeyski-pamyatniki': {'prefix': 'EP', 'description': 'Європейські пам\'ятники'},
    '/pamyatniki-dlya-viyskovikh': {'prefix': 'PV', 'description': 'Пам\'ятники для військових'},
    '/podviyni-pamyatniki': {'prefix': 'PP', 'description': 'Подвійні пам\'ятники'},
    '/suputni-tovari': {'prefix': 'ST', 'description': 'Аксесуари'},
    '/khresti': {'prefix': 'XR', 'description': 'Хрести'},
    '/index': {'prefix': 'ZG', 'description': 'Загальна категорія'},
}

def generate_article(category, existing_articles):
    """Генерує унікальний артикул для пам'ятника"""
    # Визначаємо префікс відповідно до категорії
    if category in ARTICLE_PREFIXES:
        prefix = ARTICLE_PREFIXES[category]['prefix']
    else:
        # Якщо категорія не знайдена в словнику, використовуємо альтернативний метод
        if 'одинарн' in category.lower():
            prefix = 'OP'  # Одинарні прості
        elif 'подвійн' in category.lower() or 'подвойн' in category.lower():
            prefix = 'PP'  # Подвійні
        elif 'дитяч' in category.lower():
            prefix = 'DP'  # Дитячі
        elif 'хрест' in category.lower():
            prefix = 'XR'  # Хрести
        elif 'військов' in category.lower():
            prefix = 'PV'  # Військові
        elif 'європейськ' in category.lower():
            prefix = 'EP'  # Європейські
        else:
            prefix = 'ZG'  # Загальна категорія
    
    # Спробуємо згенерувати унікальний артикул
    max_attempts = 100
    for _ in range(max_attempts):
        # Генеруємо випадковий номер від 1 до 999
        number = random.randint(1, 999)
        article = f"{prefix}{number}"
        
        # Перевіряємо, чи такий артикул вже існує
        if article not in existing_articles:
            return article
    
    # Якщо не вдалося згенерувати унікальний артикул, додаємо випадкові символи
    random_suffix = ''.join(random.choices(string.ascii_uppercase, k=2))
    number = random.randint(1, 999)
    return f"{prefix}{number}{random_suffix}"

def import_monuments():
    """Імпортує пам'ятники з JSON файлу в базу даних"""
    app = create_app()
    
    with app.app_context():
        # Завантаження JSON файлу
        with open('all_products.json', 'r', encoding='utf-8') as file:
            products = json.load(file)
        
        # Лічильники для статистики
        total_count = len(products)
        imported_count = 0
        
        print(f"Знайдено {total_count} пам'ятників для імпорту")
        
        # Отримуємо всі існуючі артикули
        existing_articles = set(m.article for m in Monument.query.all() if m.article)
        
        # Імпорт кожного пам'ятника
        for product in products:
            # Перевірка, чи вже існує пам'ятник з таким посиланням
            existing_monument = Monument.query.filter_by(original_link=product['link']).first()
            if existing_monument:
                print(f"Пам'ятник з посиланням {product['link']} вже існує, пропускаємо")
                continue
            
            # Витягуємо розміри та колір з назви
            dimensions = extract_dimensions(product['name'])
            color = extract_color(product['name'])
            
            # Генеруємо унікальний артикул
            article = generate_article(product['category'], existing_articles)
            existing_articles.add(article)  # Додаємо в список існуючих артикулів
            
            # Створюємо новий пам'ятник
            monument = Monument(
                name=product['name'],
                article=article,
                price=int(product['price']) if product['price'].isdigit() else None,
                category=product['category'].replace('/', ''),
                main_image=product['main_image_path'].replace('\\', '/') if 'main_image_path' in product else None,
                original_link=product['link'],
                dimensions=dimensions,
                color=color,
                is_active=True
            )
            
            db.session.add(monument)
            db.session.flush()  # Отримуємо ID пам'ятника
            
            # Додаємо зображення
            if 'downloaded_images' in product and product['downloaded_images']:
                for i, img_path in enumerate(product['downloaded_images']):
                    image = MonumentImage(
                        monument_id=monument.id,
                        filename=img_path.replace('\\', '/'),
                        is_main=(i == 0)  # Перше зображення - головне
                    )
                    db.session.add(image)
            
            # Додаємо додаткові зображення
            if 'additional_images' in product and product['additional_images']:
                for img_path in product['additional_images']:
                    image = MonumentImage(
                        monument_id=monument.id,
                        filename=img_path.replace('\\', '/'),
                        is_main=False
                    )
                    db.session.add(image)
            
            imported_count += 1
            
            # Зберігаємо зміни кожні 50 пам'ятників
            if imported_count % 50 == 0:
                db.session.commit()
                print(f"Імпортовано {imported_count} пам'ятників")
        
        # Зберігаємо всі зміни
        db.session.commit()
        print(f"Імпорт завершено. Імпортовано {imported_count} з {total_count} пам'ятників")

if __name__ == "__main__":
    import_monuments()
