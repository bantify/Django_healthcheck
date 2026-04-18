import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

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
    ONEVIEW_DIR = Path("/var/log/healthcheck/oneview")
    F5_DIR = Path("/var/log/healthcheck/f5")
    VCENTER_DIR = Path("/var/log/healthcheck/vcenter")
    VM_DIR = Path("/var/log/healthcheck/vms")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --------------------------------------------------
        # Use NON-timezone-aware current time (as requested)
        # --------------------------------------------------
        LOCAL_TZ = ZoneInfo("Asia/Dhaka")

        date_part = self.request.GET.get("date")
        hour_part = self.request.GET.get("hour")

        if not date_part or not hour_part:
            now = datetime.now(tz=LOCAL_TZ)
            previous_hour = now - timedelta(hours=1)
            date_part = previous_hour.strftime("%Y-%m-%d")
            hour_part = previous_hour.strftime("%H")

        # now = datetime.now(tz=ZoneInfo("UTC")).astimezone(LOCAL_TZ)
        # previous_hour = now - timedelta(hours=1)
        #
        # date_part = previous_hour.strftime("%Y-%m-%d")
        # hour_part = previous_hour.strftime("%H")

        context["selected_date"] = date_part
        context["selected_hour"] = hour_part
        context["loaded_time"] = f"{date_part} {hour_part}:00"
        context["hours"] = [f"{h:02d}" for h in range(24)]
        context["today"] = datetime.now(tz=LOCAL_TZ).strftime("%Y-%m-%d")
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

                # ✅ Process each storage system
                for s in context["storage_data"]:
                    # -------- 3PAR CPG calculation --------
                    if s.get("type") == "3par" and "cpg" in s:
                        for cpg_name, cpg_data in s["cpg"].items():
                            total = cpg_data.get("total_mib", 0)
                            free = cpg_data.get("free_mib", 0)

                            if total > 0:
                                cpg_data["free_percent"] = round((free / total) * 100, 2)
                                cpg_data["used_percent"] = round(100 - cpg_data["free_percent"], 2)
                            else:
                                cpg_data["free_percent"] = 0
                                cpg_data["used_percent"] = 0

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

        # ================= F5 =================
        f5_file = f"f5_health_{date_part}_{hour_part}.json"
        f5_path = self.F5_DIR / f5_file

        context["f5_file"] = f5_file
        context["f5_data"] = []
        context["f5_file_exists"] = False
        context["f5_error"] = None

        try:
            if f5_path.exists():
                context["f5_data"] = json.loads(f5_path.read_text())
                context["f5_file_exists"] = True
            else:
                context["f5_error"] = "F5 health file not found."
        except Exception as e:
            context["f5_error"] = str(e)

        # ================= vcenter =================
        vcenter_file = f"vcenter_health_{date_part}_{hour_part}.json"
        vcenter_path = self.VCENTER_DIR / vcenter_file

        context["vcenter_file"] = vcenter_file
        context["vcenter_data"] = []
        context["vcenter_file_exists"] = False
        context["vcenter_error"] = None

        try:
            if vcenter_path.exists():
                context["vcenter_data"] = json.loads(vcenter_path.read_text())
                context["vcenter_file_exists"] = True

                for vc in context["vcenter_data"]:
                    for ds in vc["datastores_info"]["datastores"]:
                        if ds["capacity_gb"] > 0:
                            ds["free_percent"] = round(
                                (ds["free_space_gb"] / ds["capacity_gb"]) * 100,
                                2
                            )
                        else:
                            ds["free_percent"] = 0
            else:
                context["vcenter_error"] = "Vcenter health file not found."

        except Exception as e:
            context["vcenter_error"] = str(e)

        # ==================================================
        # VM HEALTH
        # ==================================================
        vm_filename = f"vm_health_{date_part}_{hour_part}.json"
        vm_file_path = self.VM_DIR / vm_filename

        context["vm_file"] = vm_filename
        context["vm_data"] = []
        context["vm_file_exists"] = False
        context["vm_error"] = None

        try:
            if vm_file_path.exists():
                with open(vm_file_path, "r") as f:
                    context["vm_data"] = json.load(f)
                # ================= VM HEALTH STATUS =================
                for vm in context["vm_data"]:

                    # 🚨 If metrics unavailable → CRITICAL
                    if vm.get("error"):
                        vm["health_status"] = "critical"
                        vm["max_fs_used_percent"] = 0
                        continue

                    cpu = vm.get("cpu_used_percent", 0)
                    memory = vm.get("memory_used_percent", 0)

                    fs_used_values = [
                        fs.get("used_percent", 0)
                        for fs in vm.get("filesystems", {}).values()
                    ]

                    max_fs_used = max(fs_used_values) if fs_used_values else 0
                    vm["max_fs_used_percent"] = max_fs_used

                    if cpu > 80 or memory > 80 or max_fs_used > 80:
                        vm["health_status"] = "critical"
                    elif cpu > 60 or memory > 60 or max_fs_used > 60:
                        vm["health_status"] = "warning"
                    else:
                        vm["health_status"] = "healthy"
                context["vm_file_exists"] = True
            else:
                context["vm_error"] = "VM health file not found."

        except json.JSONDecodeError:
            context["vm_error"] = "Invalid VM health JSON format."
        except Exception as e:
            context["vm_error"] = str(e)

        return context
