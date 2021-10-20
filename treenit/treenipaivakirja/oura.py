import requests
from datetime import datetime
from urllib.parse import urlencode

from django.conf import settings
from treenipaivakirja.models import OuraSleep


def build_auth_url():
    params = {
        'response_type': 'code', 
        'scope': 'daily',
        'client_id': settings.OURA_CLIENT_KEY
        }
    auth_url = f'{settings.OURA_AUTH_URL}?{urlencode(params)}'
    return auth_url


def get_access_token(auth_code):
    headers = {
        'Content-Type' : 'application/x-www-form-urlencoded',
        'Accept' : 'application/json;charset=UTF-8'
        }
    data = {
        'grant_type' : 'authorization_code',
        'code' : auth_code
        }
    response = requests.post(settings.OURA_ACCESS_TOKEN_URL, 
        headers = headers, 
        data = data,
        auth = requests.auth.HTTPBasicAuth(settings.OURA_CLIENT_KEY, settings.OURA_CLIENT_SECRET)
        )
    return response


def refresh_token(refresh_token):
    headers = {
        'Content-Type' : 'application/x-www-form-urlencoded',
        'Accept' : 'application/json;charset=UTF-8'
        }
    data = {
        'grant_type' : 'refresh_token',
        'refresh_token' : refresh_token
        }
    response = requests.post(settings.OURA_ACCESS_TOKEN_URL, 
        headers = headers, 
        data = data,
        auth = requests.auth.HTTPBasicAuth(settings.OURA_CLIENT_KEY, settings.OURA_CLIENT_SECRET)
        )
    return response


def sleep_summary(token, start_date=None, end_date=None):
    params = {}
    if start_date is not None:
        params['start'] = start_date
    if end_date is not None:
        params['end'] = end_date
    headers = {'Authorization': f'Bearer {token}'}
    url = '{}/sleep?{}'.format(settings.OURA_URL, urlencode(params))
    response = requests.get(url, headers=headers)
    return response


def parse_sleep_data(user, sleep):
    sleep_objects = []
    for entry in sleep.json()['sleep']:
        if entry['is_longest'] == 1:
            sleep_objects.append(OuraSleep(
                user = user,
                date = entry['summary_date'],
                bedtime_start = datetime.strptime(entry['bedtime_start'][:19], '%Y-%m-%dT%H:%M:%S'),
                bedtime_end = datetime.strptime(entry['bedtime_end'][:19], '%Y-%m-%dT%H:%M:%S'),
                duration = entry['duration']/3600,
                total = entry['total']/3600,
                awake = entry['awake']/3600,
                rem = entry['rem']/3600,
                deep = entry['deep']/3600,
                light = entry['light']/3600,
                hr_min = entry['hr_lowest'],
                hr_avg = entry['hr_average'],
                hrv_avg = entry['rmssd'],
                score = entry['score']
            ))
    return sleep_objects


def error_message(response):
    response = response.json()
    msg = '{} {}: {}'.format(response['status'], response['title'], response['detail'])
    return msg