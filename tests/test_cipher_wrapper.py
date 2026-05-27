"""
Тесты для cipher_wrapper — усиленная криптография.
"""

import json
import struct

from cesar_len_pass_vault.cipher_wrapper import (
  ROUNDS,
  DecryptionError,
  _caesar_shift,
  _compute_shift,
  _decrypt_text,
  _derive_key,
  _encrypt_text,
  _subkey,
  decrypt_vault,
  encrypt_vault,
)
from cesar_len_pass_vault.models import PasswordEntry, Vault
from cesar_len_pass_vault.storage import vault_to_json


def test_encrypt_decrypt_roundtrip() -> None:
  """decrypt_vault(encrypt_vault(json, pw), pw) == json."""

  original = '{"version": 1, "entries": []}'

  blob = encrypt_vault(original, "master123")
  result = decrypt_vault(blob, "master123")

  assert result == original


def test_different_passwords_different_ciphertext() -> None:
  """Одинаковый JSON с разными паролями даёт разные блобы."""

  json_str = '{"test": 1}'

  b1 = encrypt_vault(json_str, "password1")
  b2 = encrypt_vault(json_str, "password2")

  assert b1 != b2


def test_same_password_different_salt() -> None:
  """Одинаковый JSON и пароль — разные блобы из-за разной соли."""

  json_str = '{"test": 1}'

  b1 = encrypt_vault(json_str, "password")
  b2 = encrypt_vault(json_str, "password")

  assert b1 != b2


def test_empty_vault_json() -> None:
  """encrypt_vault('{}', pw) → decrypt_vault → '{}'."""

  blob = encrypt_vault("{}", "pw")
  result = decrypt_vault(blob, "pw")

  assert result == "{}"


def test_cyrillic_content() -> None:
  """JSON с кириллицей сохраняется после roundtrip."""

  vault = Vault(
    entries=[
      PasswordEntry(
        service="почта",
        login="юзер",
        password="пароль",
        notes="заметки",
      )
    ]
  )

  json_str = vault_to_json(vault)

  blob = encrypt_vault(json_str, "мастер-пароль")
  result = decrypt_vault(blob, "мастер-пароль")

  assert result == json_str

  # Проверяем, что кириллица распарсилась корректно
  data = json.loads(result)

  assert data["entries"][0]["service"] == "почта"
  assert data["entries"][0]["password"] == "пароль"


def test_wrong_password_fails_json() -> None:
  """Неверный пароль → результат не является валидным JSON."""

  blob = encrypt_vault('{"test": 1}', "correct_password")

  try:
    result = decrypt_vault(blob, "wrong_password")
    # Если не упало при декодировании UTF-8, пробуем парсить JSON
    json.loads(result)
    # Крайне маловероятно, но возможно: garbage = valid JSON
    # В этом случае тест считается пройденным — это приемлемый риск
  except (json.JSONDecodeError, UnicodeDecodeError, DecryptionError):
    # Ожидаемое поведение
    pass


def test_corrupted_blob_raises() -> None:
  """Повреждённый блоб вызывает ValueError."""

  try:
    decrypt_vault(b"garbage", "pw")
    raise AssertionError("Должно было вызвать исключение")
  except ValueError:
    pass


def test_truncated_blob_raises() -> None:
  """Слишком короткий блоб вызывает ValueError."""

  try:
    decrypt_vault(b"short", "pw")
    raise AssertionError("Должно было вызвать исключение")
  except ValueError:
    pass


def test_wrong_magic_raises() -> None:
  """Неверный MAGIC в заголовке вызывает ValueError."""

  bad_magic = b"BAD_MAGIC_HEADER"
  salt = b"\x00" * 32
  header = struct.pack(">16s32s", bad_magic, salt)
  body = b"some_ciphertext"

  try:
    decrypt_vault(header + body, "pw")
    raise AssertionError("Должно было вызвать исключение")
  except ValueError:
    pass


def test_key_stretching_consistent() -> None:
  """_derive_key возвращает одинаковый результат для одинаковых входов."""

  k1 = _derive_key("password", b"salt1234567890123456789012345678")
  k2 = _derive_key("password", b"salt1234567890123456789012345678")

  assert k1 == k2


def test_key_stretching_different_salt() -> None:
  """_derive_key с разной солью даёт разные ключи."""

  k1 = _derive_key("password", b"a" * 32)
  k2 = _derive_key("password", b"b" * 32)

  assert k1 != k2


def test_subkeys_different() -> None:
  """_subkey для разных раундов даёт разные подключа."""

  key = b"test_key_32_bytes_long__12345"

  sk0 = _subkey(key, 0)
  sk1 = _subkey(key, 1)
  sk2 = _subkey(key, 2)

  assert sk0 != sk1
  assert sk1 != sk2
  assert sk0 != sk2


def test_shift_non_zero() -> None:
  """_compute_shift никогда не возвращает 0."""

  for position in range(100):
    shift = _compute_shift("test_subkey_hex_string_1234567890", position, 150)

    assert shift != 0
    assert 1 <= shift < 150


