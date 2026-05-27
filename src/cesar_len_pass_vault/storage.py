"""
Сериализация и десериализация Vault ↔ JSON ↔ зашифрованный блоб.

No local file. Только операции в памяти.
"""

import json

from cesar_len_pass_vault.cipher_primary import (
  decrypt_vault_primary,
  encrypt_vault_primary,
)
from cesar_len_pass_vault.cipher_wrapper import decrypt_vault, encrypt_vault
from cesar_len_pass_vault.models import PasswordEntry, Vault


def vault_to_json(vault: Vault) -> str:
  """
  Сериализует Vault в JSON-строку.

  Формат JSON:
  {
    "version": 1,
    "entries": [
      {
        "service": "gmail",
        "login": "user@gmail.com",
        "password": "abc123",
        "notes": "2FA enabled"
      },
      ...
    ]
  }
  """

  data = {
    "version": vault.version,
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
  При отсутствии полей — подставляет значения по умолчанию.
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

  return Vault(
    entries=entries,
    version=data.get("version", 1),
  )


def pack_vault(vault: Vault, master_password: str) -> bytes:
  """
  Упаковывает Vault в зашифрованный блоб (резервное шифрование, cipher_wrapper).

  vault → vault_to_json → encrypt_vault → bytes
  """

  json_str = vault_to_json(vault)

  return encrypt_vault(json_str, master_password)


def unpack_vault(encrypted_blob: bytes, master_password: str) -> Vault:
  """
  Распаковывает зашифрованный блоб (резервное шифрование, cipher_wrapper).

  bytes → decrypt_vault → json_to_vault → Vault
  """

  json_str = decrypt_vault(encrypted_blob, master_password)

  return json_to_vault(json_str)


def pack_vault_primary(vault: Vault, master_password: str) -> bytes:
  """
  Упаковывает Vault в зашифрованный блоб (основное шифрование, cesar_len_key).

  vault → vault_to_json → encrypt_vault_primary → bytes
  """

  json_str = vault_to_json(vault)

  return encrypt_vault_primary(json_str, master_password)


def unpack_vault_primary(encrypted_blob: bytes, master_password: str) -> Vault:
  """
  Распаковывает зашифрованный блоб (основное шифрование, cesar_len_key).

  bytes → decrypt_vault_primary → json_to_vault → Vault
  """

  json_str = decrypt_vault_primary(encrypted_blob, master_password)

  return json_to_vault(json_str)
