import os
import json
import re


def parse_form(form_text):
    fields = {
        'City': r'City:\s*(.*?)\s*(?:🚚|$)',
        'Willing to relocate?': r'Willing to relocate\?:\s*(.*?)\s*(?:💼|$)',
        'Preferred work format': r'Preferred work format:\s*(.*?)\s*(?:📌|$)',
        'Employment type': r'Employment type:\s*(.*?)\s*(?:⏰|$)',
        'Work schedule': r'Work schedule:\s*(.*?)\s*(?:💰|$)',
        'Minimum desired salary': r'Minimum desired salary:\s*(.*?)\s*(?:💱|$)',
        'Currency': r'Currency:\s*(.*?)\s*(?:🛠|$)',
        'Skills': r'Skills:\s*(.*?)\s*(?:📝|$)',
        'Additional notes': r'Additional notes:\s*(.*?)(?:\n\n|$)'
    }

    data = {}

    for field, pattern in fields.items():
        match = re.search(pattern, form_text, re.DOTALL)
        if match:

            value = match.group(1).strip()
            if value:
                if field == 'Skills':
                    value = [skill.strip() for skill in value.split(',')]
                data[field] = value

    return data


def save_form_data(form_text, output_dir):
    data = parse_form(form_text)

    os.makedirs(output_dir, exist_ok=True)

    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'user_data_{timestamp}.json')

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return output_file
