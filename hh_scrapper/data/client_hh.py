import requests
import os
from dotenv import load_dotenv
import time


class HHClient:
    
    BASE_URL = "https://api.hh.ru/vacancies"

    def __init__(self, user_agent: str = "MyApp/1.0 (my-app-feedback@example.com)"):
        load_dotenv()
        self.headers = {
            'HH-User-Agent': user_agent,
            "Authorization": f"Bearer {os.environ.get("ACCESS_TOKEN")}",
        }

    def get_areas(self):
        """Получает список регионов с HH.ru"""
        try:
            response = requests.get("https://api.hh.ru/areas", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка при получении регионов: {e}")
            return None    

    def fetch_vacancies(self, search_query: str, area: int = None, 
                    only_with_salary: bool = True, date_from: str = None):
        """
        Собирает ВСЕ доступные вакансии (или до max_vacancies).
        """
        all_vacancies = []
        page = 0
        per_page = 100
        max_pages = 20

        while page < max_pages:
            params = {
                'text': search_query,
                'per_page': per_page,
                'page': page,
                'order_by': 'publication_time',
            }

            if area is not None and area != 0:
                params['area'] = area

            if only_with_salary:
                params['label'] = 'with_salary'

            if date_from:
                params['date_from'] = date_from  

            try:
                response = requests.get(
                    str(self.BASE_URL),
                    params=params,
                    headers=self.headers,
                    timeout=20
                )

                if response.status_code == 403:
                    print(f"❌ 403 Forbidden на странице {page}. Пропускаем.")
                    break

                response.raise_for_status()

                data = response.json()
                items = data.get('items', [])

                if not items:
                    print(f"Страница {page}: вакансий больше нет.")
                    break

                all_vacancies.extend(items)
                print(f"Страница {page}: +{len(items)} вакансий (всего: {len(all_vacancies)})")

                if len(items) < per_page:
                    break

                page += 1
                time.sleep(1.0)

            except Exception as e:
                print(f"Ошибка на странице {page}: {e}")
                break

        print(f"[HH] Всего собрано {len(all_vacancies)} вакансий по запросу '{search_query}'")
        return all_vacancies