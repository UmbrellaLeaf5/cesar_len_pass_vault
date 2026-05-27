"""
Основной экран работы с хранилищем.
"""

import json
from datetime import datetime
from typing import cast

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen

from app.main import CesarVaultApp
from app.screens.add_entry import AddEntryPopup
from cesar_len_pass_vault import (
  json_to_vault,
  pack_vault,
  vault_to_json,
)
from cesar_len_pass_vault.cipher_wrapper import decrypt_vault
from cesar_len_pass_vault.sync import ConnectionError, download, upload


Builder.load_file("app/screens/vault.kv")


class VaultScreen(Screen):
  """
  Основной экран работы с хранилищем.
  """

  editor = ObjectProperty(None)
  status_label = ObjectProperty(None)
  toolbar = ObjectProperty(None)

  _state: str = "empty"

  def download(self) -> None:
    """Скачать хранилище с Яндекс.Диска и показать в редакторе."""

    self._set_state("loading")

    try:
      blob = download()
      app = cast("CesarVaultApp", App.get_running_app())

      # Расшифровка
      json_str = decrypt_vault(blob, app.master_password)

      # DEBUG: записываем расшифрованный текст до парсинга JSON
      # try:
      #   with open("debug_decrypted.txt", "w", encoding="utf-8") as f:
      #     f.write(repr(json_str))
      # except OSError:
      #   pass

      # Парсинг JSON
      vault = json_to_vault(json_str)
      json_formatted = vault_to_json(vault)
      self.editor.text = json_formatted
      self._update_status_loaded(len(vault.entries))
      self._set_state("loaded")

    except FileNotFoundError:
      self._set_state("error")
      self._update_status("Хранилище не найдено. Создайте новое.")
      self.editor.text = ""
      self._set_state("loaded")

    except json.JSONDecodeError as e:
      self._set_state("error")
      self._update_status(
        f"Ошибка JSON при расшифровке: строка {e.lineno}, "
        f"колонка {e.colno} (символ {e.pos}). "
        # f"См. debug_decrypted.txt"
      )

    except ConnectionError as e:
      self._set_state("error")
      self._update_status(f"Ошибка: {e}")

    except Exception as e:
      self._set_state("error")
      self._update_status(f"Ошибка: {e}")

  def upload(self) -> None:
    """Зашифровать редактор и загрузить на Яндекс.Диск."""

    json_str = self.editor.text.strip()

    if not json_str:
      self._update_status("Нечего сохранять: редактор пуст")

      return

    try:
      vault = json_to_vault(json_str)

    except json.JSONDecodeError as e:
      self._update_status(f"Ошибка JSON: строка {e.lineno}, колонка {e.colno}")

      return

    self._set_state("loading")

    try:
      # DEBUG: записываем JSON, который уходит на шифрование
      # json_for_encrypt = vault_to_json(vault)

      # try:
      #   with open("debug_upload.txt", "w", encoding="utf-8") as f:
      #     f.write(repr(json_for_encrypt))
      # except OSError:
      #   pass

      app = cast("CesarVaultApp", App.get_running_app())
      blob = pack_vault(vault, app.master_password)

      upload(blob)

      now = datetime.now().strftime("%H:%M")
      self._update_status(f"Сохранено {now} · {len(vault.entries)} записей")
      self._set_state("loaded")

    except ConnectionError as e:
      self._set_state("error")
      self._update_status(f"Ошибка: {e}")

    except Exception as e:
      self._set_state("error")
      self._update_status(f"Ошибка: {e}")

  def add_entry(self) -> None:
    """Открыть попап добавления записи."""

    popup = AddEntryPopup()
    popup.open()

  def copy_all(self) -> None:
    """Скопировать всё содержимое редактора в буфер обмена."""

    Clipboard.copy(self.editor.text)
    self._update_status("Скопировано!")

    # Очистить статус через 2 секунды
    Clock.schedule_once(self._restore_status, 2)

  def open_settings(self) -> None:
    """Открыть экран настроек (или попап)."""

    # Заглушка для будущего экрана настроек
    self._update_status("Настройки пока не реализованы")

  def _set_state(self, state: str) -> None:
    """Переключить состояние экрана и обновить UI."""

    self._state = state

    if state == "empty":
      self.toolbar.download_enabled = True
      self.toolbar.upload_enabled = False
      self.toolbar.add_enabled = False
      self.toolbar.copy_enabled = False
      self.editor.readonly = True

      self.editor.text = ""
    elif state == "loaded":
      self.toolbar.download_enabled = True
      self.toolbar.upload_enabled = True
      self.toolbar.add_enabled = True
      self.toolbar.copy_enabled = True
      self.editor.readonly = False

    elif state == "loading":
      self.toolbar.download_enabled = False
      self.toolbar.upload_enabled = False
      self.toolbar.add_enabled = False
      self.toolbar.copy_enabled = False
      self.editor.readonly = True

    elif state == "error":
      self.toolbar.download_enabled = True
      self.toolbar.upload_enabled = False
      self.toolbar.add_enabled = False
      self.toolbar.copy_enabled = False
      self.editor.readonly = True

  def _update_status(self, text: str) -> None:
    """Обновить текст статус-бара."""

    self.status_label.text = text

  def _update_status_loaded(self, entry_count: int) -> None:
    """Обновить статус-бар после загрузки."""

    now = datetime.now().strftime("%H:%M")
    self.status_label.text = f"Загружено {now} · {entry_count} записей"

  def _restore_status(self, dt: float) -> None:
    """Восстановить статус-бар после копирования."""

    if self._state == "loaded":
      try:
        vault = json_to_vault(self.editor.text)
        self._update_status_loaded(len(vault.entries))

      except (json.JSONDecodeError, Exception):
        self._update_status("")

    else:
      self._update_status("")
