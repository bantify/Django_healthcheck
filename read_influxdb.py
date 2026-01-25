from datetime import datetime, timedelta
from influx_client import get_influx_client,get_prediction_fail_percent
import pytz

influx_client = get_influx_client()

service_id=1
tz = pytz.timezone("Asia/Dhaka")
insert_at = datetime.now(tz)
future_days = 7
forcast = get_prediction_fail_percent(influx_client,service_id,insert_at,future_days)
print(forcast)