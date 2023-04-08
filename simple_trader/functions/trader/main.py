import functions_framework
import requests
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import dateutil.parser
import time
import sys
import hmac
from secret import Secrets
from google.cloud import bigquery
import google.cloud.logging
 
 
logging.basicConfig(
        format = "[%(asctime)s][%(levelname)s] %(message)s",
        level = logging.DEBUG
    )
logger = logging.getLogger()
 
logging_client = google.cloud.logging.Client()
logging_client.setup_logging()
 
logger.setLevel(logging.DEBUG)


def get_my_jpy():
    apiKey = Secrets.gmo_api_key()
    secretKey = Secrets.gmo_api_secret()
    timestamp = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
    method    = 'GET'
    endPoint  = 'https://api.coin.z.com/private'
    path      = '/v1/account/assets'

    text = timestamp + method + path
    sign = hmac.new(bytes(secretKey.encode('ascii')), bytes(text.encode('ascii')), hashlib.sha256).hexdigest()

    headers = {
        "API-KEY": apiKey,
        "API-TIMESTAMP": timestamp,
        "API-SIGN": sign
    }

    res = requests.get(endPoint + path, headers=headers)
    json_resp = res.json()
    data = json_resp["data"]
    for d in data:
        if d["symbol"] == "JPY":
            return int(d["available"])
    return None


@functions_framework.cloud_event
def subscribe(cloud_event):
    # 買い付け余力を確認
    jpy = get_my_jpy()
    if jpy < 100000:
        logger.warning("low jpy: " + str(jpy))
        return 

    public_api_endpoint = "https://api.coin.z.com/public"
    trades_path = "/v1/trades?symbol=ETH"

    response = requests.get(public_api_endpoint + trades_path)
    json_resp = response.json()
    if response.status_code != 200 or json_resp.get("data", None) is None:
        logger.error(response.status_code)
        logger.error(response.text)
        return
    
    trades_log = json_resp["data"].get("list", None)
    if trades_log is None:
        logger.error("response 'list' is None")
        logger.error(response.text)
        return

    is_buy_result = is_buy(trades_log)
    logger.info(is_buy_result)

    send_bq(datetime.now(tz=ZoneInfo("Asia/Tokyo")), trades_log[0]["price"], is_buy_result)
    pass


def send_bq(time, price, buy):

    client = bigquery.Client()
    client = bigquery.Client(project=Secrets.gcp_project_id())

    table = client.get_table(Secrets.bq_table_id())

    rows_to_insert = [{"time": time, "price": price, "buy": buy}]

    errors = client.insert_rows(table, rows_to_insert)

    if errors == []:
        logger.info("New rows have been added.")
    else:
        logger.error(errors)


def is_buy(trades_log:list):
    if len(trades_log) < 90:
        logger.info("trades_log size error:" + len(trades_log))
        return False
    
    latest = trades_log[0]
    price_carry = latest["price"]
    time_carry = dateutil.parser.parse(latest["timestamp"])
    cnt = 0
    for trade in trades_log:
        cnt = cnt + 1
        if latest["timestamp"] == trade["timestamp"]:
            continue
        # 上がり傾向である事を確認
        if price_carry > trade["price"]:
            price_carry = trade["price"]
            time_carry = dateutil.parser.parse(trade["timestamp"])
        else:
            break

    time_diff= dateutil.parser.parse(latest["timestamp"]) - time_carry
    time_diff_sec = time_diff.total_seconds()
    price_diff = float(latest["price"]) - float(price_carry)

    logger.info(f"time_diff: ${time_diff_sec}, price_diff: ${price_diff}")

    if cnt < 5 or time_diff_sec < 10.0:
        return False

    return 1000.0 / 600.0 < price_diff / time_diff_sec


def main():
    subscribe(None)


if __name__ == "__main__":
    main()