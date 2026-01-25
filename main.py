import importlib
import glob
from tabulate import tabulate
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch, ElasticsearchWarning
import warnings
from influx_client import get_influx_client, write_service_point,get_next_day_fail_percent
import pytz
import subprocess

SERVICE_KEYS = {
    1: {
        "CRIT": "total_bssapi_api_CRIT",
        "MAJ":  "total_bssapi_api_MAJ",
    },
    2: {
        "CRIT": "orders_api_CRIT",
        "MAJ":  "orders_api_MAJ",
    },
    3: {
        "CRIT": "credit_decisions_api_CRIT",
        "MAJ":  "credit_decisions_api_MAJ",
    },
    4: {
        "CRIT": "pack_purchase_api_CRIT",
        "MAJ":  "pack_purchase_api_MAJ",
    },
    5: {
        "CRIT": "available_products_api_CRIT",
        "MAJ":  "available_products_api_MAJ",
    },
    6: {
        "CRIT": "scratch_card_api_CRIT",
        "MAJ":  "scratch_card_api_MAJ",
    },
    7: {
        "CRIT": "provisioning_cs_api_CRIT",
        "MAJ":  "provisioning_cs_api_MAJ",
    },
    8: {
        "CRIT": "balance_api_CRIT",
        "MAJ":  "balance_api_MAJ",
    },
    9: {
        "CRIT": "usage_api_CRIT",
        "MAJ":  "usage_api_MAJ",
    },
    10: {
        "CRIT": "combined_usage_api_CRIT",
        "MAJ":  "combined_usage_api_MAJ",
    },
    11: {
        "CRIT": "crc_error_CRIT",
    },
    12: {
        "CRIT": "name_resolve_CRIT",
    },
    13: {
        "MAJ": "smpp_error_MAJ",
    },
}

LEVEL_MAP = {
    2: "CRIT",   # diff > 20
    1: "MAJ",    # diff > 10
}

CRITICAL_THRESHOLD = 20.0
MAJOR_THRESHOLD = 10.0
# -------------------------------
# Suppress Elasticsearch warnings
# -------------------------------
warnings.filterwarnings("ignore", category=ElasticsearchWarning)

# -------------------------------
# Connect to Elasticsearch
# -------------------------------
def connect_es(hosts):
    return Elasticsearch(
        hosts,
        request_timeout=60,
        max_retries=3,
        retry_on_timeout=True
    )

# -------------------------------
# Time filter for ES queries
# -------------------------------
def time_filter(window_start, window_end):
    return {
        "range": {
            "@timestamp": {
                "gte": window_start,
                "lte": window_end
            }
        }
    }

# -------------------------------
# Build success and error queries
# -------------------------------
def build_queries(filters, success_range=(200, 299), error_range=(400, 599)):
    success_query = {
        "query": {
            "bool": {
                "must": filters + [
                    {"range": {"rescode": {"gte": success_range[0], "lte": success_range[1]}}}
                ]
            }
        }
    }

    error_query = {
        "query": {
            "bool": {
                "must": filters + [
                    {"range": {"rescode": {"gte": error_range[0], "lte": error_range[1]}}}
                ]
            }
        }
    }
    return success_query, error_query

# -------------------------------
# Count documents in ES
# -------------------------------
def get_count(es, index_name, query):
    return es.count(index=index_name, body=query)["count"]

# -------------------------------
# Load all services dynamically
# -------------------------------
def load_services():
    services = []
    for file in glob.glob("services/*.py"):
        mod_name = file.replace("/", ".").replace(".py", "")
        mod = importlib.import_module(mod_name)
        services.append(mod)

    services.sort(key=lambda x: x.SERVICE_ID)
    return services

