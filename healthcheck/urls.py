from django.urls import path
from healthcheck import views

urlpatterns = [
    path('', views.generate_health_check_report, name='hello_world'),
]
