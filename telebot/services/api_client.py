import aiohttp
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

class ApiClient:
    def __init__(self):
        self.base_url = os.environ.get("API_URL")
        self._session = None

    async def get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def check_area(self, area_name: str):
        url = f"{self.base_url}area/"

        payload = {"area_name": area_name}

        print(f"[BOT] → Отправляем запрос | area_name={area_name}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=600) as response:
                    print(f"[BOT] ← Статус: {response.status}")

                    if response.status in (200, 201):
                        return await response.json()
                    else:
                        error_text = await response.text()
                        print(f"[BOT] Ошибка {response.status}: {error_text[:400]}")
                        return None
        except Exception as e:
            print(f"[BOT] Ошибка соединения: {e}")
            return None

        except asyncio.TimeoutError:
            print("[BOT] Ошибка: Таймаут при обращении к Django (слишком долго обрабатывалось)")
            return None

    async def get_data(self, keyword: str, area_id: int, tg_id: int, username: str = None, first_name: str = None):
        url = f"{self.base_url}parse/"

        payload = {
            "name": keyword,
            "tg_id": tg_id,
            "username": username,
            "first_name": first_name,
            "area_id": area_id
        }

        print(f"[BOT] → Отправляем запрос '{keyword}' | tg_id={tg_id} | username={username} | area_id={area_id}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=600) as response:
                    print(f"[BOT] ← Статус: {response.status}")

                    if response.status in (200, 201):
                        return await response.json()
                    else:
                        error_text = await response.text()
                        print(f"[BOT] Ошибка {response.status}: {error_text[:400]}")
                        return None
        except Exception as e:
            print(f"[BOT] Ошибка соединения: {e}")
            return None

        except asyncio.TimeoutError:
            print("[BOT] Ошибка: Таймаут при обращении к Django (слишком долго обрабатывалось)")
            return None
       
    async def search_by_skills(self, skills: list, area_id: int):
        url = f"{self.base_url.rstrip('/')}/search_by_skills/"

        payload = {
            "skills": skills,
            "area_id": area_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=600) as response:
                if response.status in (200, 201):
                    return await response.json()
                else:
                    error_text = await response.text()
                    print(f"Ошибка поиска по навыкам: {response.status} - {error_text[:200]}")
                    return None   
