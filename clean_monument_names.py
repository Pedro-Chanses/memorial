import os
import re
import psycopg2
from dotenv import load_dotenv
from app import create_app, db
from models import Monument

# Завантаження змінних середовища
load_dotenv()

def clean_monument_names():
    """
    Видаляє артикули та інші префікси з назв пам'ятників.
    Видаляє:
    - Артикули з номерами (OK98 №77.)
    - Числові префікси (14., 29)
    - Префікси в дужках ((145))
    - Артикули без номерів (ST40, STkhudozhnya, STpryamokutn)
    """
    app = create_app()
    
    with app.app_context():
        print("Початок очищення назв пам'ятників...")
        
        # Отримання всіх пам'ятників
        monuments = Monument.query.all()
        print(f"Знайдено {len(monuments)} пам'ятників")
        
        # Лічильники для статистики
        updated_count = 0
        skipped_count = 0
        
        # Регулярний вираз для пошуку артикулів та номерів на початку назви
        # Шукаємо: артикул (наприклад, OK98, OP123, DP45, EP55, PV67, PP89, ST12, XR34), 
        # потім можливо пробіл, потім можливо "№" з цифрами (можливо в дужках), потім можливо число, потім крапка
        # Приклади: "OK98 №77.", "OP123№45.", "EP55№12.", "OK118 №(63) 8."
        # Використовуємо всі можливі префікси категорій: OK, OP, DP, EP, PV, PP, ST, XR
        pattern = r'^((OK|OP|DP|EP|PV|PP|ST|XR)\d+\s*№\(?\d+\)?\s*\d*\.)'
        
        for monument in monuments:
            original_name = monument.name
            new_name = original_name
            prefix = ""
            updated = False
            
            # 1. Перевіряємо, чи є символ "№" в назві
            if "№" in new_name:
                # Знаходимо позицію символу "№"
                num_index = new_name.index("№")
                
                # Знаходимо все, що треба видалити - від початку рядка до кінця номера
                # Шукаємо перший пробіл після номера або кінець цифр та крапки
                end_index = num_index
                for i in range(num_index + 1, len(new_name)):
                    if new_name[i].isdigit() or new_name[i] in '().,': 
                        end_index = i
                    elif new_name[i] == ' ' and i > num_index + 1:
                        # Знайшли пробіл після цифр та символів
                        end_index = i
                        break
                    else:
                        break
                
                # Видаляємо все до кінця номера
                prefix = new_name[:end_index + 1]
                new_name = new_name[end_index + 1:].strip()
                updated = True
            
            # 2. Перевіряємо числові префікси з крапкою (14.)
            elif re.match(r'^\d+\.\s', new_name):
                match = re.match(r'^(\d+\.\s)', new_name)
                if match:
                    prefix = match.group(1)
                    new_name = new_name[len(prefix):].strip()
                    updated = True
            
            # 3. Перевіряємо префікси в дужках ((145))
            elif re.match(r'^\(\d+\)\s', new_name):
                match = re.match(r'^(\(\d+\)\s)', new_name)
                if match:
                    prefix = match.group(1)
                    new_name = new_name[len(prefix):].strip()
                    updated = True
            
            # 4. Перевіряємо числові префікси без крапки (29)
            elif re.match(r'^\d+\s', new_name):
                match = re.match(r'^(\d+\s)', new_name)
                if match:
                    prefix = match.group(1)
                    new_name = new_name[len(prefix):].strip()
                    updated = True
            
            # 5. Перевіряємо артикули без номерів (ST40, STkhudozhnya, STpryamokutn)
            elif re.match(r'^(ST\d+|ST[a-zA-Z]+)\s', new_name):
                match = re.match(r'^(ST\d+|ST[a-zA-Z]+)\s', new_name)
                if match:
                    prefix = match.group(1)
                    new_name = new_name[len(prefix):].strip()
                    updated = True
            
            # Перевіряємо інші артикули категорій (OK, OP, DP, EP, PV, PP, XR)
            elif re.match(r'^(OK|OP|DP|EP|PV|PP|XR)\d+\s', new_name):
                match = re.match(r'^((OK|OP|DP|EP|PV|PP|XR)\d+)\s', new_name)
                if match:
                    prefix = match.group(1)
                    new_name = new_name[len(prefix):].strip()
                    updated = True
                
            # Перевірка, чи не стала назва порожньою
            if not new_name:
                print(f"Пропускаємо пам'ятник {monument.id}: назва стала б порожньою")
                skipped_count += 1
                continue
            
            # Оновлення назви пам'ятника, якщо вона змінилася
            if updated:
                monument.name = new_name
                updated_count += 1
                
                print(f"Оновлено пам'ятник {monument.id}:")
                print(f"  Було: {original_name}")
                print(f"  Стало: {new_name}")
                print(f"  Видалено: {prefix}")
            else:
                skipped_count += 1
        
        # Збереження змін у базі даних
        if updated_count > 0:
            db.session.commit()
            print(f"\nЗміни збережено в базі даних")
        
        # Виведення статистики
        print(f"\nСтатистика:")
        print(f"- Оновлено пам'ятників: {updated_count}")
        print(f"- Пропущено пам'ятників: {skipped_count}")
        print(f"- Загальна кількість пам'ятників: {len(monuments)}")

if __name__ == "__main__":
    clean_monument_names()
    print("\nЗавершено!")
