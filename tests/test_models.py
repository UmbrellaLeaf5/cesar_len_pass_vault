"""
Тесты для моделей данных.
"""

from cesar_len_pass_vault.models import PasswordEntry, Vault


def test_password_entry_defaults() -> None:
  """PasswordEntry с тремя аргументами - notes пустая строка."""

  entry = PasswordEntry(service="gmail", login="user", password="abc")

  assert entry.service == "gmail"
  assert entry.login == "user"
  assert entry.password == "abc"
  assert entry.notes == ""


def test_password_entry_with_notes() -> None:
  """PasswordEntry с заметками."""

  entry = PasswordEntry(
    service="github", login="dev", password="xyz", notes="2FA включена"
  )

  assert entry.notes == "2FA включена"


def test_create_empty_vault() -> None:
  """Vault() создаётся с пустым списком записей."""

  vault = Vault()

  assert vault.entries == []


def test_vault_with_entries() -> None:
  """Vault с тремя записями."""

  entries = [
    PasswordEntry(service="a", login="a", password="a"),
    PasswordEntry(service="b", login="b", password="b"),
    PasswordEntry(service="c", login="c", password="c"),
  ]

  vault = Vault(entries=entries)

  assert len(vault.entries) == 3
  assert vault.entries[1].service == "b"
