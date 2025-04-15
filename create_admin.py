from app import create_app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash
import getpass
import sys

def create_admin():
    print("=== Створення адміністратора ===")
    
    app = create_app()
    with app.app_context():
        # Запитуємо дані адміністратора
        username = input("Введіть ім'я користувача: ")
        email = input("Введіть email: ")
        password = getpass.getpass("Введіть пароль: ")
        first_name = input("Введіть ім'я: ")
        last_name = input("Введіть прізвище: ")
        
        # Перевіряємо чи існує користувач з таким username або email
        if User.query.filter_by(username=username).first():
            print("Помилка: Користувач з таким іменем вже існує!")
            return False
        
        if User.query.filter_by(email=email).first():
            print("Помилка: Користувач з таким email вже існує!")
            return False
        
        # Створюємо нового адміністратора
        admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            is_admin=True,
            is_active=True
        )
        
        # Зберігаємо в базу даних
        db.session.add(admin)
        db.session.commit()
        
        print(f"\nАдміністратор {username} успішно створений!")
        return True

if __name__ == '__main__':
    try:
        if create_admin():
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nОперацію скасовано")
        sys.exit(1)
    except Exception as e:
        print(f"Неочікувана помилка: {str(e)}")
        sys.exit(1)
