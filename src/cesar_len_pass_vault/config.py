"""
Конфигурация приложения.

Загружает настройки из .env и предоставляет их через класс CesarVaultConfig.
"""

import os

from dotenv import load_dotenv


load_dotenv()


class CesarVaultConfig:
  """
  Конфигурация приложения.

  Все настройки загружаются из переменных окружения (.env).
  """

  # Yandex Disk authentication
  YA_TOKEN: str = os.getenv("YA_TOKEN", "")

  # Crypto settings
  SALT_SIZE: int = int(os.getenv("SALT_SIZE", "32"))
  ITERATIONS: int = int(os.getenv("ITERATIONS", "100000"))
  ROUNDS: int = int(os.getenv("ROUNDS", "3"))

  # Yandex Disk paths
  REMOTE_PATH: str = os.getenv("REMOTE_PATH", "/Приложения/cesar-len-key/vault.enc")
  BACKUP_REMOTE_PATH: str = os.getenv(
    "BACKUP_REMOTE_PATH", "/Приложения/cesar-len-key/vault_backup.enc"
  )

  # Crypto MAGIC constants (не выносятся в .env - это формат файла)
  MAGIC_PRIMARY: bytes = b"CESAR_PRIMARY_V1"
  MAGIC_BACKUP: bytes = b"CESAR_VAULT_V001"


# Экземпляр конфигурации для удобного импорта
config = CesarVaultConfig()
