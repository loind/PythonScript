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
    Date created: 21/08/2020
"""
import csv
import random
import re

import string
import time

MONGO_DATABASES = ["Account", "Admin"]
MONGO_CREATE_TEMP = 'db.createUser( {{ user: "{user}", pwd: "{pass}", "roles": [ {{role:"read", db:"{db}"}}, {{role:"readWrite", db:"{db}"}}, {{role:"dbAdmin", db:"{db}"}} ] }} )'

SPECIAL_CHAR = "#)(.!^_-*{}[];"
PASS_DATA = SPECIAL_CHAR + string.ascii_lowercase + string.ascii_uppercase + string.digits
LIST_PATTERN = [r'^.*(?=[' + re.escape(SPECIAL_CHAR) + ']).+$',
                r'^.*(?=[0-9]).+$', r'^.*(?=[a-z]).+$', r'^.*(?=[A-Z]).+$']
PASS_LIST_LEN = [ i for i in range(10,16) ]

random.seed(time.time())


def validate_password(password):
    for pattern in LIST_PATTERN:
        s = re.search(pattern, password)
        if not s:
            return True
    return False


def gen_pass():
    chars = ""
    while validate_password(chars):
        length = random.choice(PASS_LIST_LEN)
        chars = ''.join(random.choice(PASS_DATA) for i in range(length))

    return chars


def gen_data_mongo(_writer):
    # admin command
    BASE_ADMIN = 'use admin\ndb.createUser({{ user: "{user}", pwd: "{pass}", roles: [ "userAdminAnyDatabase", "readAnyDatabase","readWriteAnyDatabase","dbAdminAnyDatabase","clusterAdmin" ] }})'
    data = {'user': 'admin', 'pass': gen_pass()}
    _writer.writerow([data['user'], data['pass'], '*.*', BASE_ADMIN.format(**data)])

    # mongoconnector backup
    BASE_MONGOCONNECTOR = 'use admin\ndb.getSiblingDB("admin").createUser({{ user: "{user}", pwd: "{pass}", roles: ["backup"] }})'
    data = {'user': 'mongoconnector', 'pass': gen_pass()}
    _writer.writerow([data['user'], data['pass'], '*.*', BASE_MONGOCONNECTOR.format(**data)])

    for database in MONGO_DATABASES:
        user = database.lower() + 'user'
        password = gen_pass()
        data = {'user': user, 'pass': password, 'db': database}
        _writer.writerow(
            [data['user'], data['pass'], database + '.*', 'use ' + database + '\n' + MONGO_CREATE_TEMP.format(**data)])


MYSQL_CREATE_TEMP = "drop user '{user}'@'{host}';\ncreate user if not exists '{user}'@'{host}' identified by '{pass}';\ngrant {role} on {db}.* to '{user}'@'{host}';"
MYSQL_USER_HOST = '%'
MYSQL_USER_DATABASES = [
    {'user': 'reply', 'db': '*', 'role': 'all privileges'},
    {'user': 'monitoruser', 'db': '*', 'role': 'select'},
    {'user': 'full', 'db': '*', 'role': 'all privileges', 'host': '%'},
]


def gen_data_mysql(_writer):
    # user root
    _writer.writerow(['root', gen_pass()])

    for info in MYSQL_USER_DATABASES:
        user = info['user']
        password = gen_pass()
        db = info['db']
        role = info['role']
        host = info.get('host', None) if info.get('host') is not None else MYSQL_USER_HOST
        data = {'user': user, 'host': host, 'pass': password, 'role': role, 'db': db}
        if user == 'reply':
            reply_pattern = "GRANT replication slave ON *.* TO 'reply'@'{host}' IDENTIFIED BY '{pass}';"
            _writer.writerow([user, password, db + '.*', reply_pattern.format(**data)])
        else:
            _writer.writerow([user, password, db + '.*', MYSQL_CREATE_TEMP.format(**data)])


if __name__ == '__main__':
    file_name = input('Enter file name without extension: ')
    if len(file_name) == 0:
        while len(file_name) == 0:
            file_name = input('Enter file name AGAIN: ')

    mysql_host = input('Enter MySQL user host (Default is: %): ')
    if len(mysql_host) > 0:
        MYSQL_USER_HOST = mysql_host

    writer = csv.writer(open('./' + file_name + '.csv', 'w'))
    writer.writerow(['CASSANDRA'])
    writer.writerow(['USER', 'PASS'])
    writer.writerow(['loind', gen_pass()])
    writer.writerow([''])
    writer.writerow(['KAFKA'])
    writer.writerow(['USER', 'PASS'])
    writer.writerow(['kafka', gen_pass()])
    writer.writerow([''])
    writer.writerow(['RABBITMQ'])
    writer.writerow(['USER', 'PASS'])
    writer.writerow(['loind', gen_pass()])
    writer.writerow([''])
    writer.writerow(['MONGO'])
    writer.writerow(['USER', 'PASS', 'DATABASE', 'CREATE COMMAND'])
    gen_data_mongo(writer)
    writer.writerow([''])
    writer.writerow(['MYSQL'])
    writer.writerow(['USER', 'PASS', 'DATABASE', 'CREATE COMMAND'])
    gen_data_mysql(writer)
