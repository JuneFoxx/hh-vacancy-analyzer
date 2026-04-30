from django.contrib import admin
from .models import Vacancy, Profession, Skill, UniqueUser, Area

admin.site.register(Vacancy)
admin.site.register(Profession)
admin.site.register(Skill)
admin.site.register(UniqueUser)
admin.site.register(Area)