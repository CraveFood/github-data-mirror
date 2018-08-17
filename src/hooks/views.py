
import json
import logging

from pprint import pformat

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ghstuff import validate_secret, ghclient, get_github_db

# Logging settings
LOGGER = logging.getLogger('ghmirror.hooks')


@csrf_exempt
@validate_secret
def webhook(request):
    github_db = get_github_db()

    data = json.loads(request.body.decode('utf8'))
    LOGGER.debug(pformat(data))

    event = request.META.get('HTTP_X_GITHUB_EVENT')
    LOGGER.info('Event type: %s', event)

    action = data.get('action')
    LOGGER.info('Event action: %s', action)

    if event == 'release':
        release_response = ghclient.get(url=data['release']['url'])
        release = release_response.json()
        doc_id = 'release/{}/{}'.format(
            data['repository']['full_name'],
            data['release']['id'],
        )
        release['_id'] = doc_id

        github_db.releases.update({'_id': doc_id}, release, upsert=True)

    return JsonResponse({'status': 'ok'})
