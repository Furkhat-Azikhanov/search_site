# google_checker.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import tldextract

# путь до вашего файла с ключами от Google API
CREDS_FILE = 'creds.json'
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1t_ur4BPCkJmK-jLJXV6ou-v0KXLGP4dmSF52MjiWxxI/edit?gid=0'

def load_domains_from_sheet() -> set[str]:
    """Получает все домены из столбца G Google Таблицы."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_url(SHEET_URL)
    worksheet = sheet.get_worksheet(0)  # первая страница

    column_g = worksheet.col_values(7)  # столбец G
    domains = set()
    for value in column_g:
        ext = tldextract.extract(value)
        if ext.domain and ext.suffix:
            domain = f"{ext.domain}.{ext.suffix}"
            domains.add(domain.lower())
    return domains

def get_main_domain(url: str) -> str:
    """Извлекает главный домен из URL."""
    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}".lower()
