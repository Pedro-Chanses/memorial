import json
import os
import sys
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import re

# Додаємо поточний каталог до шляхів пошуку модулів
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Завантаження змінних середовища
load_dotenv()

# Налаштування Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# Підключення до бази даних
# Виправляємо URL для правильного підключення до PostgreSQL
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres:'):
    # Замінюємо 'postgres:' на 'postgresql:' для SQLAlchemy
    database_url = database_url.replace('postgres:', 'postgresql:', 1)

engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

# Функція для генерації артикулу на основі категорії та ID
def generate_article(category, product_link):
    # Префікси для різних категорій
    category_prefixes = {
        '/odinarni-kombinovani': 'OK',
        '/odinarni-prosti': 'OP',
        '/dityachi-pamyatniki': 'DP',
        '/evropeyski-pamyatniki': 'EP',
        '/pamyatniki-dlya-viyskovikh': 'PV',
        '/podviyni-pamyatniki': 'PP',
        '/suputni-tovari': 'ST',
        '/khresti': 'XR'
    }
    
    # Отримання префіксу для категорії
    prefix = category_prefixes.get(category, 'XX')  # XX - для невідомих категорій
    
    # Виділення ID з посилання
    # Отримуємо останню частину URL після останнього слеша
    product_id = os.path.basename(product_link)
    
    # Видаляємо мінус, якщо він є
    if product_id.startswith('-'):
        product_id = product_id[1:]
    
    # Видаляємо все, що не є цифрами
    # Якщо посилання має формат "https://granit-s.com.ua/tovar/123", то виділимо тільки цифри
    digits_only = ''.join(c for c in product_id if c.isdigit())
    
    # Якщо є цифри, використовуємо їх, інакше використовуємо весь ID
    if digits_only:
        clean_id = digits_only
    else:
        # Якщо цифр немає, беремо перші 10 символів ID
        clean_id = product_id[:10]
    
    # Формування артикулу: префікс + ID
    article = f"{prefix}{clean_id}"
    
    # Обмеження довжини артикулу до 20 символів (максимальна довжина поля article в таблиці monument)
    if len(article) > 20:
        # Залишаємо префікс та перші символи ID, щоб загальна довжина була 20 символів
        article = article[:20]
        print(f"Артикул обмежено до 20 символів: {article}")
    
    print(f"Створено артикул: {article} для посилання: {product_link}")
    return article

# Функція для завантаження зображення в Cloudinary
def upload_to_cloudinary(image_path):
    if not os.path.exists(image_path):
        print(f"Файл не знайдено: {image_path}")
        return None
    
    try:
        # Отримання імені файлу для використання як public_id
        filename = os.path.basename(image_path)
        base_filename = os.path.splitext(filename)[0]
        
        # Завантаження зображення в Cloudinary з унікальним ідентифікатором
        # Cloudinary автоматично генерує унікальні імена файлів
        result = cloudinary.uploader.upload(
            image_path,
            folder="monuments",  # Зберігаємо всі зображення в папці "monuments"
            public_id=f"monument_{base_filename}_{datetime.now().strftime('%Y%m%d%H%M%S')}",  # Унікальний ідентифікатор
            overwrite=True  # Перезаписуємо, якщо файл з таким ідентифікатором вже існує
        )
        print(f"Зображення успішно завантажено в Cloudinary: {result['secure_url']}")
        return result['secure_url']
    except Exception as e:
        print(f"Помилка при завантаженні зображення {image_path}: {e}")
        return None

# Функція для створення запису в таблиці monument
def create_monument(product_data, cloudinary_url):
    # Генерація артикулу
    article = generate_article(product_data['category'], product_data['link'])
    
    # Формування назви (артикул + ID + оригінальна назва)
    name = f"{article} {product_data['name']}"
    
    # Виконання запиту
    try:
        # Поточна дата і час
        now = datetime.utcnow()
        
        # Створення нового екземпляра Monument за допомогою SQLAlchemy ORM
        from models import Monument
        
        # Створення нового об'єкта Monument
        monument = Monument(
            name=name,
            article=article,
            price=int(product_data['price']),
            description=f"Пам'ятник {article}",
            category=product_data['category'],
            main_image=cloudinary_url,
            original_link=product_data['link'],
            is_active=True,
            created_at=now,
            updated_at=now,
            availability='В наявності',
            is_popular=False,
            is_featured=False
        )
        
        # Додавання об'єкта до сесії та збереження
        session.add(monument)
        session.commit()
        
        print(f"Успішно створено пам'ятник {article} з ID {monument.id}")
        return monument.id
    except Exception as e:
        session.rollback()
        print(f"Помилка при створенні запису для пам'ятника {article}: {e}")
        return None

