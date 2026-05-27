"""
Сериализация и десериализация Vault ↔ JSON ↔ зашифрованный блоб.

No local file. Только операции в памяти.
"""

import json

from cesar_len_pass_vault.cipher_primary import (
  decrypt_vault_primary,
  encrypt_vault_primary,
)
from cesar_len_pass_vault.cipher_wrapper import decrypt_vault_backup, encrypt_vault_backup
from cesar_len_pass_vault.models import PasswordEntry, Vault


def vault_to_json(vault: Vault) -> str:
  """
  Сериализует Vault в JSON-строку.
  """

  data = {
    "entries": [
      {
        "service": e.service,
        "login": e.login,
        "password": e.password,
        "notes": e.notes,
      }
      for e in vault.entries
    ],
  }

  return json.dumps(data, ensure_ascii=False, indent=2)


def json_to_vault(json_str: str) -> Vault:
  """
  Десериализует JSON-строку в Vault.

  Валидирует структуру JSON.
  При отсутствии полей - подставляет значения по умолчанию.
  Игнорирует неизвестные поля (прямая совместимость).
  """

  data = json.loads(json_str)

  entries = []

  for e in data.get("entries", []):
    entries.append(
      PasswordEntry(
        service=e.get("service", ""),
        login=e.get("login", ""),
        password=e.get("password", ""),
        notes=e.get("notes", ""),
      )
    )

  return Vault(entries=entries)


def pack_vault(vault: Vault, master_password: str, primary: bool = True) -> bytes:
  """
  Упаковывает Vault в зашифрованный блоб.

  Args:
    vault: хранилище для упаковки
    master_password: мастер-пароль для шифрования
    primary: если True - основное шифрование (cesar_len_key),
             если False - резервное (cipher_wrapper)

  Returns:
    Зашифрованный блоб (байты)
  """

  json_str = vault_to_json(vault)

  return (
    encrypt_vault_primary(json_str, master_password)
    if primary
    else encrypt_vault_backup(json_str, master_password)
  )


def unpack_vault(
  encrypted_blob: bytes, master_password: str, primary: bool = True
) -> Vault:
  """
  Распаковывает зашифрованный блоб в Vault.

  Args:
    encrypted_blob: зашифрованный блоб
    master_password: мастер-пароль для расшифрования
    primary: если True - основное шифрование (cesar_len_key),
             если False - резервное (cipher_wrapper)

  Returns:
    Расшифрованное хранилище Vault
  """

  json_str = (
    decrypt_vault_primary(encrypted_blob, master_password)
    if primary
    else decrypt_vault_backup(encrypted_blob, master_password)
  )

  return json_to_vault(json_str)
