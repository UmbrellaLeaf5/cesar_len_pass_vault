"""
Основное шифрование через cesar_len_key (CryptedLines).

Шифрует JSON целиком как одну строку через CryptedLines.
Ключ растягивается через SHA-256 × 100k + соль (как в cipher_wrapper).
"""

import hashlib
import os
import struct

from cesar_len_key.cryptor import DEFAULT_ALPHABET, CryptedLines
from cesar_len_key.word_cryption import CryptType


SALT_SIZE = 32
ITERATIONS = 100_000
MAGIC = b"CESAR_PRIMARY_V1"
HEADER_FORMAT = ">16s32s"


class DecryptionError(Exception):
  """
  Ошибка расшифрования: неверный пароль или повреждённые данные.
  """

  pass


def _derive_key(master_password: str, salt: bytes) -> bytes:
  """
  Растяжение ключа: SHA-256(password + salt) × ITERATIONS итераций.
  """

  key = master_password.encode("utf-8") + salt

  for _ in range(ITERATIONS):
    key = hashlib.sha256(key).digest()

  return key


def encrypt_vault_primary(vault_json: str, master_password: str) -> bytes:
  """
  Шифрует JSON-строку хранилища через CryptedLines.

  Весь JSON передаётся как одна строка — CryptedLines разбивает её
  на слова, шифрует каждое, и соединяет обратно пробелами.
  Структурные символы JSON ({, }, [, ], ", :, ,) не входят в алфавит
  и проходят без изменений.

  Args:
    vault_json: JSON-представление Vault
    master_password: мастер-пароль пользователя

  Returns:
    Зашифрованный блоб (MAGIC + salt + ciphertext)
  """

  salt = os.urandom(SALT_SIZE)
  stretched_key = _derive_key(master_password, salt)
  key_hex = stretched_key.hex()

  encrypted_lines = CryptedLines(
    [vault_json], key_hex, alphabet=DEFAULT_ALPHABET, crypt_type=CryptType.encr
  )
  ciphertext = encrypted_lines[0]
  body = ciphertext.encode("utf-8")
  header = struct.pack(HEADER_FORMAT, MAGIC, salt)

  return header + body


def decrypt_vault_primary(encrypted_blob: bytes, master_password: str) -> str:
  """
  Расшифровывает блоб через CryptedLines.

  Args:
    encrypted_blob: сырые байты (MAGIC + salt + ciphertext)
    master_password: мастер-пароль пользователя

  Returns:
    JSON-строка хранилища

  Raises:
    ValueError: если MAGIC не совпадает
    DecryptionError: если неверный пароль
  """

  header_size = struct.calcsize(HEADER_FORMAT)

  if len(encrypted_blob) < header_size:
    raise ValueError("Слишком короткий блоб")

  magic, salt = struct.unpack(HEADER_FORMAT, encrypted_blob[:header_size])

  if magic != MAGIC:
    raise ValueError("Неверный формат файла (ожидается primary)")

  body = encrypted_blob[header_size:]
  stretched_key = _derive_key(master_password, salt)
  key_hex = stretched_key.hex()

  try:
    ciphertext = body.decode("utf-8")
  except UnicodeDecodeError:
    raise DecryptionError("Неверный мастер-пароль или файл повреждён") from None

  decrypted_lines = CryptedLines(
    [ciphertext], key_hex, alphabet=DEFAULT_ALPHABET, crypt_type=CryptType.decr
  )
  plaintext = decrypted_lines[0]

  return plaintext
