import os
from flask import Flask
from models import db, Monument, MonumentImage, User, Branch, Event, News, Image
from config import config, get_environment

def create_app():
    app = Flask(__name__)
    config_name = get_environment()
    app.config.from_object(config[config_name])
    db.init_app(app)
    return app

def clean_database():
    """Очищає всі таблиці в базі даних"""
    print("Початок очищення бази даних...")
    
    # Створюємо контекст додатку
    app = create_app()
    with app.app_context():
        try:
            # Видаляємо всі записи з таблиць в правильному порядку (з урахуванням зовнішніх ключів)
            print("Видалення зображень пам'ятників...")
            MonumentImage.query.delete()
            
            print("Видалення пам'ятників...")
            Monument.query.delete()
            
            print("Видалення новин...")
            News.query.delete()
            
            print("Видалення подій...")
            Event.query.delete()
            
            print("Видалення філій...")
            Branch.query.delete()
            
            print("Видалення загальних зображень...")
            Image.query.delete()
            
            # Не видаляємо користувачів, щоб зберегти доступ адміністратора
            # print("Видалення користувачів...")
            # User.query.delete()
            
            # Зберігаємо зміни
            db.session.commit()
            print("База даних успішно очищена!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Помилка при очищенні бази даних: {str(e)}")

if __name__ == "__main__":
    clean_database()
