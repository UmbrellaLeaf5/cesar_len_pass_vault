"""
Шифрование настроек для Android settings.json.

Использует Caesar-шифрование из cipher_wrapper с ключом SETTINGS_KEY.
Вынесено в отдельный модуль чтобы избежать циклических импортов с config.py.
"""

import base64
import os

from cesar_len_pass_vault._constants import SALT_SIZE, SETTINGS_KEY
from cesar_len_pass_vault.cipher_wrapper import _decrypt_text, _encrypt_text
from cesar_len_pass_vault.crypto_utils import _derive_key


# MARK: encrypt
# ----------------------------------------------------------------------------------------


def encrypt_setting(plaintext: str) -> str:
  """Шифрует строку ключом SETTINGS_KEY. Возвращает salt_b64:data_b64."""

  salt = os.urandom(SALT_SIZE)
  key = _derive_key(SETTINGS_KEY, salt)

  cipher_text = _encrypt_text(plaintext, key)

  salt_b64 = base64.b64encode(salt).decode("ascii")
  data_b64 = base64.b64encode(cipher_text.encode("utf-8")).decode("ascii")

  return f"{salt_b64}:{data_b64}"


# MARK: decrypt
# ----------------------------------------------------------------------------------------


def decrypt_setting(encrypted: str) -> str:
  """Расшифровывает строку из формата salt_b64:data_b64."""

  salt_b64, data_b64 = encrypted.split(":", 1)

  salt = base64.b64decode(salt_b64)
  cipher_text = base64.b64decode(data_b64).decode("utf-8")

  key = _derive_key(SETTINGS_KEY, salt)

  return _decrypt_text(cipher_text, key)
