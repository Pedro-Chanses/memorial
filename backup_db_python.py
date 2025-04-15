import os
import datetime
import json
import psycopg2
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()

# Отримання URL бази даних
db_url = os.getenv('DATABASE_URL')

if not db_url:
    print("Помилка: DATABASE_URL не знайдено в .env файлі")
    exit(1)

# Створення директорії для резервних копій, якщо вона не існує
backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
os.makedirs(backup_dir, exist_ok=True)

# Формування імені файлу резервної копії з датою та часом
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = os.path.join(backup_dir, f'memorial_db_backup_{timestamp}.json')

try:
    # Підключення до бази даних
    print(f"Підключення до бази даних...")
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Отримання списку таблиць
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = [table[0] for table in cursor.fetchall()]
    
    print(f"Знайдено {len(tables)} таблиць: {', '.join(tables)}")
    
    # Словник для зберігання даних
    db_data = {}
    
    # Отримання даних з кожної таблиці
    for table in tables:
        print(f"Резервне копіювання таблиці {table}...")
        
        # Отримання структури таблиці
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}'
        """)
        columns = [(col[0], col[1]) for col in cursor.fetchall()]
        
        # Отримання даних з таблиці
        cursor.execute(f"SELECT * FROM \"{table}\"")
        rows = cursor.fetchall()
        
        # Перетворення даних у словник
        table_data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                # Перетворення дати/часу у рядок
                if isinstance(row[i], datetime.datetime):
                    row_dict[col[0]] = row[i].isoformat()
                # Перетворення інших типів даних
                elif row[i] is not None:
                    row_dict[col[0]] = row[i]
                else:
                    row_dict[col[0]] = None
            table_data.append(row_dict)
        
        # Додавання даних таблиці до загального словника
        db_data[table] = {
            'columns': columns,
            'data': table_data
        }
        
        print(f"  - Скопійовано {len(table_data)} записів")
    
    # Збереження даних у JSON-файл
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)
    
    # Перевірка розміру файлу
    backup_size = os.path.getsize(backup_file)
    print(f"\nРезервна копія успішно створена! Розмір файлу: {backup_size / 1024:.2f} КБ")
    print(f"Шлях до файлу: {backup_file}")
    
    # Закриття з'єднання
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Помилка при створенні резервної копії: {str(e)}")

print("\nЗавершено!")
