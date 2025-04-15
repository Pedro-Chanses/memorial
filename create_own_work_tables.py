from app import app, db
from models import OwnWork, Image

# Створюємо контекст додатку
with app.app_context():
    # Створюємо таблиці
    db.create_all()
    
    print("Таблиці успішно створено!")
