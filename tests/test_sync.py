"""
Тесты для sync - синхронизация с Яндекс.Диском.

Требуют валидный YA_TOKEN в .env.
Пропускаются, если токен отсутствует или невалиден.

Используют отдельный тестовый путь, чтобы не затирать боевое хранилище.
Тестовый файл удаляется перед и после каждого теста.
"""

import os
from collections.abc import Generator
from unittest.mock import patch

import pytest
import yadisk

from cesar_len_pass_vault.config import config
from cesar_len_pass_vault.sync import check_connection, download, upload


TEST_REMOTE_PATH = "/Приложения/cesar-len-key/vault_test.enc"

pytestmark = pytest.mark.skipif(
  not config.YA_TOKEN,
  reason="YA_TOKEN не задан в .env",
)


def _cleanup_test_file() -> None:
  """Удаляет тестовый файл с Яндекс.Диска (не падает если нет)."""

  try:
    y = yadisk.YaDisk(token=config.YA_TOKEN)

    if y.check_token():
      y.remove(TEST_REMOTE_PATH, permanently=True)
  except yadisk.exceptions.PathNotFoundError:
    pass
  except Exception:
    pass


@pytest.fixture(autouse=True)
def _manage_test_vault() -> Generator[None, None, None]:
  """
  Фикстура: удаляет тестовый vault перед тестом и после.

  Не трогает боевой vault (config.REMOTE_PATH) -
  патч в _patch_remote_path направляет sync.upload/download на TEST_REMOTE_PATH.
  """

  _cleanup_test_file()

  yield

  _cleanup_test_file()


def _patch_remote_path(func):
  """Декоратор: подменяет REMOTE_PATH на тестовый."""

  return patch.object(
    config,
    "REMOTE_PATH",
    TEST_REMOTE_PATH,
  )(func)


@_patch_remote_path
def test_check_connection() -> None:
  """check_connection возвращает bool."""

  result = check_connection()

  assert isinstance(result, bool)

  if not result:
    pytest.skip("Нет соединения с Яндекс.Диском (невалидный токен)")


@_patch_remote_path
def test_upload_download_roundtrip() -> None:
  """Загрузка и скачивание одних и тех же байт."""

  if not check_connection():
    pytest.skip("Нет соединения с Яндекс.Диском")

  test_data = b"Hello, Yandex Disk! Test upload/download."

  upload(test_data)
  downloaded = download()

  assert downloaded == test_data


@_patch_remote_path
def test_download_size() -> None:
  """Скачанные данные не пустые."""

  if not check_connection():
    pytest.skip("Нет соединения с Яндекс.Диском")

  test_data = b"size_test_" + os.urandom(100)
  upload(test_data)

  downloaded = download()

  assert len(downloaded) == len(test_data)
  assert downloaded == test_data
