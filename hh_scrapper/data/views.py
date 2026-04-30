from rest_framework.viewsets import ModelViewSet
from .serializers import ProfessionSerializer
from .models import Profession, Vacancy
from .controller import DataVacancyController
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count, Q, Avg

class DataViewSet(ModelViewSet):
    queryset = Profession.objects.all()
    serializer_class = ProfessionSerializer

    @action(detail=False, methods=['POST'], url_path='parse')
    def parse_vacancies(self, request):
        query = request.data.get("name")
        tg_id = request.data.get("tg_id")
        username = request.data.get("username")
        first_name = request.data.get("first_name")
        area_id = request.data.get("area_id")

        print(f"[ViewSet] Получен запрос: name='{query}', tg_id={tg_id}, username={username}, area_id={area_id}")

        if not query:
            return Response({"error": "Поле 'name' обязательно"}, status=400)

        if not tg_id:
            return Response({"error": "Поле 'tg_id' обязательно"}, status=400)

        try:
            tg_id = int(tg_id)
        except (TypeError, ValueError):
            return Response({"error": "tg_id должен быть числом"}, status=400)

        controller = DataVacancyController()

        try:
            result = controller.get_all_vacancies(
                query=query,
                tg_id=tg_id,
                username=username,
                first_name=first_name,
                area_id=area_id
            )

            return Response(result, status=201)

        except Exception as e:
            print(f"[ViewSet] Ошибка при обработке: {e}")
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['POST'], url_path='area')
    def check_area(self, request):
        area_name = request.data.get("area_name")

        print(f"[ViewSet] Получен запрос: area_name={area_name}")

        try:
            area_name = str(area_name)
        except (TypeError, ValueError):
            return Response({"error": "area_name должен быть строкой"}, status=400)

        controller = DataVacancyController()

        try:
            result = controller.get_area_id_by_name(
                area_name=area_name
            )

            if result is None:
                return Response({"error": "Данного региона не существует"}, status=400)

            return Response(result, status=201)

        except Exception as e:
            print(f"[ViewSet] Ошибка при обработке: {e}")
            return Response({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['POST'], url_path='search_by_skills')
    def search_by_skills(self, request):
        skills = request.data.get("skills", [])
        area_id = request.data.get("area_id")

        if not skills or not area_id:
            return Response({"error": "skills и area_id обязательны"}, status=400)

        skills = list(set([s.strip() for s in skills if s.strip()]))
        skill_count = len(skills)

        if skill_count == 0:
            return Response({"error": "Список навыков пуст"}, status=400)

        queryset = Vacancy.objects.filter(
            areas__hh_id=area_id
        ).distinct()

        queryset = queryset.annotate(
            matching_skills=Count('skills', filter=Q(skills__name__in=skills))
        )

        queryset = queryset.filter(matching_skills=skill_count)

        top_vacancies = queryset.order_by('-salary')[:10]

        avg_salary_result = queryset.aggregate(avg=Avg('salary'))
        avg_salary = avg_salary_result['avg']

        data = [
            {
                "name": v.name,
                "url": v.url,
                "salary": v.salary
            }
            for v in top_vacancies
        ]

        return Response({
            "success": True,
            "total_found": queryset.count(),
            "average_salary": round(avg_salary) if avg_salary is not None else None,
            "vacancies": data
        })