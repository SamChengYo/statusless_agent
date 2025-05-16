import requests
import json

decrypt_url = "http://localhost:1212/decrypt"
encrypt_url = "http://localhost:1212/encrypt"

def get_key(encrypt_key, password:str):
    data = {
        "encrypted_key": encrypt_key,
        "password": password
    }
    
    response = requests.post(decrypt_url, headers={"Content-Type": "application/json"}, data=json.dumps(data))
    
    try:
        key = response.json().get("key")
        
    except:
        key = None
    
    return key

def lock_key(origin_key, password:str):
    data = {
        "key": origin_key,
        "password": password
    }
    
    response = requests.post(encrypt_url, headers={"Content-Type": "application/json"}, data=json.dumps(data))
    
    try:
        key = response.json().get("key")
        
    except :
        key = None
    
    return key