import cloudinary
import cloudinary.uploader
from flask import current_app
import uuid
from werkzeug.utils import secure_filename

def upload_image(file, folder='okinava', width=None, height=None, crop=None):
    """
    Завантажує зображення в Cloudinary
    
    Args:
        file: Файл зображення
        folder: Папка в Cloudinary
        width: Ширина для трансформації
        height: Висота для трансформації
        crop: Метод кропу (fill, limit, etc.)
        
    Returns:
        dict: Результат завантаження з Cloudinary
    """
    if not file:
        return None
        
    # Налаштування Cloudinary
    cloudinary.config(
        cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=current_app.config['CLOUDINARY_API_KEY'],
        api_secret=current_app.config['CLOUDINARY_API_SECRET']
    )
    
    # Генеруємо унікальне ім'я файлу
    filename = secure_filename(file.filename)
    public_id = f"{folder}_{int(uuid.uuid4().hex[:8], 16)}_{filename}"
    
    # Налаштування трансформації
    transformation = {}
    if width:
        transformation['width'] = width
    if height:
        transformation['height'] = height
    if crop:
        transformation['crop'] = crop
    
    # Завантажуємо файл
    try:
        upload_result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            folder=folder,
            overwrite=True,
            resource_type="image",
            transformation=transformation
        )
        current_app.logger.info(f"Зображення успішно завантажено: {public_id}")
        return upload_result
    except Exception as e:
        current_app.logger.error(f"Помилка завантаження зображення: {str(e)}")
        return None

def get_thumbnail_url(public_id, width=400, height=300):
    """
    Створює URL мініатюри для зображення
    
    Args:
        public_id: Cloudinary public_id зображення
        width: Ширина мініатюри
        height: Висота мініатюри
        
    Returns:
        str: URL мініатюри
    """
    return cloudinary.utils.cloudinary_url(
        public_id,
        width=width,
        height=height,
        crop="fill",
        quality="auto",
        fetch_format="auto"
    )[0]
