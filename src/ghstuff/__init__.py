
import hmac
import hashlib

import requests

from functools import wraps

from django.conf import settings
from django.http import JsonResponse

from pymongo import MongoClient


def validate_secret(func):
    @wraps(func)
    def decorator(request, *args, **kwargs):
        key = hmac.HMAC(settings.GH_WEBHOOK_SECRET.encode('utf8'),
                        request.body, hashlib.sha1).hexdigest()

        signature = request.META.get('HTTP_X_HUB_SIGNATURE')
        if not signature or not signature.endswith(key):
            response = JsonResponse({
                'error': "Signature doesn't match.",
                'status': 'error',
            })
            response.status_code = 403
            return response

        return func(request, *args, **kwargs)
    return decorator


class GithubClient:
    base_url = 'https://api.github.com'

    def __init__(self, token=None):
        if not token:
            token = settings.GH_TOKEN

        self.auth_headers = {
            'Authorization': 'token {}'.format(token),
            'Accept': 'application/vnd.github.inertia-preview+json',
        }

    def __getattr__(self, attr):
        if hasattr(requests, attr):
            method = getattr(requests, attr)

            def func(uri=None, url=None, json=None, headers=None):
                if not headers:
                    headers = {}

                new_headers = dict(**headers, **self.auth_headers)
                if not url and uri:
                    url = self.base_url + uri
                return method(url, json=json, headers=new_headers)

            return func

ghclient = GithubClient()  # noqa


def get_github_db():
    mongo_client = MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
    return mongo_client.github


def get_document_id(event, webhook_payload, document):
    repo = webhook_payload['repository']['full_name']

    if event == 'release':
        doc_type = 'release'
        _id = webhook_payload['release']['tag_name']

    elif event == 'issues':
        doc_type = 'issue'
        _id = webhook_payload['issue']['number']

    elif event == 'pull_request':
        doc_type = 'pr'
        _id = webhook_payload['pull_request']['number']

    return '{}/{}/{}'.format(doc_type, repo, _id)


def get_document_from_payload(event, webhook_payload):
    url = None
    if event == 'release':
        url = webhook_payload['release']['url']
    elif event == 'issues':
        url = webhook_payload['issue']['url']
    elif event == 'pull_request':
        url = webhook_payload['pull_request']['url']

    if url:
        response = ghclient.get(url=url)
        return response.json()


def get_collection_from_event(event):
    ghdb = get_github_db()
    collection_name = None

    if event == 'release':
        collection_name = 'releases'

    elif event == 'issues':
        collection_name = 'issues'

    elif event == 'pull_request':
        collection_name = 'pull_requests'

    if collection_name:
        return getattr(ghdb, collection_name)
