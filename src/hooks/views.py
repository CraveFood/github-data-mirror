
import json
import logging

from pprint import pformat

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ghstuff import get_document_from_payload, store_document, validate_secret

# Logging settings
LOGGER = logging.getLogger('ghmirror.hooks')


@csrf_exempt
@validate_secret
def webhook(request):
    data = json.loads(request.body.decode('utf8'))
    LOGGER.debug(pformat(data))

    event = request.META.get('HTTP_X_GITHUB_EVENT')
    LOGGER.info('Event type: %s', event)

    action = data.get('action')
    LOGGER.info('Event action: %s', action)

    document = get_document_from_payload(event, data)
    if not document:
        response = JsonResponse({
            'status': 'ok',
            'message': 'No document retrived from payload.',
        })
        response.status_code = 204
        return response

    store_document(document)

    return JsonResponse({'status': 'ok'})
