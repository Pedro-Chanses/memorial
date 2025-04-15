# Memorial - Сайт пам'ятників та меморіальних комплексів

<div align="center">
  <img src="static/img/logo.png" alt="Логотип Memorial" width="200">
</div>

Веб-сайт для продажу пам'ятників та меморіальних комплексів. Сайт містить каталог пам'ятників, новини, галерею та контактну інформацію. Сайт має потужну адміністративну панель для керування контентом та товарами.

## Функціонал

- **Публічна частина**:
  - Головна сторінка з популярними пам'ятниками
  - Каталог пам'ятників з фільтрацією та пошуком
  - Детальні сторінки пам'ятників з фотогалереєю
  - Сторінка новин з детальним переглядом
  - Галерея зображень виконаних робіт
  - Сторінка контактів та форма зворотного зв'язку
  - Сторінки категорій пам'ятників

- **Адміністративна частина**:
  - Авторизація через email/пароль
  - Управління пам'ятниками (створення, редагування, видалення)
  - Управління артикулами пам'ятників
  - Імпорт/експорт пам'ятників через Excel
  - Управління новинами (створення, редагування, видалення)
  - Завантаження та керування зображеннями в Cloudinary
  - Управління користувачами та доступами

## Технічний стек

- **Backend**:
  - Python 3.9+
  - Flask 3.0+
  - SQLAlchemy 2.0+
  - Flask-Migrate (для міграцій бази даних)
  - Flask-Login (для авторизації)
  - Flask-WTF (для форм та CSRF захисту)
  - Flask-Mail (для відправки email)
  - Flask-Babel (для інтернаціоналізації)
  - Flask-Limiter (для обмеження запитів)
  - psycopg2-binary (для PostgreSQL)
  - Cloudinary (для зберігання зображень)
  - pandas, openpyxl (для імпорту/експорту Excel)

- **Frontend**:
  - Tailwind CSS 3
  - Alpine.js
  - Font Awesome 6

## Встановлення

1. Клонуйте репозиторій:
```bash
git clone https://github.com/mashmanuc/memorial.git
cd memorial
```

2. Створіть віртуальне середовище:
```bash
python -m venv venv
```

3. Активуйте віртуальне середовище:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Встановіть залежності:
```bash
pip install -r requirements.txt
```

5. Створіть файл .env в корені проекту:
```env
# Flask configuration
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=ваш-секретний-ключ-тут

# Cloudinary налаштування
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Налаштування пошти
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=ваша-пошта@gmail.com
MAIL_PASSWORD=ваш-пароль-пошти
MAIL_DEFAULT_SENDER=noreply@memorial-company.com

# Налаштування бази даних
DATABASE_URL=postgresql://username:password@localhost:5432/memorial

# Адміністратори
ADMIN_EMAILS=admin@example.com,another-admin@example.com

# Upload settings

## Керування користувачами

Для керування користувачами використовується CLI інтерфейс через `manage.py`. Доступні наступні команди:

### Створення користувачів

1. Створити звичайного користувача:
```bash
python manage.py create-user
```

2. Створити користувача з правами адміністратора:
```bash
python manage.py create-user --admin
```

В обох випадках вам потрібно буде ввести:
- Username (ім'я користувача)
- Email (електронна пошта)
- Password (пароль, вводиться двічі для підтвердження)

### Перегляд списку користувачів

```bash
python manage.py list-users
```

Команда виведе список всіх користувачів з їх ролями (admin/user) та email адресами.

### Видалення користувача

```bash
python manage.py delete-user username
```

Де `username` - ім'я користувача, якого потрібно видалити. Перед видаленням буде запит на підтвердження.

### Безпека

- Паролі зберігаються в базі даних у зашифрованому вигляді
- Для шифрування використовується алгоритм scrypt
- Всі операції з користувачами логуються
- Невдалі спроби входу обмежуються за допомогою rate limiting
- Сесії користувачів захищені від CSRF атак
MAX_CONTENT_LENGTH=16777216  # 16MB в байтах
```

6. Керування базою даних:

Проект використовує Flask-Migrate для керування версіями бази даних. Доступні команди:

### Перша ініціалізація

Якщо ви вперше запускаєте проект:

```bash
# Ініціалізувати міграції
flask db init

# Створити першу міграцію
flask db migrate -m "Початкова міграція"

# Застосувати міграцію
flask db upgrade
```

### Оновлення бази даних

Коли ви змінюєте моделі (структуру таблиць):

```bash
# Створити нову міграцію
flask db migrate -m "Опис змін"

# Застосувати міграцію
flask db upgrade
```

### Відкат змін

Якщо потрібно відкатити останню міграцію:

```bash
flask db downgrade
```

### Перевірка статусу

Перевірити поточну версію бази даних:

```bash
flask db current
```

Перевірити історію міграцій:

```bash
flask db history
```

**Важливо**: Не змінюйте існуючі міграції, які вже були застосовані. Завжди створюйте нові міграції для змін.

7. Створіть адміністратора:
```bash
python create_admin.py
```

## Запуск

### Локальний запуск

```bash
python app.py
```

Відкрийте http://localhost:5000 у браузері.

### Розгортання на Render

1. Створіть новий Web Service на Render
2. Підключіть ваш GitHub репозиторій
3. Налаштуйте змінні оточення в Render:
   - Додайте всі змінні з файлу .env
   - Встановіть `FLASK_ENV=production`
   - Встановіть `FLASK_DEBUG=0`
4. Build Command:
   ```bash
   pip install -r requirements.txt
   ```
5. Start Command:
   ```bash
   gunicorn app:app
   ```

## Структура проекту

```
okinava/
├── blueprints/          # Blueprints Flask
│   ├── admin.py        # Адмін панель
│   ├── auth.py         # Авторизація
│   ├── main.py         # Головні сторінки
│   ├── events.py       # Події та розклад
│   ├── gallery.py      # Галерея
│   └── news.py         # Новини
├── forms/              # Форми WTForms
├── static/             # Статичні файли
│   ├── css/           # CSS файли
│   ├── js/            # JavaScript файли
│   ├── img/           # Зображення
│   └── uploads/       # Завантажені файли
├── templates/          # Шаблони Jinja2
│   ├── admin/         # Шаблони адмін панелі
│   ├── auth/          # Шаблони авторизації
│   ├── main/          # Основні шаблони
│   ├── news/          # Шаблони новин
│   ├── events/        # Шаблони подій
│   └── gallery/       # Шаблони галереї
├── utils/             # Утиліти
├── migrations/         # Міграції бази даних
├── app.py             # Створення Flask застосунку
├── config.py          # Конфігурація
├── extensions.py      # Розширення Flask
├── models.py          # Моделі SQLAlchemy
└── wsgi.py            # Точка входу для PythonAnywhere
```



## Ліцензія

MIT License
