#!/usr/bin/env bash
# Скрипт для налаштування середовища на Render

# Встановлюємо залежності
pip install -r requirements.txt

# Створюємо необхідні директорії
mkdir -p static/uploads/news
mkdir -p static/uploads/gallery
mkdir -p static/uploads/avatars
mkdir -p logs
chmod -R 777 logs  # Надаємо повні права на директорію логів

# Ініціалізуємо базу даних (якщо використовуємо SQLite)
if [ "$USE_SQLITE" = "true" ]; then
  echo "Initializing SQLite database..."
  flask db init
  flask db migrate -m "Initial migration"
  flask db upgrade
fi

echo "Build completed successfully!"
