import base64
import hashlib
import hmac

class ApiBase():
    def __init__(self, exchange_id=None):
        self.exchange_id = exchange_id

    def get_signature(self, message, secret_key):
        message = message.encode("UTF-8")
        hmac_key = base64.b64decode(secret_key)
        signature = hmac.new(hmac_key, message, hashlib.sha256).digest()
        signature_b64 = base64.b64encode(signature).decode()
        return signature_b64

    def get_auth(self):
        raise NotImplementedError

    def get_query(self):
        raise NotImplementedError


