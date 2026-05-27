"""
Основное шифрование через cesar_len_key (CryptedLines).

Шифрует JSON целиком как одну строку через CryptedLines.
Ключ растягивается через SHA-256 × 100k + соль (как в cipher_wrapper).
"""

import os
import struct

from cesar_len_key.cryptor import DEFAULT_ALPHABET, CryptedLines
from cesar_len_key.word_cryption import CryptType

from cesar_len_pass_vault.config import config
from cesar_len_pass_vault.crypto_utils import (
  HEADER_FORMAT,
  _derive_key,
  get_body,
  validate_and_parse_header,
)
from cesar_len_pass_vault.exceptions import DecryptionError


def encrypt_vault_primary(vault_json: str, master_password: str) -> bytes:
  """
  Шифрует JSON-строку хранилища через CryptedLines.

  Весь JSON передаётся как одна строка - CryptedLines разбивает её
  на слова, шифрует каждое, и соединяет обратно пробелами.
  Структурные символы JSON ({, }, [, ], ", :, ,) не входят в алфавит
  и проходят без изменений.

  Args:
    vault_json: JSON-представление Vault
    master_password: мастер-пароль пользователя

  Returns:
    Зашифрованный блоб (MAGIC + salt + cipher_text)
  """

  salt = os.urandom(config.SALT_SIZE)
  stretched_key = _derive_key(master_password, salt)
  key_hex = stretched_key.hex()

  encrypted_lines = CryptedLines(
    [vault_json], key_hex, alphabet=DEFAULT_ALPHABET, crypt_type=CryptType.encr
  )
  cipher_text = encrypted_lines[0]
  body = cipher_text.encode("utf-8")
  header = struct.pack(HEADER_FORMAT, config.MAGIC_PRIMARY, salt)

  return header + body


def decrypt_vault_primary(encrypted_blob: bytes, master_password: str) -> str:
  """
  Расшифровывает блоб через CryptedLines.

  Args:
    encrypted_blob: сырые байты (MAGIC + salt + cipher_text)
    master_password: мастер-пароль пользователя

  Returns:
    JSON-строка хранилища

  Raises:
    ValueError: если MAGIC не совпадает
    DecryptionError: если неверный пароль
  """

  salt = validate_and_parse_header(encrypted_blob, config.MAGIC_PRIMARY)
  body = get_body(encrypted_blob)
  stretched_key = _derive_key(master_password, salt)
  key_hex = stretched_key.hex()

  try:
    cipher_text = body.decode("utf-8")

  except UnicodeDecodeError:
    raise DecryptionError("Invalid master password or corrupted file") from None

  decrypted_lines = CryptedLines(
    [cipher_text], key_hex, alphabet=DEFAULT_ALPHABET, crypt_type=CryptType.decr
  )

  return decrypted_lines[0]
