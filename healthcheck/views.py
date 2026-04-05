from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView


# Create your views here.
@login_required
def generate_health_check_report(req):
    context = {}
    return render(req, "healthcheck/healthcheck.html", context)


class GenerateHealthCheckReportView(LoginRequiredMixin, TemplateView):
    template_name = "healthcheck/healthcheck.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["example"] = "value"
        return context