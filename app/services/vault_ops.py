"""
Операции с хранилищем: скачать/загрузить + шифрование/дешифрование.
"""

from cesar_len_pass_vault import pack_vault, unpack_vault, vault_to_json
from cesar_len_pass_vault.config import config
from cesar_len_pass_vault.models import Vault
from cesar_len_pass_vault.sync import download, upload


# MARK: download
# --------------------------------------------------------------------------------------


def download_primary(password: str) -> tuple[str, int]:
  """
  Скачать и расшифровать primary-хранилище с Яндекс.Диска.

  Args:
    password: мастер-пароль для расшифрования

  Returns:
    Кортеж (json_str, entry_count) — JSON-строка и количество записей

  Raises:
    FileNotFoundError: хранилище ещё не создано
    YaConnectionError: ошибка подключения к Яндекс.Диску
    json.JSONDecodeError: неверный пароль или повреждённые данные
  """

  blob = download()
  vault = unpack_vault(blob, password, primary=True)
  json_str = vault_to_json(vault)

  return json_str, len(vault.entries)


# MARK: backup
# --------------------------------------------------------------------------------------


def download_backup(password: str) -> tuple[str, int]:
  """
  Скачать и расшифровать backup-хранилище с Яндекс.Диска.

  Args:
    password: мастер-пароль для расшифрования

  Returns:
    Кортеж (json_str, entry_count) — JSON-строка и количество записей

  Raises:
    FileNotFoundError: backup ещё не создан
    YaConnectionError: ошибка подключения к Яндекс.Диску
    json.JSONDecodeError: неверный пароль или повреждённые данные
    DecryptionError: ошибка расшифрования backup
  """

  blob = download(path=config.BACKUP_REMOTE_PATH)
  vault = unpack_vault(blob, password, primary=False)
  json_str = vault_to_json(vault)

  return json_str, len(vault.entries)


# MARK: upload
# --------------------------------------------------------------------------------------


def upload_vault(primary_vault: Vault, backup_vault: Vault, password: str) -> None:
  """
  Зашифровать и загрузить оба хранилища на Яндекс.Диск.

  Args:
    primary_vault: primary-хранилище (объект Vault)
    backup_vault: backup-хранилище (объект Vault)
    password: мастер-пароль для шифрования

  Raises:
    YaConnectionError: ошибка подключения к Яндекс.Диску
  """

  # Основное хранилище
  primary_blob = pack_vault(primary_vault, password, primary=True)
  upload(primary_blob)

  # Резервная копия
  backup_blob = pack_vault(backup_vault, password, primary=False)
  upload(backup_blob, path=config.BACKUP_REMOTE_PATH)
