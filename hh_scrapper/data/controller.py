import os
from .models import Vacancy, Skill, Profession, UniqueUser, UserProfessionRequest, Area
from .client_hh import HHClient
from dateutil import parser
import json
from dotenv import load_dotenv
from django.db.models import Count, Avg
import re
import ollama
from django.utils import timezone
from datetime import timedelta

class DataVacancyController:
    def clean_old_vacancies(self, days: int = 30):
        """
        Удаляет вакансии старше указанного количества дней.
        """

        cutoff_date = timezone.now().date() - timedelta(days=days)

        to_delete = Vacancy.objects.filter(published_at__lt=cutoff_date)
        count = to_delete.count()

        if count == 0:
            print(f"[Clean] Вакансий старше {days} дней не найдено.")
            return 0

        print(f"[Clean] Найдено {count} вакансий старше {days} дней. Удаляем...")

        deleted_count, _ = to_delete.delete()

        print(f"[Clean] ✅ Успешно удалено {deleted_count} вакансий (старше {days} дней)")

        return deleted_count
    
    def get_area_id_by_name(self, area_name: str) -> int | None:
        load_dotenv()
        
        area = Area.objects.filter(name__iregex=f'^{area_name}$').first()

        if area:
            print(f"✅ Найден регион: {area.name} (ID: {area.hh_id})")
            return area.hh_id
        else:
            print(f"❌ Регион '{area_name}' не найден")
            return None
    
    def ai_response(self, skills_dict: dict, query: str = "", is_automatic: bool = False):
        result = {}
        
        if is_automatic:
            batch_size = 1
        else:
            batch_size = 6

        client = ollama.Client()

        items = list(skills_dict.items())

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_text = ""

            for vid, data in batch:
                if isinstance(data, dict):
                    text = data.get("requirement", "")
                    vacancy_name = data.get("name", "")
                else:
                    text = str(data)
                    vacancy_name = ""

                batch_text += f"\n--- ВАКАНСИЯ {vid} ---\n{text}\n"

            context = f"Вакансия: {vacancy_name}" if is_automatic and vacancy_name else f"Запрос: {query}"

            try:
                response = client.chat(
                    model="qwen2.5:14b",
                    messages=[
                        {"role": "system", "content": "Ты — эксперт по извлечению навыков. Отвечай ТОЛЬКО JSON. Никакого другого текста."},
                        {"role": "user", "content": f"""
                            {context}

                            Извлеки только релевантные навыки из каждой вакансии ниже.

                            Текст вакансий:
                            {batch_text}

                            Верни **строго** JSON (без каких-либо пояснений!):
                            {{
                            "301": ["C++", "ООП", "STL", "CMake", "Linux"],
                            "302": ["Python", "FastAPI", "PostgreSQL", "Docker"]
                            }}
                        """}
                                            ],
                    options={"temperature": 0.0}
                )

                content = response['message']['content'].strip()
                
                json_match = re.search(r'(\{[\s\S]*\})', content)
                if json_match:
                    content = json_match.group(1)

                content = re.sub(r',\s*}', '}', content)
                content = re.sub(r',\s*]', ']', content)

                parsed = json.loads(content)

                for vid_str, skills in parsed.items():
                    try:
                        vid = int(re.search(r'\d+', str(vid_str)).group()) if isinstance(vid_str, str) else int(vid_str)
                        if isinstance(skills, list):
                            result[vid] = [s.strip() for s in skills if isinstance(s, str) and s.strip()]
                    except:
                        continue

                print(f"✓ Партия {i//batch_size + 1} ({len(batch)} вакансий) — OK")

            except Exception as e:
                print(f"Ошибка партии {i//batch_size + 1}: {e}")
                print(f"   → Ответ модели был: {repr(content[:1000])}")
                for vid, _ in batch:
                    result[vid] = []

        return result
    
    def register_user_request(self, tg_id: int, query: str, username: str = None, first_name: str = None):
        """Регистрирует пользователя и его запрос"""
        try:
            user, user_created = UniqueUser.objects.get_or_create(
                tg_id=tg_id,
                defaults={
                    'username': username or '',
                    'first_name': first_name or '',
                }
            )

            if user_created:
                print(f"Создан новый пользователь с tg_id = {tg_id}")

            profession, _ = Profession.objects.get_or_create(name=query)

            request_obj, request_created = UserProfessionRequest.objects.get_or_create(
                user=user,
                profession=profession,
            )

            if not request_created:
                request_obj.save()

            print(f"✅ Запрос '{query}' от пользователя {tg_id} успешно зарегистрирован")
            return user, profession, request_obj

        except Exception as e:
            print(f"❌ Критическая ошибка в register_user_request: {e}")
            raise
    
    def get_request_stats(self, query: str):
        """Возвращает, сколько раз этот запрос уже делали пользователи"""
        try:
            profession = Profession.objects.get(name=query)
            request_count = profession.user_requests.count()
            return request_count
        except Profession.DoesNotExist:
            return 0

    def _save_skills_to_vacancies(self, skills_dict: dict):
        for vacancy_pk, skills in skills_dict.items():

            try:
                vacancy_pk = int(vacancy_pk)
            except (ValueError, TypeError):
                print(f"[Save] Ошибка: vacancy_pk = {vacancy_pk} не является числом!")
                continue

            cleaned_skills = [s.strip() for s in skills if isinstance(s, str) and s.strip()]

            skills_objects = []
            for skill_name in cleaned_skills:
                skill, _ = Skill.objects.get_or_create(name=skill_name)
                skills_objects.append(skill)

            vacancy_obj = Vacancy.objects.filter(id=vacancy_pk).first()

            if vacancy_obj:
                vacancy_obj.skills.set(skills_objects)
                print(f"[Save] Вакансия {vacancy_pk}: сохранено {len(skills_objects)} навыков")
            else:
                print(f"[Save] Вакансия {vacancy_pk} не найдена")
    
    def _calculate_skill_stats(self, profession, user_request=None, area_id: int = None):
        queryset = Vacancy.objects.filter(profession=profession)

        if user_request:
            queryset = queryset.filter(user_request=user_request)

        if area_id:
            queryset = queryset.filter(areas__hh_id=area_id)

        stats = queryset.values('skills__name')\
                 .annotate(count=Count('skills__name'))\
                 .order_by('-count')[:15]

        print(f"[Stats] Подсчёт по {queryset.count()} вакансиям (регион {area_id}) | Найдено навыков: {len(stats)}")

        if queryset.count() == 0 and area_id:
            print(f"[DEBUG] Вакансий с area_id={area_id} не найдено. Проверяем наличие регионов:")
            for v in Vacancy.objects.filter(profession=profession)[:5]:
                areas = [a.hh_id for a in v.areas.all()]
                print(f"  Вакансия {v.id}: регионы {areas}")

        return [
            {"skill_name": item['skills__name'], "count": item['count']}
            for item in stats if item['skills__name']
        ]
    
    def get_average_salary(self, profession_name: str, area_id: int = None):
        """Считает среднюю зарплату"""
        profession = Profession.objects.get(name=profession_name)

        queryset = Vacancy.objects.filter(
            profession=profession,
            salary__isnull=False
        )

        if area_id:
            queryset = queryset.filter(areas__hh_id=area_id)

        result = queryset.aggregate(avg=Avg('salary'))
        avg_salary = result['avg']

        return round(avg_salary) if avg_salary is not None else None
     

    def get_all_vacancies(self, query: str, area_id: int = None, tg_id: int = None, username: str = None, first_name: str = None, is_automatic: bool = False, date_from: str = None):
        print(f"[Controller] Начало обработки '{query}' | area={area_id} | tg_id={tg_id}")

        hh_client = HHClient(user_agent=os.environ.get("USER_AGENT"))
                
        vacancy_dict = hh_client.fetch_vacancies(
            search_query=query,
            area=area_id,
            date_from=date_from
        )

        profession, _ = Profession.objects.get_or_create(name=query)

        user_request = None
        if tg_id:
            user, _ = UniqueUser.objects.get_or_create(
                tg_id=tg_id,
                defaults={'username': username, 'first_name': first_name}
            )
            user_request, _ = UserProfessionRequest.objects.get_or_create(
                user=user, profession=profession
            )

        skills_dict = {}
        new_vacancies_count = 0
        existing_vacancies_count = 0
        skipped_vacancies_count = 0

        for vacancy in vacancy_dict:
            vacancy_date_str = vacancy["published_at"]
            dt = parser.isoparse(vacancy_date_str)
            date_obj = dt.date()

            salary = None
            salary_data = vacancy.get("salary")
            if salary_data:
                f = salary_data.get("from")
                t = salary_data.get("to")
                if f is not None and t is not None:
                    salary = (f + t) // 2
                elif f is not None:
                    salary = f
                elif t is not None:
                    salary = t

            url = vacancy.get("alternate_url")
            if not url:
                continue

            vacancy_obj, created = Vacancy.objects.update_or_create(
                url=url,
                defaults={
                    'name': vacancy["name"],
                    'published_at': date_obj,
                    'salary': salary,
                    'profession': profession,
                    'user_request': user_request,
                }
            )

            added_count = 0

            if area_id:
                area_obj, _ = Area.objects.get_or_create(
                    hh_id=area_id,
                    defaults={'name': 'Запрошенный регион'}
                )
                vacancy_obj.areas.add(area_obj)
                added_count += 1

            area_data = vacancy.get("area")
            if area_data and isinstance(area_data, dict):
                hh_id = area_data.get("id")
                if hh_id and hh_id != area_id:
                    area_obj, _ = Area.objects.get_or_create(
                        hh_id=hh_id,
                        defaults={'name': area_data.get("name", "Неизвестно")}
                    )
                    vacancy_obj.areas.add(area_obj)
                    added_count += 1

            if added_count > 0:
                vacancy_obj.save()

            # Отладка
            areas_list = [a.name for a in vacancy_obj.areas.all()]
            print(f"[Vacancy] {vacancy_obj.name[:70]:70} → регионы: {areas_list} "
                  f"({'новая' if created else 'обновлена'})")

            needs_analysis = False

            if created:
                needs_analysis = True
                new_vacancies_count += 1
            else:
                skipped_vacancies_count += 1

            if needs_analysis:
                skills_raw = vacancy.get("snippet", {}).get("requirement")
                if skills_raw and isinstance(skills_raw, str) and len(skills_raw.strip()) > 10:
                    skills_dict[vacancy_obj.pk] = {
                        "requirement": skills_raw.strip(),
                        "name": vacancy.get("name", "")
                    }

        print(f"[Controller] Найдено: {len(vacancy_dict)} | Новых: {new_vacancies_count} | "
              f" | Пропущено: {skipped_vacancies_count}")

        if skills_dict:
            clean_skills_dict = self.ai_response(
                skills_dict, 
                query=query,
                is_automatic=is_automatic
            )
            self._save_skills_to_vacancies(clean_skills_dict)
        else:
            print("[AI] Нет вакансий, требующих анализа")

        print(f"[Controller] Найдено вакансий: {len(vacancy_dict)} | Новых: {new_vacancies_count} | Уже было: {existing_vacancies_count}")

        if skills_dict:
            clean_skills_dict = self.ai_response(skills_dict, query=query)
            self._save_skills_to_vacancies(clean_skills_dict)

        stats = self._calculate_skill_stats(profession, user_request, area_id)
        request_count = self.get_request_stats(query)
        avg_salary = self.get_average_salary(query, area_id)
        total_mentions = sum(item.get('count', 0) for item in stats)
        unique_skills = len(stats)

        result = {
            "success": True,
            "profession": query,
            "vacancies_parsed": len(vacancy_dict),
            "new_vacancies": new_vacancies_count,
            "skills_extracted": total_mentions,
            "unique_skills_count": unique_skills,
            "top_skills": stats[:15],
            "average_salary": avg_salary,
            "request_count": request_count
        }

        if not skills_dict:
            result["message"] = "Все вакансии уже были в базе. Статистика обновлена."

        return result