# Функція для створення запису в таблиці monument_image
def create_monument_image(monument_id, cloudinary_url, is_main=True):
    # Виконання запиту
    try:
        # Поточна дата і час
        now = datetime.utcnow()
        
        # Створення нового екземпляра MonumentImage за допомогою SQLAlchemy ORM
        from models import MonumentImage
        
        # Створення нового об'єкта MonumentImage
        monument_image = MonumentImage(
            monument_id=monument_id,
            filename=cloudinary_url,
            is_main=is_main,
            created_at=now
        )
        
        # Додавання об'єкта до сесії та збереження
        session.add(monument_image)
        session.commit()
        
        print(f"Успішно створено зображення для пам'ятника {monument_id}")
        return True
    except Exception as e:
        session.rollback()
        print(f"Помилка при створенні запису для зображення пам'ятника {monument_id}: {e}")
        return False

# Функція для очищення таблиць перед імпортом
def clear_tables():
    try:
        # Завантаження моделей
        from models import Monument, MonumentImage
        
        # Підрахунок кількості записів перед видаленням
        monument_count = session.query(Monument).count()
        image_count = session.query(MonumentImage).count()
        
        print(f"\nПеред очищенням:")
        print(f"- Кількість пам'ятників: {monument_count}")
        print(f"- Кількість зображень: {image_count}")
        
        # Видалення всіх записів з таблиці monument_image
        session.query(MonumentImage).delete()
        
        # Видалення всіх записів з таблиці monument
        session.query(Monument).delete()
        
        # Збереження змін
        session.commit()
        
        print(f"Таблиці успішно очищені.\n")
        return True
    except Exception as e:
        session.rollback()
        print(f"Помилка при очищенні таблиць: {e}")
        return False

# Головна функція для імпорту даних
def import_products():
    # Очищення таблиць перед імпортом
    if not clear_tables():
        print("Не вдалося очистити таблиці. Імпорт скасовано.")
        return
    
    # Шлях до файлу з даними
    json_file_path = 'all_products.json'
    
    # Завантаження даних з JSON-файлу
    with open(json_file_path, 'r', encoding='utf-8') as file:
        products = json.load(file)
    
    print(f"Знайдено {len(products)} продуктів для імпорту")
    
    # Лічильники для статистики
    successful_imports = 0
    failed_imports = 0
    skipped_index_category = 0
    
    # Імпорт кожного продукту
    for product in products:
        # Пропускаємо продукти з категорією '/index'
        if product.get('category') == '/index':
            print(f"Пропускаємо продукт {product.get('name')}: категорія '/index' ігнорується")
            skipped_index_category += 1
            continue
        
        # Отримання шляху до головного зображення
        main_image_path = product.get('main_image_path')
        
        # Якщо шлях до зображення відсутній, пропускаємо продукт
        if not main_image_path:
            print(f"Пропускаємо продукт {product.get('name')}: відсутній шлях до зображення")
            failed_imports += 1
            continue
        
        # Завантаження зображення в Cloudinary
        cloudinary_url = upload_to_cloudinary(main_image_path)
        
        # Якщо завантаження не вдалося, пропускаємо продукт
        if not cloudinary_url:
            print(f"Пропускаємо продукт {product.get('name')}: не вдалося завантажити зображення")
            failed_imports += 1
            continue
        
        # Створення запису в таблиці monument
        monument_id = create_monument(product, cloudinary_url)
        
        # Якщо створення запису не вдалося, пропускаємо продукт
        if not monument_id:
            print(f"Пропускаємо продукт {product.get('name')}: не вдалося створити запис в таблиці monument")
            failed_imports += 1
            continue
        
        # Створення запису в таблиці monument_image для головного зображення
        if not create_monument_image(monument_id, cloudinary_url, True):
            print(f"Не вдалося створити запис для головного зображення пам'ятника {monument_id}")
        
        # Завантаження додаткових зображень
        for additional_image_path in product.get('additional_images', []):
            # Завантаження зображення в Cloudinary
            additional_cloudinary_url = upload_to_cloudinary(additional_image_path)
            
            # Якщо завантаження вдалося, створюємо запис в таблиці monument_image
            if additional_cloudinary_url:
                if not create_monument_image(monument_id, additional_cloudinary_url, False):
                    print(f"Не вдалося створити запис для додаткового зображення пам'ятника {monument_id}")
        
        successful_imports += 1
        print(f"Успішно імпортовано продукт: {product.get('name')}")
    
    # Виведення статистики
    print(f"\nІмпорт завершено!")
    print(f"Успішно імпортовано: {successful_imports}")
    print(f"Не вдалося імпортувати: {failed_imports}")
    print(f"Пропущено продуктів з категорією '/index': {skipped_index_category}")

# Запуск імпорту
if __name__ == "__main__":
    import_products()
