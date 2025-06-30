# main.py

import base64
import xml.etree.ElementTree as ET
import requests
from urllib.parse import urlparse
import json
import tldextract
from transliterate import translit

with open("config.json", "r") as f:
    config = json.load(f)

API_KEY = config["API_KEY"]
FOLDER_ID = config["FOLDER_ID"]
PAGE_SIZE = 100

def yandex_api(query: str, region: int = 213, page: int = 0) -> list[str]:
    payload = {
        "query": {
            "searchType": "SEARCH_TYPE_RU",
            "queryText": query,
            "familyMode": "FAMILY_MODE_STRICT",
            "page": page,
        },
        "groupSpec": {
            "groupMode": "GROUP_MODE_DEEP",
            "groupsOnPage": PAGE_SIZE,
            "docsInGroup": 1,
        },
        "region": str(region),
        "l10N": "LOCALIZATION_RU",
        "folderId": FOLDER_ID,
        "responseFormat": "FORMAT_XML",
        "userAgent": "python-requests",
    }

    response = requests.post(
        "https://searchapi.api.cloud.yandex.net/v2/web/search",
        headers={
            "Authorization": f"Api-Key {API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=12,
    )
    response.raise_for_status()
    xml_raw = base64.b64decode(response.json()["rawData"]).decode()
    root = ET.fromstring(xml_raw)
    return [
        elem.findtext("url").strip()
        for elem in root.iter("doc")
        if elem.find("url") is not None
    ]

def is_real_site(url: str) -> bool:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()

    blacklist = [
        "afisha.ru", "m24.ru", "t-j.ru", "thecity.m24.ru",
        "2gis.ru", "yell.ru", "zoon.ru", "flamp.ru", "tripadvisor.ru",
        "vk.com", "facebook.com", "instagram.com", "youtube.com",
        "restoplace.ws"
    ]
    if any(b in domain for b in blacklist):
        return False
    if "xn--" in domain:
        return False
    if path.count("/") > 2:
        return False
    return True


def is_city_in_domain(url: str, city: str) -> bool:
    """Проверяет, содержится ли транслитерированное название города в домене."""
    city_translit = translit(city.lower().replace("ё", "е"), 'ru', reversed=True)
    ext = tldextract.extract(url)
    parts = [ext.subdomain, ext.domain]
    return any(city_translit in part for part in parts if part)

