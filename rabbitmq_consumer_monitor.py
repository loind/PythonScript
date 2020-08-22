#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
            _|\ _/|_,
          ,((\\``-\\\\_
        ,(())      `))\
      ,(()))       ,_ \
     ((())'   |        \
     )))))     >.__     \
     ((('     /    `-. .c|
     (('     /        `-`'
    Author: LoiND
    Company: MobioVN
    Date created: 29/08/2019
"""
import json
import platform
from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth


class StatusIssues:
    WARNING = 0
    ERROR = 1
    PASS = 2


def send_to_slack(status_issues, content):
    slack_url = "https://hooks.slack.com/services/xxxxxxxx/xxxxxxxxx"

    color = ""
    if status_issues == StatusIssues.WARNING:
        color = "#ffae42"
    elif status_issues == StatusIssues.ERROR:
        color = "#ff0000"
    elif status_issues == StatusIssues.PASS:
        color = "#46B886"

    payload = {
        "attachments": [
            {
                "text": content,
                "color": color,
                "fields": [
                    {"title": "Date", "value": str(datetime.now()), "short": True},
                    {"title": "Host", "value": platform.node(), "short": True}
                ]
            }
        ]
    }
    requests.post(url=slack_url, json=payload)


LIST_IGNORED = ["celery"]

if __name__ == '__main__':
    rabbitmq_host = "rabbitmq-server:15672"
    header = {
        'content-type': 'application/json'
    }
    url = "http://%s/api/queues" % rabbitmq_host

    response = requests.get(url, headers=header, auth=HTTPBasicAuth('user', 'pass'))
    results = ""
    content_file = open('~/rabbitmq.log', 'r+')
    data_saved = content_file.read()

    dict_consumers = {}
    if data_saved:
        dict_consumers = json.loads(data_saved)

    warning_content = ""
    pass_content = ""
    for queue in response.json():
        num_consumers = int(queue.get('consumers', 0))
        queue_name = queue.get('name')
        key_num_alert = "%s_%s" % (queue_name, "num-alert")
        key_message_count = "%s_%s" % (queue_name, "count")

        if queue_name in LIST_IGNORED:
            continue

        cache_number = dict_consumers.get(queue_name)
        if cache_number:
            num_alert = dict_consumers.get(key_num_alert, 0)

            if num_consumers >= cache_number:
                dict_consumers[queue_name] = num_consumers
                if num_alert > 0:
                    if len(pass_content) > 0:
                        pass_content = "%s\n" % pass_content
                    pass_content = "%s --- healing to %s" % (queue_name, num_consumers)
                num_alert = 0

            elif num_consumers < cache_number:
                if num_alert < 5:
                    if len(warning_content) > 0:
                        warning_content = "%s\n" % warning_content
                    num_alert = num_alert + 1
                    warning_content = "%s --- down from %s to %s" % (queue_name, cache_number, num_consumers)

            dict_consumers[key_num_alert] = num_alert

        else:
            dict_consumers[queue_name] = num_consumers

        old_message_count = dict_consumers.get(key_message_count, 0)
        message_count = int(queue.get('messages', 0))
        if abs(old_message_count - message_count) >= 1000:
            if len(warning_content) > 0:
                warning_content = "%s\n" % warning_content
            warning_content = "%s --- is lagging: %s" % (queue_name, message_count)
            dict_consumers[key_message_count] = message_count

        if message_count == 0:
            dict_consumers[key_message_count] = message_count

        if num_consumers == 0:
            if len(results) > 0:
                results = "%s\n" % results
            results = "%s%s --- No consumeres" % (results, queue_name)

    if len(warning_content):
        send_to_slack(StatusIssues.WARNING, warning_content)

    if len(pass_content):
        send_to_slack(StatusIssues.PASS, pass_content)

    content_file.seek(0)
    content_file.truncate()
    content_file.write(json.dumps(dict_consumers))
    content_file.close()

    if results and len(results) > 0:
        exit(0)
    else:
        exit(1)
