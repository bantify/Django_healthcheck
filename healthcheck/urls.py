from django.urls import path
from healthcheck.views import GenerateHealthCheckReportView,GenerateHealthCheckPDFView

urlpatterns = [
    path('', GenerateHealthCheckReportView.as_view(), name='home'),
    path("pdf/", GenerateHealthCheckPDFView.as_view(), name="health_dashboard_pdf"),
]
