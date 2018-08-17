
import json
import logging

from pprint import pformat

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ghstuff import (get_collection_from_event, get_document_from_payload,
                     get_document_id, validate_secret)

# Logging settings
LOGGER = logging.getLogger('ghmirror.hooks')

event_mapping = {
    'pull_request_review': 'pull_request',
}


@csrf_exempt
@validate_secret
def webhook(request):
    data = json.loads(request.body.decode('utf8'))
    LOGGER.debug(pformat(data))

    event = request.META.get('HTTP_X_GITHUB_EVENT')
    LOGGER.info('Event type: %s', event)

    action = data.get('action')
    LOGGER.info('Event action: %s', action)

    mapped_event = event_mapping.get(event, event)

    document = get_document_from_payload(mapped_event, data)
    if not document:
        response = JsonResponse({
            'status': 'ok',
            'message': 'No document retrived from payload.',
        })
        response.status_code = 204
        return response

    doc_id = get_document_id(mapped_event, data, document)

    collection = get_collection_from_event(mapped_event)
    collection.update({'_id': doc_id}, document, upsert=True)

    return JsonResponse({'status': 'ok'})
