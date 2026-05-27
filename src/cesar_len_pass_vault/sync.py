"""
Управление синхронизацией хранилища через Яндекс.Диск.

No local file — весь vault существует только как зашифрованный блоб в облаке.
"""

import io

import yadisk
from yadisk.exceptions import PathNotFoundError, YaDiskError

from cesar_len_pass_vault.config import REMOTE_PATH, YA_TOKEN


class ConnectionError(Exception):
  """
  Ошибка подключения к Яндекс.Диску.
  """

  pass


def get_client() -> yadisk.YaDisk:
  """
  Создаёт и проверяет клиент Яндекс.Диска.
  Вызывает исключение, если токен невалиден.
  """

  y = yadisk.YaDisk(token=YA_TOKEN)

  if not y.check_token():
    raise ConnectionError("Неверный токен Яндекс.Диска. Проверьте YA_TOKEN в .env")

  return y


def upload(encrypted_blob: bytes, path: str | None = None) -> None:
  """
  Загружает зашифрованный блоб на Яндекс.Диск.
  Перезаписывает существующий файл.
  """

  target = path if path is not None else REMOTE_PATH

  try:
    y = get_client()
    file_stream = io.BytesIO(encrypted_blob)
    y.upload(file_stream, target, overwrite=True)

  except ConnectionError:
    raise

  except YaDiskError as e:
    raise ConnectionError(f"Ошибка загрузки на Диск: {e}") from e


def download(path: str | None = None) -> bytes:
  """
  Скачивает зашифрованный блоб с Яндекс.Диска.
  Возвращает сырые байты.
  """

  target = path if path is not None else REMOTE_PATH

  try:
    y = get_client()
    file_stream = io.BytesIO()
    y.download(target, file_stream)
    return file_stream.getvalue()

  except ConnectionError:
    raise

  except PathNotFoundError:
    raise FileNotFoundError(
      "Хранилище не найдено на Диске. Возможно, оно ещё не создано."
    ) from None

  except YaDiskError as e:
    raise ConnectionError(f"Ошибка скачивания с Диска: {e}") from e


def check_connection() -> bool:
  """
  Проверяет соединение с Яндекс.Диском.
  Возвращает True, если токен валиден и Диск доступен.
  """

  try:
    get_client()

    return True
  except ConnectionError:
    return False


def delete_remote(path: str | None = None) -> None:
  """
  Удаляет файл с Яндекс.Диска.

  Если путь не указан, используется REMOTE_PATH.
  Не вызывает исключение, если файл не существует.
  """

  target = path if path is not None else REMOTE_PATH

  try:
    y = get_client()
    y.remove(target, permanently=True)
  except PathNotFoundError:
    pass
  except YaDiskError as e:
    raise ConnectionError(f"Ошибка удаления с Диска: {e}") from e
