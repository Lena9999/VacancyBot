import os
import json
import re


def parse_form(form_text):
    # Определяем шаблон для извлечения данных
    fields = {
        'City': r'City:\s*(.*?)\s*(?:🚚|$)',
        'Willing to relocate?': r'Willing to relocate\?:\s*(.*?)\s*(?:💼|$)',
        'Preferred work format': r'Preferred work format:\s*(.*?)\s*(?:📌|$)',
        'Employment type': r'Employment type:\s*(.*?)\s*(?:⏰|$)',
        'Work schedule': r'Work schedule:\s*(.*?)\s*(?:💰|$)',
        'Minimum desired salary': r'Minimum desired salary:\s*(.*?)\s*(?:💱|$)',
        'Currency': r'Currency:\s*(.*?)\s*(?:🛠|$)',
        'Skills': r'Skills:\s*(.*?)\s*(?:📝|$)',
        # Последнее поле до конца
        'Additional notes': r'Additional notes:\s*(.*?)(?:\n\n|$)'
    }

    # Словарь для хранения извлеченных данных
    data = {}

    # Извлекаем данные для каждого поля
    for field, pattern in fields.items():
        match = re.search(pattern, form_text, re.DOTALL)
        if match:
            # Очищаем данные от лишних пробелов и переносов строк
            value = match.group(1).strip()
            # Если поле не пустое, добавляем в словарь
            if value:
                # Для Skills разбиваем на список, если указаны через запятую
                if field == 'Skills':
                    value = [skill.strip() for skill in value.split(',')]
                data[field] = value

    return data


def save_form_data(form_text, output_dir):
    # Парсим данные из формы
    data = parse_form(form_text)

    # Проверяем, существует ли директория, если нет — создаем
    os.makedirs(output_dir, exist_ok=True)

    # Генерируем уникальное имя файла (например, на основе времени)
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'user_data_{timestamp}.json')

    # Сохраняем данные в JSON-файл
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return output_file
