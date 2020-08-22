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
    Date created: 06/07/2020
"""
from copy import deepcopy

import requests

REGISTRY_HOST = 'registry.private:5000'
MODULE_NAME = "xxxx"

URL_TAG_LIST = "http://{}/v2/{}/tags/list".format(REGISTRY_HOST, MODULE_NAME)
URL_GET_DIGEST = "http://{}/v2/{}/manifests/{}"
URL_DELETE_DIGEST = "http://{}/v2/{}/manifests/{}"

headers = {
    'Authorization': 'Basic TOKEN'
}


def get_latest_url_delete():
    digest = URL_GET_DIGEST.format(REGISTRY_HOST, MODULE_NAME, 'latest')
    _header_digest = deepcopy(headers)
    _header_digest.update({"Accept": "application/vnd.docker.distribution.manifest.v2+json"})
    _response_digest = requests.get(digest, headers=_header_digest)
    _sha_content_diget = _response_digest.headers.get('Docker-Content-Digest')

    return URL_DELETE_DIGEST.format(REGISTRY_HOST, MODULE_NAME, _sha_content_diget)


if __name__ == '__main__':
    response = requests.get(URL_TAG_LIST, headers=headers)
    tags = response.json().get('tags')
    cache_url_ignored = get_latest_url_delete()
    for tag in tags:
        print('---- ' + tag)
        if tag == 'latest':
            continue

        url_digest = URL_GET_DIGEST.format(REGISTRY_HOST, MODULE_NAME, tag)
        print('url_digest: %s' % url_digest)
        header_digest = deepcopy(headers)
        header_digest.update({"Accept": "application/vnd.docker.distribution.manifest.v2+json"})
        response_digest = requests.get(url_digest, headers=header_digest)
        sha_content_diget = response_digest.headers.get('Docker-Content-Digest')

        url_delete = URL_DELETE_DIGEST.format(REGISTRY_HOST, MODULE_NAME, sha_content_diget)
        if url_delete == cache_url_ignored:
            continue
        print('url_delete: ' + url_delete)
        response_delete = requests.delete(url_delete, headers=headers)
        print(response_delete.text)
