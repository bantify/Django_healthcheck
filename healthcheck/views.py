import json
from datetime import datetime, timedelta
from pathlib import Path

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class GenerateHealthCheckReportView(LoginRequiredMixin, TemplateView):
    """
    Dashboard view that loads:
    - Storage health (VNX / Unity / 3PAR)
    - Switch health (HP / Extreme)
    - OneView health (Enclosures / Servers)
    Using the previous-hour JSON files.
    """

    template_name = "healthcheck/home.html"

    # Base directories
    STORAGE_DIR = Path("/var/log/healthcheck/storage")
    SWITCH_DIR = Path("/var/log/healthcheck/switch")
    ONEVIEW_DIR = Path("var/log/healthcheck/oneview")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --------------------------------------------------
        # Use NON-timezone-aware current time (as requested)
        # --------------------------------------------------
        now = datetime.now()
        previous_hour = now - timedelta(hours=1)

        date_part = previous_hour.strftime("%Y-%m-%d")
        hour_part = previous_hour.strftime("%H")

        # ==================================================
        # STORAGE
        # ==================================================
        storage_filename = f"storage_health_{date_part}_{hour_part}.json"
        storage_file_path = self.STORAGE_DIR / storage_filename

        context["storage_file"] = storage_filename
        context["storage_data"] = []
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

        # ==================================================
        # SWITCH
        # ==================================================
        switch_filename = f"switch_health_{date_part}_{hour_part}.json"
        switch_file_path = self.SWITCH_DIR / switch_filename

        context["switch_file"] = switch_filename
        context["switch_data"] = []
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

        # ==================================================
        # ONEVIEW
        # ==================================================
        oneview_filename = f"oneview_health_{date_part}_{hour_part}.json"
        oneview_file_path = self.ONEVIEW_DIR / oneview_filename

        context["oneview_file"] = oneview_filename
        context["oneview_data"] = []
        context["oneview_file_exists"] = False
        context["oneview_error"] = None

        try:
            if oneview_file_path.exists():
                with open(oneview_file_path, "r") as f:
                    context["oneview_data"] = json.load(f)
                context["oneview_file_exists"] = True
            else:
                context["oneview_error"] = "OneView health file not found."
        except json.JSONDecodeError:
            context["oneview_error"] = "Invalid OneView JSON format."
        except Exception as e:
            context["oneview_error"] = str(e)

        return context