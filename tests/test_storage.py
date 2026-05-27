"""
Тесты для storage - сериализация/десериализация.
"""

import json

import pytest

from cesar_len_pass_vault.models import PasswordEntry, Vault
from cesar_len_pass_vault.storage import (
  json_to_vault,
  pack_vault,
  unpack_vault,
  vault_to_json,
)


def test_vault_to_json_empty() -> None:
  """Пустой Vault → корректный JSON."""

  vault = Vault()
  result = vault_to_json(vault)

  data = json.loads(result)

  assert data["entries"] == []


def test_vault_to_json_with_entries() -> None:
  """Vault с записями → JSON с корректной структурой."""

  vault = Vault(
    entries=[
      PasswordEntry(service="gmail", login="user", password="abc"),
      PasswordEntry(service="github", login="dev", password="xyz", notes="2FA"),
    ]
  )

  result = vault_to_json(vault)
  data = json.loads(result)

  assert len(data["entries"]) == 2
  assert data["entries"][0]["service"] == "gmail"
  assert data["entries"][1]["notes"] == "2FA"


def test_json_to_vault_empty() -> None:
  """JSON без записей → Vault с пустым списком."""

  json_str = '{"entries": []}'
  vault = json_to_vault(json_str)

  assert vault.entries == []


def test_json_to_vault_with_entries() -> None:
  """JSON с записями → корректный Vault."""

  json_str = """
  {
    "entries": [
      {"service": "gmail", "login": "user", "password": "abc", "notes": ""},
      {"service": "github", "login": "dev", "password": "xyz", "notes": "2FA"}
    ]
  }
  """

  vault = json_to_vault(json_str)

  assert len(vault.entries) == 2
  assert vault.entries[0].service == "gmail"
  assert vault.entries[1].notes == "2FA"


def test_vault_to_json_roundtrip() -> None:
  """json_to_vault(vault_to_json(vault)) восстанавливает Vault."""

  original = Vault(
    entries=[
      PasswordEntry(service="s1", login="l1", password="p1", notes="n1"),
      PasswordEntry(service="s2", login="l2", password="p2"),
    ]
  )

  json_str = vault_to_json(original)
  restored = json_to_vault(json_str)

  assert len(restored.entries) == len(original.entries)

  for orig, rest in zip(original.entries, restored.entries, strict=True):
    assert orig.service == rest.service
    assert orig.login == rest.login
    assert orig.password == rest.password
    assert orig.notes == rest.notes


def test_json_missing_optional_fields() -> None:
  """JSON без поля notes → notes пустая строка."""

  json_str = """
  {
    "entries": [
      {"service": "gmail", "login": "user", "password": "abc"}
    ]
  }
  """

  vault = json_to_vault(json_str)

  assert vault.entries[0].notes == ""


def test_json_unknown_fields_ignored() -> None:
  """JSON с неизвестными полями → парсится без ошибок, поля игнорируются."""

  json_str = """
  {
    "entries": [
      {"service": "gmail", "login": "user", "password": "abc", "foo": "bar"}
    ],
    "extra_field": 42
  }
  """

  vault = json_to_vault(json_str)

  assert len(vault.entries) == 1
  assert vault.entries[0].service == "gmail"


def test_invalid_json_raises() -> None:
  """Невалидный JSON → json.JSONDecodeError."""

  with pytest.raises(json.JSONDecodeError):
    json_to_vault("{invalid json")


def test_empty_entries_list() -> None:
  """JSON с "entries": [] → Vault с 0 записей."""

  vault = json_to_vault('{"entries": []}')

  assert len(vault.entries) == 0


def test_cyrillic_in_json() -> None:
  """Roundtrip сохраняет кириллицу в полях."""

  original = Vault(
    entries=[
      PasswordEntry(
        service="сервис",
        login="логин",
        password="пароль",
        notes="заметки",
      )
    ]
  )

  json_str = vault_to_json(original)
  restored = json_to_vault(json_str)

  assert restored.entries[0].service == "сервис"
  assert restored.entries[0].login == "логин"
  assert restored.entries[0].password == "пароль"
  assert restored.entries[0].notes == "заметки"


def test_pack_vault_returns_bytes() -> None:
  """pack_vault возвращает bytes."""

  vault = Vault(entries=[PasswordEntry(service="s", login="l", password="p")])

  blob = pack_vault(vault, "password")

  assert isinstance(blob, bytes)
  assert len(blob) > 0


def test_pack_unpack_roundtrip() -> None:
  """unpack_vault(pack_vault(vault, pw), pw) восстанавливает Vault."""

  original = Vault(
    entries=[
      PasswordEntry(service="s1", login="l1", password="p1", notes="n1"),
      PasswordEntry(service="s2", login="l2", password="p2"),
    ]
  )

  blob = pack_vault(original, "master123")
  restored = unpack_vault(blob, "master123")

  assert len(restored.entries) == len(original.entries)

  for orig, rest in zip(original.entries, restored.entries, strict=True):
    assert orig.service == rest.service
    assert orig.login == rest.login
    assert orig.password == rest.password
    assert orig.notes == rest.notes


def test_pack_unpack_empty_vault() -> None:
  """pack/unpack пустого Vault."""

  original = Vault()
  blob = pack_vault(original, "pw")
  restored = unpack_vault(blob, "pw")

  assert restored.entries == []
