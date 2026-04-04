from django.shortcuts import render
import requests
from django.http import JsonResponse
from netmiko import ConnectHandler
import json
import re

# Create your views here.
@login_required
def generate_health_check_report(req):

    context = {}

    return render(req, "healthcheck/healthcheck.html", context)

