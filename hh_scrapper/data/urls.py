from rest_framework.routers import DefaultRouter
from .views import DataViewSet
from django.urls import path
router = DefaultRouter()
router.register(r'professions', DataViewSet, basename='professions')

urlpatterns = router.urls

