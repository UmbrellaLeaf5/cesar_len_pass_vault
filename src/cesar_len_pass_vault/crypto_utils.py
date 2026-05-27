"""
Общие криптографические утилиты.
"""

import hashlib
import struct

from cesar_len_pass_vault.config import config


HEADER_FORMAT = f">16s{config.SALT_SIZE}s".encode()


class DecryptionError(Exception):
  """
  Ошибка расшифрования: неверный пароль или повреждённые данные.
  """

  pass


def _derive_key(master_password: str, salt: bytes) -> bytes:
  """
  Растяжение ключа: SHA-256(password + salt) × ITERATIONS итераций.

  Не использует PBKDF2 (не хотим зависеть от hashlib.pbkdf2_hmac),
  реализуем вручную для полного контроля и прозрачности.
  """

  key = master_password.encode("utf-8") + salt

  for _ in range(config.ITERATIONS):
    key = hashlib.sha256(key).digest()

  return key


def validate_and_parse_header(encrypted_blob: bytes, expected_magic: bytes) -> bytes:
  """
  Проверяет и разбирает заголовок блоба.

  Args:
    encrypted_blob: сырые байты (MAGIC + salt + cipher_text)
    expected_magic: ожидаемый MAGIC для проверки

  Returns:
    salt (32 bytes)

  Raises:
    ValueError: если блоб слишком короткий или MAGIC не совпадает
  """

  header_size = struct.calcsize(HEADER_FORMAT)

  if len(encrypted_blob) < header_size:
    raise ValueError("Blob too short")

  magic, salt = struct.unpack(HEADER_FORMAT, encrypted_blob[:header_size])

  if magic != expected_magic:
    raise ValueError("Invalid file format")

  return salt


def get_body(encrypted_blob: bytes) -> bytes:
  """
  Извлекает тело блоба (без заголовка).
  """

  header_size = struct.calcsize(HEADER_FORMAT)

  return encrypted_blob[header_size:]
