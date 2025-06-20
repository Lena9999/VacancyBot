import requests


class HHClient:
    BASE_URL = "https://api.hh.ru"

    def __init__(self):
        self.session = requests.Session()

    def search_simple(self, **kwargs):
        """
        Performs a job search on hh.ru using standard API parameters based on the specified filters.
        """
        url = f"{self.BASE_URL}/vacancies"

        params = {k: v for k, v in kwargs.items() if v not in (None, "", [])}

        response = self.session.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[Error] {response.status_code}: {response.text}")
            return None
