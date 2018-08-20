
import hmac
import hashlib

import requests

from functools import wraps

from django.conf import settings
from django.core.management.color import color_style
from django.http import JsonResponse

from github import Github
from github.Issue import Issue
from pymongo import MongoClient


COLLECTION_TO_DOC_TYPE = {
    'issues': 'issues',
    'pulls': 'pull_request',
    'releases': 'release',
}


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


def get_collection_name(document):
    url_type = document['url'].split('/')[-2]
    return url_type


def get_doctype(document):
    collection_name = get_collection_name(document)
    return COLLECTION_TO_DOC_TYPE.get(collection_name)


def get_document_id(document):
    org, repo = document['url'].split('/')[-4:-2]
    repo_full_name = '{}/{}'.format(org, repo)

    doc_type = get_doctype(document)

    if doc_type == 'release':
        _id = document['tag_name']

    elif doc_type == 'issues':
        _id = document['number']

    elif doc_type == 'pull_request':
        _id = document['number']

    if _id:
        return '{}/{}/{}'.format(doc_type, repo_full_name, _id)


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


def get_collection(document):
    ghdb = get_github_db()
    collection_name = get_collection_name(document)

    if collection_name:
        return getattr(ghdb, collection_name)


def store_document(document):
    doc_id = get_document_id(document)
    collection = get_collection(document)
    collection.update({'_id': doc_id}, document, upsert=True)


def get_issues(repo_full_name):
    gh = Github(settings.GH_TOKEN)
    repo = gh.get_repo(repo_full_name)

    for issue in repo.get_issues(state='all'):
        store_document(issue.raw_data)


def get_pulls(repo_full_name):
    gh = Github(settings.GH_TOKEN)
    repo = gh.get_repo(repo_full_name)

    for pull in repo.get_pulls(state='all'):
        store_document(pull.raw_data)


def get_releases(repo_full_name):
    gh = Github(settings.GH_TOKEN)
    repo = gh.get_repo(repo_full_name)

    for release in repo.get_releases():
        store_document(release.raw_data)


def get_events(repo_full_name):
    gh = Github(settings.GH_TOKEN)
    ghdb = get_github_db()

    search_for = {
        'repository_url': {
            '$regex': '{}$'.format(repo_full_name),
        }
    }
    for issue_raw in ghdb.issues.find(search_for):
        issue = Issue(gh._Github__requester, {}, issue_raw, completed=True)
        issue_raw['events'] = []
        for event in issue.get_events():
            issue_raw['events'].append(event.raw_data)

        store_document(issue_raw)


def sync_gh_data(organization_name):
    colors = color_style()

    gh = Github(settings.GH_TOKEN)
    org = gh.get_organization(organization_name)

    for repo in org.get_repos(organization_name):
        print('\nSyncing data from repo {}'.format(repo.full_name))

        print('Downloading releases... ', end='', flush=True)
        get_releases(repo.full_name)
        print(colors.SUCCESS('Done'), flush=True)

        print('Downloading pull requests... ', end='', flush=True)
        get_pulls(repo.full_name)
        print(colors.SUCCESS('Done'), flush=True)

        print('Downloading issues... ', end='', flush=True)
        get_issues(repo.full_name)
        print(colors.SUCCESS('Done'), flush=True)

        print('Downloading issue events... ', end='', flush=True)
        get_events(repo.full_name)
        print(colors.SUCCESS('Done'), flush=True)
