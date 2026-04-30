from rest_framework import serializers
from .models import Profession, Vacancy, Skill
from django.db.models import Count

class ProfessionSerializer(serializers.ModelSerializer):
    skill_stats = serializers.SerializerMethodField()

    class Meta:
        model = Profession
        fields = "__all__"

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = "__all__"

class VacancySerializer(serializers.ModelSerializer):
    skills = SkillSerializer()
    profession = ProfessionSerializer()
    
    class Meta:
        model = Vacancy
        fields = "__all__"