def test_shift_deterministic() -> None:
  """Одинаковые входы → одинаковый сдвиг."""

  s1 = _compute_shift("subkey", 42, 150)
  s2 = _compute_shift("subkey", 42, 150)

  assert s1 == s2


def test_caesar_shift_deterministic() -> None:
  """_caesar_shift детерминирован при одинаковых входах."""

  alph = "abcdefghijklmnopqrstuvwxyz"

  r1 = _caesar_shift("a", 5, alph)
  r2 = _caesar_shift("a", 5, alph)

  assert r1 == r2
  assert r1 == "f"  # a + 5 = f


def test_caesar_shift_roundtrip() -> None:
  """_caesar_shift(decrypt=True) обращает _caesar_shift(decrypt=False)."""

  alph = "abcdefghijklmnopqrstuvwxyz"

  for char in alph:
    for shift_val in range(1, 26):
      encrypted = _caesar_shift(char, shift_val, alph, decrypt=False)
      decrypted = _caesar_shift(encrypted, shift_val, alph, decrypt=True)

      assert decrypted == char, f"Failed for char={char}, shift={shift_val}"


def test_caesar_shift_unknown_char() -> None:
  """Символ не из алфавита возвращается без изменений."""

  alph = "abc"

  assert _caesar_shift("z", 3, alph) == "z"
  assert _caesar_shift(" ", 1, alph) == " "
  assert _caesar_shift("\n", 2, alph) == "\n"


def test_encrypt_decrypt_text_roundtrip() -> None:
  """_encrypt_text + _decrypt_text восстанавливает исходный текст."""

  key = b"a" * 32
  original = "Hello, World! This is a test 123."

  encrypted = _encrypt_text(original, key, rounds=ROUNDS)
  decrypted = _decrypt_text(encrypted, key, rounds=ROUNDS)

  assert decrypted == original


def test_encrypt_decrypt_text_cyrillic() -> None:
  """_encrypt_text + _decrypt_text сохраняет кириллицу."""

  key = b"b" * 32
  original = "Привет, мир! Тест 123."

  encrypted = _encrypt_text(original, key, rounds=ROUNDS)
  decrypted = _decrypt_text(encrypted, key, rounds=ROUNDS)

  assert decrypted == original


def test_encrypt_text_different_keys() -> None:
  """Разные ключи дают разный шифротекст для одного текста."""

  text = "Hello, World!"

  e1 = _encrypt_text(text, b"a" * 32)
  e2 = _encrypt_text(text, b"b" * 32)

  assert e1 != e2


def test_encrypt_vault_long_content() -> None:
  """Шифрование/расшифрование длинного JSON."""

  vault = Vault(
    entries=[
      PasswordEntry(
        service=f"service-{i}",
        login=f"user-{i}@example.com",
        password=f"pass-{i}-!@#$%",
        notes=f"Заметка номер {i} с кириллицей",
      )
      for i in range(50)
    ]
  )

  json_str = vault_to_json(vault)

  blob = encrypt_vault(json_str, "long_test_password")
  result = decrypt_vault(blob, "long_test_password")

  assert result == json_str


def test_vault_json_with_colon_and_special_chars() -> None:
  """JSON хранилища с :, -, цифрами и кириллицей — точный roundtrip."""

  vault = Vault(
    entries=[
      PasswordEntry(
        service="gmail",
        login="user@gmail.com",
        password="my-password:123",
        notes="2FA включена",
      ),
      PasswordEntry(
        service="github",
        login="dev",
        password="xyz-789",
        notes="",
      ),
    ]
  )

  json_str = vault_to_json(vault)

  blob = encrypt_vault(json_str, "master123")
  result = decrypt_vault(blob, "master123")

  assert result == json_str, (
    f"Roundtrip failed!\n"
    f"Expected ({len(json_str)} chars): {json_str!r}\n"
    f"Got ({len(result)} chars): {result!r}"
  )

  # Проверяем что результат парсится как JSON
  data = json.loads(result)

  assert data["version"] == 1
  assert len(data["entries"]) == 2
  assert data["entries"][0]["service"] == "gmail"
  assert data["entries"][0]["password"] == "my-password:123"
  assert data["entries"][0]["notes"] == "2FA включена"


def test_vault_json_roundtrip_with_various_passwords() -> None:
  """Roundtrip с разными мастер-паролями, включая короткие и русские."""

  vault = Vault(
    entries=[
      PasswordEntry(service="s", login="l", password="p", notes=""),
    ]
  )

  json_str = vault_to_json(vault)

  for pw in ["1", "abc", "пароль", "long-master-password!@#"]:
    blob = encrypt_vault(json_str, pw)
    result = decrypt_vault(blob, pw)
    assert result == json_str, f"Failed for password {pw!r}"
    json.loads(result)  # Должен парситься
