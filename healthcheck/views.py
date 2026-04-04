from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required
def generate_health_check_report(req):
    context = {}
    return render(req, "healthcheck/healthcheck.html", context)
