from requests import get as http_get
import requests as rq


def ping(url):
    return http_get(url, timeout=2).status_code


def build_session():
    s = rq.Session()
    s.headers.update({"User-Agent": "demo"})
    return s
