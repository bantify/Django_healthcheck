# influx_client.py
from influxdb import InfluxDBClient
from datetime import datetime
import pandas as pd
from prophet import Prophet

# --------------------------------
# InfluxDB v1.8.3 Configuration
# --------------------------------
INFLUX_HOST = "10.74.6.36"
INFLUX_PORT = 8086
INFLUX_DB = "telegraf"
INFLUX_USER = "enarban"
INFLUX_PASS = "enarban123"

# --------------------------------
# Create InfluxDB client
# --------------------------------
def get_influx_client():
    """
    Return an InfluxDB client connected to the configured DB.
    """
    return InfluxDBClient(
        host=INFLUX_HOST,
        port=INFLUX_PORT,
        username=INFLUX_USER,
        password=INFLUX_PASS,
        database=INFLUX_DB
    )

# --------------------------------
# Write service metrics
# --------------------------------
def write_service_point(
    client,
    service_id,
    success_cnt,
    fail_cnt,
    total_cnt,
    fail_percent,
    status,
    timestamp=None
):
    """
    Write a single service metric to InfluxDB.

    Args:
        client: InfluxDBClient instance
        service_id: integer
        service_name: string
        success_cnt: integer
        fail_cnt: integer
        total_cnt: integer
        fail_percent: float
        status: integer (1=OK, 0=FAIL)
        timestamp: datetime object (optional, defaults to now UTC)
    """
    if timestamp is None:
        timestamp = datetime.utcnow()

    insert_minute = timestamp.strftime("%H:%M")

    json_body = [
        {
            "measurement": "service_data",
            "tags": {
                "service_id": str(service_id)
            },
            "time": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fields": {
                "success_cnt": int(success_cnt),
                "fail_cnt": int(fail_cnt),
                "total_cnt": int(total_cnt),
                "fail_percent": float(fail_percent),
                "status": int(status),       # 1 = OK, 0 = FAIL
                "insert_date": timestamp.strftime("%Y-%m-%d"),  # additional field
                "insert_min": insert_minute
            }
        }
    ]

    client.write_points(json_body)




# --------------------------------

# Predict next-day fail_percent

# --------------------------------

def get_next_day_fail_percent(

    client,

    service_id,

    timestamp=None

):

    """

    Predict fail_percent for the **next day** for a specific service_id 

    and insert_min (taken from timestamp).



    Returns:

        dict: {'ds': date, 'yhat': float, 'yhat_lower': float, 'yhat_upper': float}

    """



    if timestamp is None:

        timestamp = datetime.now()



    insert_minute = timestamp.strftime("%H:%M")



    query = f"""

        SELECT MEAN(fail_percent) AS fail_percent

        FROM service_data

        WHERE status = 1

          AND service_id = '{service_id}'

          AND insert_min = '12:15'

          AND time >= now() - 30d

        GROUP BY time(1d) fill(null)

        ORDER BY time ASC

    """



    #print("Query =", query)



    result = client.query(query)

    points = list(result.get_points(measurement="service_data"))



    df = pd.DataFrame(points)



    if df.empty:

        print("No data found for Prophet")

        return None



    # Prophet formatting

    df = df.rename(columns={"time": "ds", "fail_percent": "y"})

    df["ds"] = pd.to_datetime(df["ds"]).dt.tz_localize(None)

    df["y"] = pd.to_numeric(df["y"], errors="coerce")

    df = df.dropna().sort_values("ds").reset_index(drop=True)



    if len(df) < 5:

        print("Not enough data points for prediction")

        return None



    # Fit Prophet

    model = Prophet(daily_seasonality=True)

    model.fit(df)



    # Make future DataFrame for 1 day

    future = model.make_future_dataframe(periods=1, freq="D")

    forecast = model.predict(future)



    # Keep only the **next day prediction**

    last_history_date = df["ds"].max()

    next_day_forecast = forecast[forecast["ds"] > last_history_date].iloc[0]



    return {

        "ds": next_day_forecast["ds"],

        "yhat": next_day_forecast["yhat"],

        "yhat_lower": next_day_forecast["yhat_lower"],

        "yhat_upper": next_day_forecast["yhat_upper"]

    }