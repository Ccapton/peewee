from random import randrange
import sys
import zlib
try:
    from cStringIO import StringIO
except ImportError:
    if sys.version_info[0] == 2:
        from StringIO import StringIO
    else:
        from io import StringIO

try:
    from Crypto.Cipher import AES
    from Crypto import Random
except ImportError:
    AES = Random = None

from peewee import *
from peewee import binary_construct

PY2 = sys.version_info[0] == 2


class CompressedField(BlobField):
    if PY2:
        def db_value(self, value):
            if value is not None:
                return binary_construct(zlib.compress(value))

        def python_value(self, value):
            if value is not None:
                return zlib.decompress(value)
    else:
        def db_value(self, value):
            if value is not None:
                return zlib.compress(binary_construct(value))

        def python_value(self, value):
            if value is not None:
                return zlib.decompress(value).decode('utf-8')


if AES and Random:
    class AESEncryptedField(BlobField):
        def __init__(self, key, *args, **kwargs):
            self.key = key
            super(AESEncryptedField, self).__init__(*args, **kwargs)

        def get_cipher(self, key, iv):
            if len(key) > 32:
                raise ValueError('Key length cannot exceed 32 bytes.')
            key = key + ' ' * (32 - len(key))
            return AES.new(key, AES.MODE_CFB, iv)

        def encrypt(self, value, chunk_size=1024):
            iv = Random.get_random_bytes(AES.block_size)
            cipher = self.get_cipher(self.key, iv)
            return iv + cipher.encrypt(value)

        def decrypt(self, value, chunk_size=1024):
            iv = value[:AES.block_size]
            cipher = self.get_cipher(self.key, iv)
            return cipher.decrypt(value[AES.block_size:])

        if PY2:
            def db_value(self, value):
                if value is not None:
                    return binary_construct(self.encrypt(value))

            def python_value(self, value):
                if value is not None:
                    return self.decrypt(value)
        else:
            def db_value(self, value):
                if value is not None:
                    return self.encrypt(value)

            def python_value(self, value):
                if value is not None:
                    return self.decrypt(value)
