from app import app, db
from sqlalchemy import inspect

# Створюємо контекст додатку
with app.app_context():
    # Отримуємо інспектор бази даних
    inspector = inspect(db.engine)
    
    # Виводимо список таблиць
    tables = inspector.get_table_names()
    print(f"Таблиці в базі даних: {tables}")
    
    # Перевіряємо колонки в таблиці image
    columns = inspector.get_columns('image')
    print("\nКолонки в таблиці image:")
    for column in columns:
        print(f"  - {column['name']}: {column['type']}")
    
    # Оновлюємо метадані
    db.metadata.clear()
    db.metadata.reflect(bind=db.engine)
    
    print("\nМетадані оновлено!")
    
    # Перевіряємо, чи існують потрібні колонки
    columns = inspector.get_columns('image')
    column_names = [col['name'] for col in columns]
    
    if 'is_own_work' in column_names:
        print("Колонка is_own_work існує в таблиці image")
    else:
        print("Колонка is_own_work НЕ існує в таблиці image")
        
    if 'own_work_id' in column_names:
        print("Колонка own_work_id існує в таблиці image")
    else:
        print("Колонка own_work_id НЕ існує в таблиці image")
        
    if 'gallery_id' in column_names:
        print("Колонка gallery_id існує в таблиці image")
    else:
        print("Колонка gallery_id НЕ існує в таблиці image")
