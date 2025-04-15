import os
import cloudinary
import cloudinary.api
import cloudinary.uploader
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()

def test_cloudinary_connection():
    try:
        # Налаштування Cloudinary
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
            api_key=os.environ.get('CLOUDINARY_API_KEY'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET')
        )
        
        print("Успішне налаштування Cloudinary!")
        print(f"Назва хмари: {os.environ.get('CLOUDINARY_CLOUD_NAME')}")
        
        # Отримання інформації про ресурси
        try:
            resources = cloudinary.api.resources(max_results=1)
            total = resources.get('total_count', 0)
            print(f"Загальна кількість ресурсів: {total}")
            
            if 'resources' in resources and resources['resources']:
                print("Приклад ресурсу:")
                print(f"  - URL: {resources['resources'][0].get('url')}")
                print(f"  - Формат: {resources['resources'][0].get('format')}")
                print(f"  - Розмір: {resources['resources'][0].get('bytes')} байт")
        except Exception as e:
            print(f"Помилка при отриманні ресурсів: {str(e)}")
        
        # Тестове завантаження тексту для перевірки з'єднання
        try:
            test_result = cloudinary.uploader.text(
                "Memorial Test",
                public_id="test_connection",
                font_family="Arial",
                font_size=30,
                overwrite=True
            )
            print("Тестове завантаження успішне!")
            print(f"URL тестового зображення: {test_result.get('url')}")
        except Exception as e:
            print(f"Помилка при тестовому завантаженні: {str(e)}")
        
        print("З'єднання з Cloudinary працює коректно!")
        return True
    except Exception as e:
        print(f"Загальна помилка з'єднання з Cloudinary: {str(e)}")
        return False

if __name__ == "__main__":
    test_cloudinary_connection()
