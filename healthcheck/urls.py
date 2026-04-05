from django.urls import path
from healthcheck.views import GenerateHealthCheckReportView

urlpatterns = [
    path('', GenerateHealthCheckReportView.as_view(), name='hello_world'),
]
