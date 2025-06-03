import re


def clean_value(value):
    if isinstance(value, str):
        return value.split("# Example")[0].strip()
    if isinstance(value, list):
        return [
            v
            for v in (val.strip() if isinstance(val, str) else val for val in value)
            if not (isinstance(v, str) and v.startswith("# Example"))
        ]
    return value


def get_city_id(city_name):
    mapping = {
        "москва": 1,
        "moscow": 1,
        "санкт-петербург": 2,
        "петербург": 2,
        "питер": 2,
        "saint-petersburg": 2,
        "st. petersburg": 2,
    }
    key = city_name.strip().lower()
    return mapping.get(key)


def parse_form(form_text):
    api_fields = {
        "area": r"City:\s*(.*?)\s*(?:\n|#|$)",
        "schedule": r"Preferred work format:\s*(.*?)\s*(?:\n|#|$)",
        "employment": r"Employment type:\s*(.*?)\s*(?:\n|#|$)",
        "salary": r"Minimum desired salary:\s*(.*?)\s*(?:\n|#|$)",
        "currency": r"Currency:\s*(.*?)\s*(?:\n|#|$)",
    }

    other_fields = {
        "skills": r"Skills:\s*(.*?)\s*(?:\n|#|$)",
        "willing_to_relocate": r"Willing to relocate\?:\s*(.*?)\s*(?:\n|#|$)",
        "work_schedule": r"Work schedule:\s*(.*?)\s*(?:\n|#|$)",
        "additional_notes": r"Additional notes:\s*(.*?)(?:\n\n|#|$)",
    }

    data = {}
    all_fields = {}
    all_fields.update(api_fields)
    all_fields.update(other_fields)

    for field, pattern in all_fields.items():
        match = re.search(pattern, form_text, re.IGNORECASE | re.DOTALL)
        if not match:
            continue

        raw = match.group(1).strip()
        if not raw:
            continue

        if field == "skills":
            raw = [skill.strip() for skill in raw.split(",")]

        value = clean_value(raw)
        if value is not None and value != "":
            data[field] = value

    api_params = {}
    if "area" in data:
        city_text = data.pop("area")
        city_id = get_city_id(city_text)
        if city_id is not None:
            api_params["area"] = city_id
        else:
            api_params["area"] = city_text

    for key in api_fields.keys():
        if key == "area":
            continue
        if key in data:
            api_params[key] = data[key]
    other_params = {}
    for key in other_fields.keys():
        if key in data:
            other_params[key] = data[key]

    return [api_params, other_params]
