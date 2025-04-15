import sys
import os

# Додаємо батьківську директорію до шляху пошуку модулів
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)

def upgrade():
    """Додає стовпець is_main до таблиці image"""
    with app.app_context():
        db.engine.execute('ALTER TABLE image ADD COLUMN is_main BOOLEAN DEFAULT FALSE')
        print("Стовпець is_main успішно додано до таблиці image")

def downgrade():
    """Видаляє стовпець is_main з таблиці image"""
    with app.app_context():
        db.engine.execute('ALTER TABLE image DROP COLUMN is_main')
        print("Стовпець is_main успішно видалено з таблиці image")

if __name__ == '__main__':
    upgrade()
