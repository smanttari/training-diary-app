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


def sleep_summary(path, token, start_date=None, end_date=None):
    params = {}
    if start_date is not None:
        params['start_date'] = start_date
    if end_date is not None:
        params['end_date'] = end_date
    headers = {'Authorization': f'Bearer {token}'}
    url = settings.OURA_URL + '/' + path
    response = requests.get(url, headers=headers, params=params)
    return response


def parse_sleep_data(user, sleep, daily_sleep):
    sleep_objects = []
    sleep_data = sleep.json()['data']
    daily_sleep_data = daily_sleep.json()['data']
    for entry in sleep_data:
        if entry['type'] == 'long_sleep':
            # get sleep score from daily sleep data
            for item in daily_sleep_data:
                if item['day'] == entry['day']:
                    score = item['score']
            sleep_objects.append(OuraSleep(
                user = user,
                date = entry['day'],
                bedtime_start = datetime.strptime(entry['bedtime_start'][:19], '%Y-%m-%dT%H:%M:%S'),
                bedtime_end = datetime.strptime(entry['bedtime_end'][:19], '%Y-%m-%dT%H:%M:%S'),
                duration = entry['time_in_bed']/3600,
                total = entry['total_sleep_duration']/3600,
                awake = entry['awake_time']/3600,
                rem = entry['rem_sleep_duration']/3600,
                deep = entry['deep_sleep_duration']/3600,
                light = entry['light_sleep_duration']/3600,
                hr_min = entry['lowest_heart_rate'],
                hr_avg = entry['average_heart_rate'],
                hrv_avg = entry['average_hrv'],
                score = score
            ))
    return sleep_objects


def error_message(response):
    response_json = response.json()
    if 'detail' in response_json:
        msg = str(response.status_code) + ': ' + response_json['detail']['msg']
    else:
        msg = str(response.status_code)
    return msg