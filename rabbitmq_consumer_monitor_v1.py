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
    SUCCESS = 2


def send_to_slack(status_issues, content):
    slack_url = "https://hooks.slack.com/services/xxxxxxxxxxxxxx/xxxxxxxxx/xxxxxxxxxxxxxx"

    color = ""
    if status_issues == StatusIssues.WARNING:
        color = "#ffcc00"
    elif status_issues == StatusIssues.ERROR:
        color = "#ff0000"
    elif status_issues == StatusIssues.SUCCESS:
        color = "#00ff00"

    payload = {
        "attachments": [
            {
                "text": content,
                "color": color,
                "fields": [
                    {"title": "Date", "value": str(datetime.now()), "short": True},
                    {"title": "Host", "value": 'VNPAY - %s' % platform.node(), "short": True}
                ]
            }
        ]
    }
    requests.post(url=slack_url, json=payload)


if __name__ == '__main__':
    rabbitmq_host = "rabbitmq-server:15672"
    header = {
        'content-type': 'application/json'
    }
    url = "http://%s/api/queues" % rabbitmq_host

    IGNORED_LIST = ['celery']

    response = requests.get(url, headers=header, auth=HTTPBasicAuth('user', 'pass'))
    results = ""
    content_file = open('~/rabbitmq.log', 'r+')
    data_saved = content_file.read()

    dict_consumers = {}
    if data_saved:
        dict_consumers = json.loads(data_saved)

    warning_content = ""
    success_content = ""
    for queue in response.json():
        messages_ready = int(queue.get('messages_ready_ram', 0))
        num_consumers = int(queue.get('consumers', 0))
        queue_name = queue.get('name')
        if queue_name in IGNORED_LIST:
            continue

        # check consumer
        key_warn = "warn_%s" % queue_name
        cache_number = dict_consumers.get(queue_name)
        if cache_number:
            if num_consumers > cache_number:
                dict_consumers[queue_name] = num_consumers

            elif num_consumers < cache_number:
                if dict_consumers.get(key_warn, 0) < 5:
                    if len(warning_content) > 0:
                        warning_content = "%s\n" % warning_content
                    warning_content = "%s%s --- down from %s to %s" % (
                        warning_content, queue_name, cache_number, num_consumers)
                    dict_consumers[key_warn] = dict_consumers.get(key_warn, 0) + 1

            elif num_consumers == cache_number:
                if dict_consumers.get(key_warn, 0) > 0:
                    dict_consumers[key_warn] = 0
                    if len(warning_content) > 0:
                        success_content = "%s\n" % success_content
                    success_content = "%s%s --- healing to %s" % (success_content, queue_name, num_consumers)

        else:
            dict_consumers[queue_name] = num_consumers

        if num_consumers == 0:
            if len(results) > 0:
                results = "%s\n" % results
            results = "%s%s --- No consumeres" % (results, queue_name)

        # check ready message
        key_lag_message = 'lag_%s' % queue_name
        if messages_ready >= 1000:
            old_value = dict_consumers.get(key_lag_message, 0)
            if abs(old_value - messages_ready) >= 1000:
                if len(warning_content) > 0:
                    warning_content = "%s\n" % warning_content
                warning_content = "%s%s --- lagging: %s messages" % (warning_content, queue_name, messages_ready)
                dict_consumers[key_lag_message] = messages_ready
        else:
            dict_consumers[key_lag_message] = messages_ready

    if len(warning_content):
        send_to_slack(StatusIssues.WARNING, warning_content)

    if len(success_content):
        send_to_slack(StatusIssues.SUCCESS, success_content)

    print(results)

    content_file.seek(0)
    content_file.truncate()
    content_file.write(json.dumps(dict_consumers))
    content_file.close()

    if results and len(results) > 0:
        exit(0)
    else:
        exit(1)
