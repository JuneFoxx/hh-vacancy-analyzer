from django.core.management.base import BaseCommand
from data.controller import DataVacancyController
from datetime import datetime, timedelta
import time


class Command(BaseCommand):
    help = 'Собирает вакансии через множество разных запросов (обход лимита 2000)'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7)
        parser.add_argument('--area', type=int, default=None)

    def handle(self, *args, **options):
        days = options['days']
        area_id = options['area']
        controller = DataVacancyController()

        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        self.stdout.write(self.style.SUCCESS(
            f"[{datetime.now()}] Запуск сбора вакансий за период с {date_from} ({days} дней)"
        ))

        queries = [
            "",
            "Python", "Java", "JavaScript", "C++", "C#", "Go", "PHP", "1C", "Ruby", "Kotlin",
            "Frontend", "Backend", "Fullstack", "DevOps", "Data Scientist", "Data Engineer",
            "Аналитик", "Менеджер", "Тестировщик", "Программист", "Разработчик",
            "Системный администратор", "Системный аналитик", "Product Manager",
            "a", "б", "в", "г", "д", "е", "ж", "з", "и", "к", "л", "м", "н", "о", "п", "р", "с", "т"
        ]

        total_vacancies = 0
        total_new = 0

        for i, query in enumerate(queries, 1):
            display = "ПУСТОЙ" if query == "" else query
            self.stdout.write(f"[{i}/{len(queries)}] Запрос: '{display}'")

            try:
                result = controller.get_all_vacancies(
                    query=query,
                    area_id=area_id,
                    tg_id=None,
                    is_automatic=True,
                    date_from=date_from
                )

                vacancies = result.get("vacancies_parsed", 0)
                new_vac = result.get("new_vacancies", 0)

                total_vacancies += vacancies
                total_new += new_vac

                self.stdout.write(self.style.SUCCESS(
                    f"   ✓ {vacancies} вакансий (новых: {new_vac})"
                ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ✗ Ошибка: {e}"))

            time.sleep(2.0)  # пауза

        self.stdout.write(self.style.SUCCESS(
            f"\nСбор завершён!\n"
            f"Всего собрано: {total_vacancies} вакансий\n"
            f"Из них новых: {total_new}"
        ))