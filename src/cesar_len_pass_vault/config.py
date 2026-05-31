"""
Конфигурация приложения.

Загружает настройки из .env и предоставляет их через класс CesarVaultConfig.
На Android использует settings.json в user_data_dir.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv


# --------------------------------------------------------------------------------------

load_dotenv()

# --------------------------------------------------------------------------------------


class CesarVaultConfig:
  """
  Конфигурация приложения.

  Все настройки загружаются из переменных окружения (.env) или settings.json (Android).
  """

  # Crypto settings (не меняются через UI)
  SALT_SIZE: int = int(os.getenv("SALT_SIZE", "32"))
  ITERATIONS: int = int(os.getenv("ITERATIONS", "100000"))
  ROUNDS: int = int(os.getenv("ROUNDS", "3"))

  # Crypto MAGIC constants (не выносятся в .env - это формат файла)
  MAGIC_PRIMARY: bytes = b"CESAR_PRIMARY_V1"
  MAGIC_BACKUP: bytes = b"CESAR_VAULT_V001"

  def __init__(self) -> None:
    """
    Инициализирует конфигурацию.

    На Android пытается загрузить из settings.json, если .env не найден.
    """
    # Пытаемся загрузить с Android-хранилища если .env пуст
    if not os.getenv("YA_TOKEN") or not os.getenv("REMOTE_PATH"):
      self._load_android_settings()

    self.YA_TOKEN = os.getenv("YA_TOKEN", "")
    self.REMOTE_PATH = os.getenv("REMOTE_PATH", "")

  @property
  def BACKUP_REMOTE_PATH(self) -> str:
    """
    Вычисляет путь к backup-файлу.

    Если BACKUP_REMOTE_PATH задан в .env (backward compat), использует его.
    Иначе: REMOTE_PATH + ".backup"
    """
    env_backup = os.getenv("BACKUP_REMOTE_PATH", "")
    if env_backup:
      return env_backup
    return self.REMOTE_PATH + ".backup" if self.REMOTE_PATH else ""

  # MARK: private
  # --------------------------------------------------------------------------

  def _load_android_settings(self) -> None:
    """
    Загружает настройки из settings.json (Android).

    Вызывается только если .env не содержит YA_TOKEN/REMOTE_PATH.
    """
    settings_path = self._env_path() / "settings.json"
    if not settings_path.exists():
      return

    try:
      with open(settings_path, encoding="utf-8") as f:
        settings = json.load(f)

      if "YA_TOKEN" in settings:
        os.environ["YA_TOKEN"] = settings["YA_TOKEN"]
      if "REMOTE_PATH" in settings:
        os.environ["REMOTE_PATH"] = settings["REMOTE_PATH"]
      if "BACKUP_REMOTE_PATH" in settings:
        os.environ["BACKUP_REMOTE_PATH"] = settings["BACKUP_REMOTE_PATH"]

    except (json.JSONDecodeError, OSError):
      pass

  def _env_path(self) -> Path:
    """
    Возвращает путь к директории для хранения настроек.

    На Android: user_data_dir (через android.storage)
    На Desktop: текущая рабочая директория
    """
    try:
      from android.storage import app_storage_path  # type: ignore  # noqa: PLC0415

      return Path(app_storage_path())
    except Exception:
      return Path.cwd()

  def save_settings(self, ya_token: str, remote_path: str) -> None:
    """
    Сохраняет настройки в .env (desktop) или settings.json (Android).

    Args:
        ya_token: Yandex Disk OAuth токен
        remote_path: путь к vault.enc на Яндекс.Диске
    """
    # Обновляем in-memory и os.environ
    self.YA_TOKEN = ya_token
    self.REMOTE_PATH = remote_path
    os.environ["YA_TOKEN"] = ya_token
    os.environ["REMOTE_PATH"] = remote_path

    # Определяем платформу и пишем в соответствующий файл
    try:
      from android.storage import app_storage_path  # type: ignore  # noqa: PLC0415

      # Android: settings.json
      settings_path = Path(app_storage_path()) / "settings.json"
      settings_path.parent.mkdir(parents=True, exist_ok=True)

      with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(
          {
            "YA_TOKEN": ya_token,
            "REMOTE_PATH": remote_path,
            "SALT_SIZE": self.SALT_SIZE,
            "ITERATIONS": self.ITERATIONS,
            "ROUNDS": self.ROUNDS,
          },
          f,
          ensure_ascii=False,
          indent=2,
        )

    except Exception:
      # Desktop: .env
      env_path = Path.cwd() / ".env"
      with open(env_path, "w", encoding="utf-8") as f:
        f.write("# Yandex Disk authentication\n")
        f.write(f"YA_TOKEN={ya_token}\n")
        f.write("\n")
        f.write("# Crypto settings\n")
        f.write(f"SALT_SIZE={self.SALT_SIZE}\n")
        f.write(f"ITERATIONS={self.ITERATIONS}\n")
        f.write(f"ROUNDS={self.ROUNDS}\n")
        f.write("\n")
        f.write("# Yandex Disk paths\n")
        f.write(f"REMOTE_PATH={remote_path}\n")


# --------------------------------------------------------------------------------------


# Экземпляр конфигурации для удобного импорта
config = CesarVaultConfig()


# --------------------------------------------------------------------------------------


def is_configured() -> bool:
  """
  Проверяет, настроено ли приложение.

  Returns:
      True, если YA_TOKEN и REMOTE_PATH не пусты
  """
  return bool(config.YA_TOKEN and config.REMOTE_PATH)
