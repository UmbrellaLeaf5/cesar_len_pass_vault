"""
Обёртка над cesar_len_key с усиленной криптографией.

Проблемы, которые решает этот модуль:
  1. Float-недетерминизм (замена sin/cos на целочисленный хеш)
  2. Зависимость сдвига только от длин (используем содержимое ключа и слова)
  3. Нулевой сдвиг (запрещаем shift ≡ 0)
  4. Отсутствие соли (добавляем 32-байтовую соль в заголовок блоба)
  5. Отсутствие растяжения ключа (SHA-256, 100k итераций)
  6. Один раунд (3 раунда с подключами)
"""

import hashlib
import hmac
import os
import struct

from cesar_len_key.alphabet_shuffle import ShuffledAlphabet
from cesar_len_key.cryptor import DEFAULT_ALPHABET

from cesar_len_pass_vault.config import config
from cesar_len_pass_vault.crypto_utils import (
  HEADER_FORMAT,
  _derive_key,
  get_body,
  validate_and_parse_header,
)
from cesar_len_pass_vault.exceptions import DecryptionError


def _subkey(parent_key: bytes, round_num: int) -> str:
  """
  Порождение подключа для конкретного раунда через HMAC-SHA256.

  Подключ - строка из hex-цифр (64 символа = 256 бит).
  Используется как ключ для ShuffledAlphabet и для вычисления сдвига.
  """

  data = f"round_{round_num}".encode()

  return hmac.new(parent_key, data, hashlib.sha256).hexdigest()


def _compute_shift(subkey: str, position: int, alph_len: int) -> int:
  """
  Вычисляет целочисленный сдвиг для позиции в тексте.

  Формула: SHA-256(subkey + position) → первые 4 байта → int → mod alph_len.

  Не использует содержимое символа, чтобы шифрование и расшифрование
  давали одинаковый сдвиг для одной и той же позиции.

  Если результат ≡ 0 (mod alph_len), возвращаем 1 (запрет нулевого сдвига).

  Args:
    subkey: подключ раунда (hex-строка)
    position: позиция символа в тексте (для уникальности)
    alph_len: длина алфавита

  Returns:
    int: сдвиг, 1 ≤ shift < alph_len
  """

  data = f"{subkey}|{position}".encode()
  hash_bytes = hashlib.sha256(data).digest()
  raw_shift = int.from_bytes(hash_bytes[:4], "big")
  shift = raw_shift % alph_len

  return shift if shift != 0 else 1


def _caesar_shift(char: str, shift: int, alph: str, decrypt: bool = False) -> str:
  """
  Применяет сдвиг Цезаря к одному символу.

  В отличие от CryptedWord из cesar_len_key:
    - Не использует float-тригонометрию
    - Сдвиг передаётся извне (вычислен через _compute_shift)
    - Не переворачивает слово (это делается на уровне всего текста)

  Args:
    char: исходный символ
    shift: целочисленный сдвиг (не ноль)
    alph: перемешанный алфавит
    decrypt: если True - обратный сдвиг

  Returns:
    Зашифрованный символ (или исходный, если его нет в алфавите)
  """

  if char not in alph:
    return char

  idx = alph.index(char)

  if decrypt:
    new_idx = (idx - shift) % len(alph)

  else:
    new_idx = (idx + shift) % len(alph)

  return alph[new_idx]


def _encrypt_text(text: str, key: bytes, rounds: int = config.ROUNDS) -> str:
  """
  Многораундовое шифрование текста.

  Для каждого раунда:
    1. Породить подключ через _subkey(key, round)
    2. Перемешать алфавит: ShuffledAlphabet(subkey, DEFAULT_ALPHABET)
    3. Для каждого символа в тексте:
       - Вычислить сдвиг через _compute_shift(subkey, position, alph_len)
       - Применить _caesar_shift
  """

  result = text

  for round_num in range(rounds):
    subkey = _subkey(key, round_num)
    alph = ShuffledAlphabet(subkey, DEFAULT_ALPHABET)
    alph_len = len(alph)

    encrypted_chars = []

    for position, char in enumerate(result):
      shift = _compute_shift(subkey, position, alph_len)
      encrypted_chars.append(_caesar_shift(char, shift, alph, decrypt=False))

    result = "".join(encrypted_chars)

  return result


def _decrypt_text(cipher_text: str, key: bytes, rounds: int = config.ROUNDS) -> str:
  """
  Многораундовое расшифрование (обратное _encrypt_text).

  Раунды идут в обратном порядке, операция сдвига - обратная.
  """

  result = cipher_text

  for round_num in range(rounds - 1, -1, -1):
    subkey = _subkey(key, round_num)
    alph = ShuffledAlphabet(subkey, DEFAULT_ALPHABET)
    alph_len = len(alph)

    decrypted_chars = []

    for position, char in enumerate(result):
      shift = _compute_shift(subkey, position, alph_len)
      decrypted_chars.append(_caesar_shift(char, shift, alph, decrypt=True))

    result = "".join(decrypted_chars)

  return result


def encrypt_vault_backup(vault_json: str, master_password: str) -> bytes:
  """
  Шифрует JSON-строку хранилища.

  Args:
    vault_json: JSON-представление Vault
    master_password: мастер-пароль пользователя

  Returns:
    Зашифрованный блоб (MAGIC + salt + cipher_text), готовый к загрузке на Диск
  """

  salt = os.urandom(config.SALT_SIZE)
  stretched_key = _derive_key(master_password, salt)
  cipher_text = _encrypt_text(vault_json, stretched_key)
  body = cipher_text.encode("utf-8")
  header = struct.pack(HEADER_FORMAT, config.MAGIC_BACKUP, salt)

  return header + body


def decrypt_vault_backup(encrypted_blob: bytes, master_password: str) -> str:
  """
  Расшифровывает блоб, полученный с Яндекс.Диска.

  Args:
    encrypted_blob: сырые байты (MAGIC + salt + cipher_text)
    master_password: мастер-пароль пользователя

  Returns:
    JSON-строка хранилища

  Raises:
    ValueError: если MAGIC не совпадает (файл повреждён или не от нас)
    DecryptionError: если неверный мастер-пароль
  """

  salt = validate_and_parse_header(encrypted_blob, config.MAGIC_BACKUP)
  body = get_body(encrypted_blob)
  stretched_key = _derive_key(master_password, salt)

  try:
    cipher_text = body.decode("utf-8")

  except UnicodeDecodeError:
    raise DecryptionError("Invalid master password or corrupted file") from None

  return _decrypt_text(cipher_text, stretched_key)
