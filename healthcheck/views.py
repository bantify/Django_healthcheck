from django.shortcuts import render
import requests
from django.http import JsonResponse
from netmiko import ConnectHandler
import json
import re

# Create your views here.
def helloWorld(req):

    session_key = get_session_key("10.74.0.16","3paradm","StoreinAdmin4321!")

    gzp_3par_node_info = get_3par_node_info(session_key,"10.74.0.16")
    #print("gzp_3par_node_info:",gzp_3par_node_info)

    gzp_3par_cpg_info = get_3par_cpg_info(session_key,"10.74.0.16")

    gzp_3par_cage_info = get_3par_cage_info("10.74.0.16","3paradm","StoreinAdmin4321!")
    
    #print("gzp_3par_cage_info:",gzp_3par_cage_info)

    gzp_3par_disk_info = get_3par_disk_info("10.74.0.16","3paradm","StoreinAdmin4321!")

    #print("gzp_3par_disk_info:",gzp_3par_disk_info)

    gzp_3par_alarm_info = get_gzp_3par_alarm_info("10.74.0.16","3paradm","StoreinAdmin4321!")
    print("gzp_3par_alarm_info:",gzp_3par_alarm_info)

    degraded_cage_count = sum(
    1 for cage in gzp_3par_cage_info
    if cage.get("loopA") is None or cage.get("loopB") is None
    )
    degraded_disk_count = sum(
    1 for disk in gzp_3par_disk_info
    if disk.get("state") == "degraded" 
    )
    context = {"gzp_3par_node_info" : gzp_3par_node_info,
        "gzp_3par_cpg_info" : gzp_3par_cpg_info,
        "gzp_3par_cage_info" : gzp_3par_cage_info,
        "gzp_3par_disk_info": gzp_3par_disk_info,
        "degraded_cage_count": degraded_cage_count,
        "degraded_disk_count": degraded_disk_count,
        "gzp_3par_alarm_info": gzp_3par_alarm_info,}

    return render(req, "healthcheck.html", context)

def get_gzp_3par_alarm_info(host, username, password):
    conn = ConnectHandler(
        host=host,
        username=username,
        password=password,
        device_type="terminal_server",
        global_delay_factor=2,
        conn_timeout=30,
        banner_timeout=30,
        fast_cli=False
    )

    output = conn.send_command_timing("showalert")
    conn.disconnect()

    # ✅ Parse FULL output once
    alarms = parse_alerts(output)

    # ✅ Filter Major & Critical
    filtered = [
        a for a in alarms
        if a.get("Severity") in ["Major", "Critical"]
    ]

    return filtered

def parse_alerts(output):
    alerts = []

    blocks = output.strip().split("\n\n")

    for block in blocks:
        alert = {}
        for line in block.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                alert[key.strip()] = value.strip()

        if alert:  # avoid empty blocks
            alerts.append(alert)

    return alerts

def get_3par_disk_info(host,username,password):
    conn = ConnectHandler(host=host, username=username, password=password, device_type="terminal_server",global_delay_factor=2,conn_timeout=30,banner_timeout=30)
    output = conn.send_command_timing("showpd")
    conn.disconnect()
    cages = []

    for line in output.splitlines():
        parsed = parse_disk_line(line)
        if parsed:
            cages.append(parsed)
    return cages

def parse_disk_line(line):
    line = line.strip()

    # skip header / separator lines
    if not line or line.startswith("---") or line.startswith("Id"):
        return None

    parts = line.split()

    if len(parts) < 8:
        return None

    return {
        "id": parts[0],
        "cagePos": parts[1],
        "type": parts[2],
        "rpm": parts[3],
        "state": parts[4],
        "total": parts[5],
        "free": parts[6],
        "loopA": parts[7] if len(parts) > 7 else None,
        "loopB": parts[8] if len(parts) > 8 else None,
    }

def get_3par_cage_info(host,username,password):
    conn = ConnectHandler(host=host, username=username, password=password, device_type="terminal_server",global_delay_factor=2,conn_timeout=30,banner_timeout=30)
    output = conn.send_command_timing("showcage")
    conn.disconnect()
    cages = []

    for line in output.splitlines():
        parsed = parse_cpg_line(line)
        if parsed:
            cages.append(parsed)
    return cages

def parse_cpg_line(line):
    parts = re.split(r"\s+", line.strip())

    if len(parts) < 5 or parts[0].lower() == "id":
        return None

    return {
        "id": parts[0],
        "name": parts[1],
        "loopA": parts[2] if parts[2] != "---" else None,
        "loopB": parts[4] if parts[4] != "---" else None,
    }

def get_3par_node_info(session_key,host):
    url = f"https://{host}:8080/api/v1/system"
    response = requests.get(
            url,
            headers={
                "X-HP3PAR-WSAPI-SessionKey": session_key
            },
            verify=False
        )

    response.raise_for_status()

    data = response.json()

    return data


def get_3par_cpg_info(session_key,host):
    url = f"https://{host}:8080/api/v1/cpgs"
    response = requests.get(
            url,
            headers={
                "X-HP3PAR-WSAPI-SessionKey": session_key
            },
            verify=False
        )

    response.raise_for_status()

    data = response.json()

    return data

def get_session_key(host,username,password):
    url = f"https://{host}:8080/api/v1/credentials"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "user": username,
        "password": password
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=False  # same as curl -k
        )

        data = response.json()

        session_key = (
            data.get("key") or
            data.get("sessionKey") or
            data.get("credentials", {}).get("sessionKey")
        )

        return session_key

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


