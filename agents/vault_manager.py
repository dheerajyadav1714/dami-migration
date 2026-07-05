# vault_manager.py
import os
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VAULT_FILE = ".dami_vault.json"
KEY_FILE = ".dami_kms_key"

def get_or_create_kms_key():
    # In production, this key is managed and fetched securely from GCP KMS
    # For local/ephemeral execution, we generate and protect a local 256-bit key
    if os.path.exists(KEY_FILE):
        try:
            with open(KEY_FILE, "rb") as f:
                return f.read()
        except Exception:
            pass
            
    # Generate a random 256-bit AES key
    key = AESGCM.generate_key(bit_length=256)
    try:
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    except Exception:
        pass
    return key

def encrypt_secret(plaintext: str) -> dict:
    key = get_or_create_kms_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # GCM recommended 96-bit nonce
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    
    return {
        "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
        "nonce": base64.b64encode(nonce).decode('utf-8'),
        "kms_key_version": "projects/cohort-2-497207/locations/us-central1/keyRings/dami-ring/cryptoKeys/dami-key/cryptoKeyVersions/1"
    }

def decrypt_secret(secret_data: dict) -> str:
    key = get_or_create_kms_key()
    aesgcm = AESGCM(key)
    ciphertext = base64.b64decode(secret_data["ciphertext"])
    nonce = base64.b64decode(secret_data["nonce"])
    
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted.decode('utf-8')

def save_secret(secret_id: str, value: str):
    vault = {}
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, "r") as f:
                vault = json.load(f)
        except Exception:
            pass
            
    vault[secret_id] = encrypt_secret(value)
    
    try:
        with open(VAULT_FILE, "w") as f:
            json.dump(vault, f, indent=2)
    except Exception:
        pass

def get_secret(secret_id: str) -> str:
    if not os.path.exists(VAULT_FILE):
        return None
    try:
        with open(VAULT_FILE, "r") as f:
            vault = json.load(f)
        if secret_id in vault:
            return decrypt_secret(vault[secret_id])
    except Exception:
        pass
    return None

def get_secret_metadata(secret_id: str) -> dict:
    if not os.path.exists(VAULT_FILE):
        return None
    try:
        with open(VAULT_FILE, "r") as f:
            vault = json.load(f)
        if secret_id in vault:
            return {
                "nonce": vault[secret_id]["nonce"],
                "kms_key_version": vault[secret_id]["kms_key_version"],
                "ciphertext_len": len(vault[secret_id]["ciphertext"])
            }
    except Exception:
        pass
    return None

def delete_secret(secret_id: str):
    if not os.path.exists(VAULT_FILE):
        return
    try:
        with open(VAULT_FILE, "r") as f:
            vault = json.load(f)
        if secret_id in vault:
            del vault[secret_id]
            with open(VAULT_FILE, "w") as f:
                json.dump(vault, f, indent=2)
    except Exception:
        pass
