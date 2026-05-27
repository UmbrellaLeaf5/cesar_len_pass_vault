"""
Основной экран работы с хранилищем.
"""

import json
from datetime import datetime
from typing import TYPE_CHECKING, cast

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen


if TYPE_CHECKING:
  from app.main import CesarVaultApp

from app.screens.add_entry import AddEntryPopup
from cesar_len_pass_vault import json_to_vault, pack_vault, unpack_vault, vault_to_json
from cesar_len_pass_vault.config import config
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

      vault = unpack_vault(blob, app.master_password, primary=True)

      self.editor.text = vault_to_json(vault)
      self._update_status_loaded(len(vault.entries))

      self._set_state("loaded")

    except FileNotFoundError:
      self._set_state("error")
      self._update_status("Vault not found. Create a new one.")
      self.editor.text = ""
      self._set_state("loaded")

    except json.JSONDecodeError as e:
      self._set_state("error")
      self._update_status(
        f"JSON error during decryption: line {e.lineno}, column {e.colno} (char {e.pos})"
      )

    except ConnectionError as e:
      self._set_state("error")
      self._update_status(f"Error: {e}")

    except Exception as e:
      self._set_state("error")
      self._update_status(f"Error: {e}")

  def upload(self) -> None:
    """Encrypt editor content and upload to Yandex Disk."""

    json_str = self.editor.text.strip()

    if not json_str:
      self._update_status("Nothing to save: editor is empty")
      return

    try:
      vault = json_to_vault(json_str)

    except json.JSONDecodeError as e:
      self._update_status(f"JSON error: line {e.lineno}, column {e.colno}")
      return

    self._set_state("loading")

    try:
      app = cast("CesarVaultApp", App.get_running_app())
      pw = app.master_password

      # Основное хранилище - шифрование через cesar_len_key
      primary_blob = pack_vault(vault, pw, primary=True)
      upload(primary_blob)

      # Резервная копия - шифрование через cipher_wrapper
      backup_blob = pack_vault(vault, pw, primary=False)
      upload(backup_blob, path=config.BACKUP_REMOTE_PATH)

      now = datetime.now().strftime("%H:%M")
      self._update_status(f"Saved {now} · {len(vault.entries)} entries")

      self._set_state("loaded")

    except ConnectionError as e:
      self._set_state("error")
      self._update_status(f"Error: {e}")

    except Exception as e:
      self._set_state("error")
      self._update_status(f"Error: {e}")

  def add_entry(self) -> None:
    """Открыть попап добавления записи."""

    popup = AddEntryPopup()
    popup.open()

  def open_settings(self) -> None:
    """Открыть попап с настройками."""

    content = BoxLayout(orientation="vertical", padding=12, spacing=8)

    load_btn = Button(
      text="Load Backup Vault",
      size_hint_y=None,
      height=48,
      background_normal="",
      background_color=(0.2, 0.5, 0.8, 1),
      color=(1, 1, 1, 1),
      on_release=lambda _: self._load_backup(),
    )

    content.add_widget(
      Label(
        text="Settings",
        size_hint_y=None,
        height=32,
        color=(0.9, 0.9, 0.9, 1),
      )
    )

    content.add_widget(load_btn)

    popup = Popup(
      title="",
      content=content,
      size_hint=(0.7, 0.35),
      auto_dismiss=True,
    )

    popup.open()

  def _load_backup(self) -> None:
    """Загрузить резервную копию хранилища (cipher_wrapper)."""

    self._set_state("loading")

    try:
      blob = download(path=config.BACKUP_REMOTE_PATH)
      app = cast("CesarVaultApp", App.get_running_app())

      vault = unpack_vault(blob, app.master_password, primary=False)

      self.editor.text = vault_to_json(vault)
      self._update_status_loaded(len(vault.entries))

      self._set_state("loaded")

    except FileNotFoundError:
      self._set_state("error")
      self._update_status("Backup vault not found")

    except ConnectionError as e:
      self._set_state("error")
      self._update_status(f"Error: {e}")

    except Exception as e:
      self._set_state("error")
      self._update_status(f"Error: {e}")

  def _set_state(self, state: str) -> None:
    """Переключить состояние экрана и обновить UI."""

    self._state = state

    if state == "empty":
      self.toolbar.download_enabled = True
      self.toolbar.upload_enabled = False
      self.toolbar.add_enabled = False
      self.editor.readonly = True

      self.editor.text = ""

    elif state == "loaded":
      self.toolbar.download_enabled = True
      self.toolbar.upload_enabled = True
      self.toolbar.add_enabled = True
      self.editor.readonly = False

    elif state == "loading":
      self.toolbar.download_enabled = False
      self.toolbar.upload_enabled = False
      self.toolbar.add_enabled = False
      self.editor.readonly = True

    elif state == "error":
      self.toolbar.download_enabled = True
      self.toolbar.upload_enabled = False
      self.toolbar.add_enabled = False
      self.editor.readonly = True

  def _update_status(self, text: str) -> None:
    """Обновить текст статус-бара."""

    self.status_label.text = text

  def _update_status_loaded(self, entry_count: int) -> None:
    """Обновить статус-бар после загрузки."""

    now = datetime.now().strftime("%H:%M")
    self.status_label.text = f"Loaded {now} · {entry_count} entries"
