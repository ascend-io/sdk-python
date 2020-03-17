import crypt
import requests

URL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv'


def context(credentials: str):
    return {}


def list_objects(context: dict, metadata: dict):
    resp = requests.get(URL)
    yield {'name': 'confirmed_cases', 'fingerprint': crypt.crypt(str(resp.content)), 'is_prefix': False}


def read_bytes(context: dict, metadata: dict):
    resp = requests.get(URL)
    yield resp.content
