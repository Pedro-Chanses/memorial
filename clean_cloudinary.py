import os
import cloudinary
import cloudinary.api
import cloudinary.uploader
from flask import Flask
from config import config, get_environment

def create_app():
    app = Flask(__name__)
    config_name = get_environment()
    app.config.from_object(config[config_name])
    return app

def clean_cloudinary():
    """Видаляє всі зображення з Cloudinary"""
    print("Початок очищення Cloudinary...")
    
    # Створюємо контекст додатку
    app = create_app()
    with app.app_context():
        try:
            # Налаштування Cloudinary
            cloudinary.config(
                cloud_name=app.config.get('CLOUDINARY_CLOUD_NAME'),
                api_key=app.config.get('CLOUDINARY_API_KEY'),
                api_secret=app.config.get('CLOUDINARY_API_SECRET')
            )
            
            # Отримуємо список всіх ресурсів (зображень)
            print("Отримання списку зображень з Cloudinary...")
            result = cloudinary.api.resources(max_results=500)
            
            if 'resources' in result and result['resources']:
                total = len(result['resources'])
                print(f"Знайдено {total} зображень для видалення")
                
                # Видаляємо кожне зображення
                for i, resource in enumerate(result['resources'], 1):
                    public_id = resource['public_id']
                    print(f"Видалення зображення {i}/{total}: {public_id}")
                    cloudinary.uploader.destroy(public_id)
                
                print("Всі зображення успішно видалені з Cloudinary!")
            else:
                print("Зображення в Cloudinary не знайдені або акаунт вже порожній.")
            
        except Exception as e:
            print(f"Помилка при очищенні Cloudinary: {str(e)}")

if __name__ == "__main__":
    clean_cloudinary()
