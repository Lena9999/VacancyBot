import re
from datetime import datetime


"""
Module for parsing job preference forms filled out by users.

This parser is made to prepare user data in the right format for the HeadHunter (HH.ru) job platform API.

The parsing logic is designed to produce exactly **two** dictionaries:
- `api_params`: contains only parameters that can be directly sent to the HH API in the required format.
- `other_params`: includes fields that the HH API does not accept, but which may be useful for future processing.

The parser returns these dictionaries and they are saved as JSON for later use.

Functions:
- clean_value: removes template hints and extra spaces
- get_city_id: maps city names to HH area IDs
- parse_form: main entry point to parse the full form
"""


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
    """
    Converts a city name into its corresponding HeadHunter API area ID.

    Args:
        city_name (str): Name of the city provided by the user.

    Returns:
        int or None: Numeric ID for known cities, or None if not recognized.
    """
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
        "schedule": r"Schedule:\s*(.*?)\s*(?:\n|#|$)",
        "employment": r"Employment type:\s*(.*?)\s*(?:\n|#|$)",
        "salary": r"Minimum desired salary:\s*(.*?)\s*(?:\n|#|$)",
        "currency": r"Currency:\s*(.*?)\s*(?:\n|#|$)",
        "date_from": r"Show jobs published after:\s*(.*?)\s*(?:\n|#|$)",
    }

    other_fields = {
        "skills": r"Skills:\s*(.*?)\s*(?:\n|#|$)",
        "willing_to_relocate": r"Willing to relocate\?:\s*(.*?)\s*(?:\n|#|$)",
        "additional_notes": r"Additional notes:\s*(.*?)(?:\n\n|#|$)",
    }

    all_param = {}
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
        value = clean_value(raw)
        if value is not None and value != "":
            all_param[field] = value

    api_params = {}

    # process comma-separated ("skills", "schedule", "employment") lists
    for list_field in {"skills", "schedule", "employment"}:
        if list_field in all_param:
            raw_value = all_param[list_field]
            if isinstance(raw_value, str):
                all_param[list_field] = [
                    item.strip() for item in raw_value.split(",") if item.strip()
                ]

    # processing of the area parameter
    if "area" in all_param:
        city_text = all_param.pop("area")
        city_id = get_city_id(city_text)
        if city_id is not None:
            api_params["area"] = city_id
        else:
            api_params["area"] = city_text

    # processing of the date_from parameter
    if "date_from" in all_param:
        date_value = all_param.pop("date_from")
        try:
            datetime.strptime(date_value, "%Y-%m-%d")
            api_params["date_from"] = date_value
        except ValueError:
            pass

    # processing of parameters that do not require complex processing
    for key in api_fields.keys():
        if key in {"area", "date_from"}:
            continue
        if key in all_param:
            api_params[key] = all_param[key]
    other_params = {}
    for key in other_fields.keys():
        if key in all_param:
            other_params[key] = all_param[key]

    return [api_params, other_params]
