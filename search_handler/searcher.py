import os
import logging

"""
This module connects the Telegram bot interface (telegram_bot.py) with the HeadHunter (hh.ru) API to perform vacancy searches
based on user-specified criteria. It also provides per-client logging to track search activity.

Key Components:
---------------
1. `setup_client_logger(client_id)`:
    - Initializes a logger specific to the provided client_id and ensures logs are stored in a
      structured and persistent way under 'logs/search_vacancies/'.

2. `search_vacancies_by_params_hh(hh_api_client, user_vacancy_hh_filters, client_id)`:
    - Performs paginated searches against the hh.ru API using search parameters that match the API format,
      retrieving vacancy data and collecting relevant vacancy URLs from the response for further use
      (e.g., messaging in the Telegram bot).

Usage Notes:
------------
- The `user_vacancy_hh_filters` argument must be a dictionary structured exactly as expected by hh.ru's `search_simple` API method.
"""


def setup_client_logger(client_id):
    logs_dir = "logs/search_vacancies"
    os.makedirs(logs_dir, exist_ok=True)

    logger_name = f"vacancies_{client_id}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        log_filename = os.path.join(logs_dir, f"vacancies_{client_id}.log")
        file_handler = logging.FileHandler(
            log_filename, mode="a", encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def search_vacancies_by_params_hh(hh_api_client, user_vacancy_hh_filters, client_id):
    """
    Performs a paginated search against the hh.ru API using provided search parameters.
    The `user_vacancy_hh_filters` argument must be a dictionary formatted exactly as required by hh.ru's
    API (see official hh.ru API documentation for valid parameters). This dictionary is passed directly
    to the `search_simple` method without modification.
    """
    logger = setup_client_logger(client_id)
    all_vacancies = []
    vacancy_count_page = 5
    for page in range(vacancy_count_page):
        try:
            params = {**user_vacancy_hh_filters, "page": page, "per_page": 100}

            vacancy_response = hh_api_client.search_simple(**params)
            vacancy = vacancy_response.get("items", [])
            if not vacancy:
                logger.info(f"No vacancies on page {page}.")
                break

            kept_this_page = 0
            for vac in vacancy:
                all_vacancies.append(vac)
                kept_this_page += 1

            logger.info(
                f"Checked {len(vacancy)} vacancies on page {page}, "
                f"kept {kept_this_page} active, "
                f"total kept so far: {len(all_vacancies)}"
            )

        except Exception as e:
            logger.error(f"Error when requesting the API on page {page}: {e}")
            break

    vacancy_urls = [
        vac.get("alternate_url") for vac in all_vacancies if vac.get("alternate_url")
    ]

    return vacancy_urls
