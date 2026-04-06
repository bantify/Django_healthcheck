import json
from datetime import timedelta
from pathlib import Path

from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class GenerateHealthCheckReportView(LoginRequiredMixin, TemplateView):
    template_name = "healthcheck/home.html"

    STORAGE_DIR = Path("/var/log/healthcheck/storage")
    SWITCH_DIR = Path("/home/infraadmin/healthcheck")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Current time (timezone-aware)
        now = timezone.now()

        # Previous hour
        previous_hour_time = now - timedelta(hours=1)

        date_part = previous_hour_time.strftime("%Y-%m-%d")
        hour_part = previous_hour_time.strftime("%H")

        # ==========================
        # STORAGE HEALTH FILE
        # ==========================
        storage_filename = f"storage_health_{date_part}_{hour_part}.json"
        storage_file_path = self.STORAGE_DIR / storage_filename

        context["storage_data"] = []
        context["storage_file"] = storage_filename
        context["storage_file_exists"] = False
        context["storage_error"] = None

        try:
            if storage_file_path.exists():
                with open(storage_file_path, "r") as f:
                    context["storage_data"] = json.load(f)
                context["storage_file_exists"] = True
            else:
                context["storage_error"] = "Storage health file not found."
        except json.JSONDecodeError:
            context["storage_error"] = "Invalid storage JSON format."
        except Exception as e:
            context["storage_error"] = str(e)

        # ==========================
        # SWITCH HEALTH FILE
        # ==========================
        switch_filename = f"switch_health_{date_part}_{hour_part}.json"
        switch_file_path = self.SWITCH_DIR / switch_filename

        context["switch_data"] = []
        context["switch_file"] = switch_filename
        context["switch_file_exists"] = False
        context["switch_error"] = None

        try:
            if switch_file_path.exists():
                with open(switch_file_path, "r") as f:
                    context["switch_data"] = json.load(f)
                context["switch_file_exists"] = True
            else:
                context["switch_error"] = "Switch health file not found."
        except json.JSONDecodeError:
            context["switch_error"] = "Invalid switch JSON format."
        except Exception as e:
            context["switch_error"] = str(e)

        return context