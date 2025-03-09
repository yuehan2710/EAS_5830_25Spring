import hashlib
import os

def myhash(m):
    #Generate random nonce
    nonce = os.urandom(16).hex()  # Convert to a hex string

    #Generate hex digest
    # Concatenate nonce and message, then hash using SHA-256
    h_hex = hashlib.sha256((nonce + m).encode()).hexdigest()

    return nonce, h_hex
