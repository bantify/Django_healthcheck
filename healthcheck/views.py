import json
from datetime import timedelta
from pathlib import Path

from django.utils import timezone

from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.generic import TemplateView


class GenerateHealthCheckReportView(LoginRequiredMixin, TemplateView):
    template_name = "healthcheck/home.html"
    STORAGE_DIR = Path("/var/log/healthcheck/storage")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Current time (timezone-aware)
        now = timezone.now()

        # Previous hour
        previous_hour_time = now - timedelta(hours=1)

        # Build filename
        filename = (
            f"storage_health_"
            f"{previous_hour_time.strftime('%Y-%m-%d')}_"
            f"{previous_hour_time.strftime('%H')}.json"
        )

        file_path = self.STORAGE_DIR / filename

        # Default values
        context["storage_data"] = {}
        context["storage_file"] = filename
        context["storage_file_exists"] = False
        context["storage_error"] = None

        # Load JSON safely
        try:
            if file_path.exists():
                with open(file_path, "r") as f:
                    context["storage_data"] = json.load(f)
                context["storage_file_exists"] = True
            else:
                context["storage_error"] = "Health check file not found."

        except json.JSONDecodeError:
            context["storage_error"] = "Invalid JSON format."

        except Exception as e:
            context["storage_error"] = str(e)
        print(context)
        return context
