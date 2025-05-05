"""
This file is giving cryptography lib
"""
import hashlib, base64
from Crypto.PublicKey import RSA

class CryptoLib():

    @staticmethod
    def generate_sha256(string_input):
        sha256 = hashlib.sha256()
        sha256.update(string_input.encode('ascii'))
        hash_value = sha256.hexdigest()

        return hash_value
    
    @staticmethod
    def encode_base64(string_input):
        string_bytes = string_input.encode('ascii')
        base64_bytes = base64.b64encode(string_bytes)
        base64_string = base64_bytes.decode('ascii')

        return base64_string

    @staticmethod
    def decode_base64(base64_string_input):
        base64_bytes = base64_string_input.encode('ascii')
        string_bytes = base64.b64decode(base64_bytes)
        string_message = string_bytes.decode('ascii')

        return string_message

#    key = RSA.generate(4096)
#    private_key = key.exportKey()
#    public_key = key.publickey().exportKey()
#    import json
#    from jwcrypto.jwk import JWK
#    f = open("jwtRS256.key.pub", "r")
#    public_key = f.read()
#    f.clos#e()

#    jwk_obj = JWK.from_pem(public_key.encode('utf-8'))
#    public_jwk = json.loads(jwk_obj.export_public())
#    public_jwk['alg'] = 'RS256'
#    public_jwk['use'] = 'sig'
#    public_jwk_str = json.dumps(public_jwk)
#    print(public_jwk_str)