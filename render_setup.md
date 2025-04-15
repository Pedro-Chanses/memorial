# Налаштування проекту на Render

## Необхідні змінні середовища

Для правильної роботи проекту на Render необхідно налаштувати наступні змінні середовища:

### Основні налаштування
- `SECRET_KEY` - секретний ключ для Flask (генеруйте надійний ключ)
- `RENDER` - встановіть значення `true`
- `USE_SQLITE` - встановіть значення `true` для використання SQLite або `false` для PostgreSQL

### Налаштування електронної пошти
- `MAIL_SERVER` - SMTP сервер (наприклад, smtp.gmail.com)
- `MAIL_PORT` - порт SMTP сервера (зазвичай 587)
- `MAIL_USE_TLS` - використання TLS (встановіть `true`)
- `MAIL_USERNAME` - ім'я користувача для SMTP
- `MAIL_PASSWORD` - пароль для SMTP

### Налаштування Cloudinary
- `CLOUDINARY_CLOUD_NAME` - ім'я хмари Cloudinary
- `CLOUDINARY_API_KEY` - API ключ Cloudinary
- `CLOUDINARY_API_SECRET` - секретний ключ API Cloudinary

## Кроки для розгортання

1. Зареєструйтесь на [Render](https://render.com/)
2. Створіть новий Web Service
3. Підключіть GitHub репозиторій
4. Налаштуйте змінні середовища в розділі "Environment"
5. Розгорніть проект

## Примітки

- База даних SQLite буде скинута при кожному розгортанні. Для продакшену рекомендується використовувати PostgreSQL.
- Для використання PostgreSQL створіть базу даних на Render та налаштуйте змінну `DATABASE_URL`.