# -------------------------------
# Main logic
# -------------------------------
def main():
    fetch_time = datetime.now() - timedelta(minutes=5)

    es = connect_es(["http://10.74.10.217:9200"])
    influx_client = get_influx_client()

    index_name = "classicapps-*"
    tf = time_filter("now-10m", "now-5m")
    tz = pytz.timezone("Asia/Dhaka")
    insert_at = datetime.now(tz)  # keep as datetime object
    services = load_services()

    table_data = [
        ["Service ID", "Service Name", "Success", "Fail", "Total", "Fail %", "Insert At"]
    ]

    for svc in services:
        try:
            # ------------------------
            # Services with get_counts()
            # ------------------------
            if hasattr(svc, "get_counts"):
                success_cnt, fail_cnt = svc.get_counts(fetch_time)

            # ------------------------
            # SPECIAL ES services
            # ------------------------
            elif getattr(svc, "SPECIAL", False):
                success_query = {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"log.file.path.keyword": svc.LOG_PATH}},
                                {"match_phrase": {"message": "result OK"}},
                                tf
                            ]
                        }
                    }
                }

                error_query = {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"log.file.path.keyword": svc.LOG_PATH}},
                                {"match_phrase": {"message": "result ERROR"}},
                                tf
                            ]
                        }
                    }
                }

                success_cnt = get_count(es, index_name, success_query)
                fail_cnt = get_count(es, index_name, error_query)

            # ------------------------
            # Normal ES services
            # ------------------------
            else:
                filters = [{"term": {"log.file.path.keyword": svc.LOG_PATH}}]

                if getattr(svc, "METHOD", None):
                    filters.append({"term": {"request_type.keyword": f'"{svc.METHOD}'}})

                if getattr(svc, "URIPATH", None):
                    if "*" in svc.URIPATH:
                        filters.append({"wildcard": {"URIpath.keyword": svc.URIPATH}})
                    else:
                        filters.append({"term": {"URIpath.keyword": svc.URIPATH}})

                if getattr(svc, "WILDCARD", None):
                    for wc in svc.WILDCARD:
                        filters.append({"wildcard": {"URIpath.keyword": wc}})

                filters.append(tf)

                success_query, error_query = build_queries(filters)
                success_cnt = get_count(es, index_name, success_query)
                fail_cnt = get_count(es, index_name, error_query)

            # ------------------------
            # Final calculation
            # ------------------------
            total_cnt = success_cnt + fail_cnt
            fail_percent = (fail_cnt / total_cnt * 100) if total_cnt else 0.0
            status = 1

            # Get next-day prediction
            prediction = get_next_day_fail_percent(influx_client, svc.SERVICE_ID, insert_at)
            print("Actual Fail %:", fail_percent)

            if prediction:
              predicted_fail = prediction["yhat"]
              print(f"Service ID: {svc.SERVICE_ID} Actual Failure %: {fail_percent}, Predicted Failure %: {prediction['yhat']:.3f}" )
              diff = fail_percent - predicted_fail

              if diff > 20:
                level = 2   # CRITICAL
              elif diff > 10:
                level = 1   # MAJOR
              else:
                level = 0   # CLEAR

              key = get_zabbix_key(svc.SERVICE_ID, level)

              if key:
                send_zabbix(key, 1)
              else:
                # clear both CRIT & MAJ if needed
                for sev in ("CRIT", "MAJ"):
                  k = SERVICE_KEYS.get(svc.SERVICE_ID, {}).get(sev)
                  if k:
                    send_zabbix(k, 0)



              
            else:
              print("Prediction could not be generated")
            # ------------------------
            # Write to InfluxDB
            # ------------------------
            write_service_point(
                influx_client,
                svc.SERVICE_ID,
                success_cnt,
                fail_cnt,
                total_cnt,
                fail_percent,
                status,
                insert_at
            )

            table_data.append([
                svc.SERVICE_ID,
                svc.SERVICE_NAME,
                success_cnt,
                fail_cnt,
                total_cnt,
                f"{fail_percent:.2f}%",
                insert_at
            ])

        except Exception as e:
            print(f"[Service {svc.SERVICE_ID}] ERROR: {e}")

    print(tabulate(table_data, headers="firstrow", tablefmt="grid"))

def get_zabbix_key(service_id, level):
    severity = LEVEL_MAP.get(level)
    if not severity:
        return None

    return SERVICE_KEYS.get(service_id, {}).get(severity)


def send_zabbix_alarm(service_id, level,value):
    if service_id == 1 and level == 1:
      key = "total_bssapi_api_CRIT"
    if service_id == 1 and level == 2:
      key = "total_bssapi_api_MAJ"
    if service_id == 2 and level == 1:
      key = "orders_api_CRIT"
    if service_id == 2 and level == 2:
      key = "orders_api_MAJ"

    subprocess.run([
        "zabbix_sender",
        "-z", "172.16.7.185",
        "-s", "metroc-p-qv-installserver2",
        "-k", key,
        "-o", str(value)
    ], check=False)

# -------------------------------
# Run main
# -------------------------------
if __name__ == "__main__":
    main()