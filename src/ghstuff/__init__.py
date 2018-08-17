
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
