from django.core.management.base import BaseCommand
from data.models import Area
from data.client_hh import HHClient
from dotenv import load_dotenv
import os

class Command(BaseCommand):
    help = 'Загружает все регионы HH.ru в базу'

    def handle(self, *args, **options):
        load_dotenv()
        
        self.stdout.write("Загрузка регионов HH.ru...")

        hh = HHClient(os.environ.get("USER_AGENT"))
        areas_data = hh.get_areas()

        def save_areas(area_list, parent=None):
            for area in area_list:
                obj, created = Area.objects.update_or_create(
                    hh_id=area['id'],
                    defaults={
                        'name': area['name'],
                        'parent': parent
                    }
                )
                if created:
                    self.stdout.write(f"  + {area['name']}")
                else:
                    self.stdout.write(f"  ~ {area['name']}")

                if 'areas' in area and area['areas']:
                    save_areas(area['areas'], obj)

        save_areas(areas_data)
        self.stdout.write(self.style.SUCCESS("Регионы успешно загружены!"))