
import hmac
import hashlib

import requests

from functools import wraps

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse


def validate_secret(func):
    @wraps(func)
    def decorator(request, *args, **kwargs):
        key = hmac.HMAC(settings.GH_WEBHOOK_SECRET.encode('utf8'),
                        request.body, hashlib.sha1).hexdigest()

        signature = request.META.get('HTTP_X_HUB_SIGNATURE')
        if not signature or not signature.endswith(key):
            response = JsonResponse({'error': "Signature doesn't match."})
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

            def func(uri, json=None, headers=None):
                if not headers:
                    headers = {}

                new_headers = dict(**headers, **self.auth_headers)
                url = self.base_url + uri
                return method(url, json=json, headers=new_headers)

            return func
