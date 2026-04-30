from django.core.management.base import BaseCommand
from data.controller import DataVacancyController


class Command(BaseCommand):
    help = 'Удаляет вакансии старше N дней'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Удалять вакансии старше указанного количества дней (по умолчанию 30)'
        )

    def handle(self, *args, **options):
        days = options['days']

        self.stdout.write(self.style.WARNING(
            f"Запуск очистки вакансий старше {days} дней."
        ))

        controller = DataVacancyController()

        deleted = controller.clean_old_vacancies(days=days)
        self.stdout.write(self.style.SUCCESS(f"Успешно удалено {deleted} вакансий"))