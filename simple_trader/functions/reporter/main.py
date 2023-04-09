import functions_framework
import requests
from datetime import datetime, timedelta, timezone
import hashlib
import time
import sys
import hmac
from secret import Secrets
from google.cloud import bigquery
import matplotlib.pyplot as plt
from discordwebhook import Discord


query = """
    SELECT * FROM `{id}`
    WHERE time BETWEEN '{since}' AND '{until}'
    ORDER BY time
    LIMIT 2000
"""
test_query = """
    SELECT * FROM `bigquery-public-data.crypto_ethereum.balances`
    LIMIT 2
"""
#    LIMIT 1860


@functions_framework.cloud_event
def subscribe(cloud_event):
    client = bigquery.Client(Secrets.gcp_project_id())

    now = datetime.now() - timedelta(hours=15) # 嘘 UTC
    yesterday = now - timedelta(days=1)
    q = query.format(id=Secrets.bq_table_id(), since=yesterday, until=now)
    print(q)
    query_job = client.query(q)

    fig = plt.figure(figsize=(16, 8), dpi=72)
    ax = fig.add_subplot(111, xlabel="time", ylabel="price")
    all_count = 0
    buy_count = 0
    not_buy_time = []
    not_buy_price = []
    buy_log = []
    for r in query_job:
        all_count = all_count + 1
        if r.get("buy") is True:
            buy_count = buy_count + 1
            ax.scatter(r.get("time"), r.get("price"), marker="o", color="#FF0000", zorder=2)
            buy_log.append(r)
        else:
            not_buy_time.append(r.get("time"))
            not_buy_price.append(r.get("price"))

    ax.plot(not_buy_time, not_buy_price, zorder=1)

    log_str = "```"
    c = 0
    for x in buy_log:
        if c % 5 == 0:
            log_str = log_str + "\n"
        log_str = log_str + x.get("time").strftime("(%H:%M") + "," + str(x.get("price")) + ") "
        c = c + 1
    log_str = log_str + "\n```\n"
    log_str = log_str + f"{buy_count} / {all_count}"

    discord = Discord(url=Secrets.get_discord_url())
    image_file_name = "image.png"
    fig.savefig(image_file_name)
    with open(image_file_name, "rb") as img:
        discord.post(content=log_str, file={"attachment": img})


def main():
    subscribe(None)


if __name__ == "__main__":
    main()