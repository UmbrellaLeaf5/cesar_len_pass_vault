"""
Основной экран работы с хранилищем.
"""

import json
from datetime import datetime
from typing import TYPE_CHECKING, cast

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen


if TYPE_CHECKING:
  from app.main import CesarVaultApp

from app.screens.add_entry import AddEntryPopup
from app.screens.settings_popup import SettingsPopup
from cesar_len_pass_vault import json_to_vault, pack_vault, unpack_vault, vault_to_json
from cesar_len_pass_vault.config import config
from cesar_len_pass_vault.enums import VaultState
from cesar_len_pass_vault.sync import YaConnectionError, download, upload


Builder.load_file("app/screens/vault.kv")


class VaultScreen(Screen):
  """
  Основной экран работы с хранилищем.
  """

  editor = ObjectProperty(None)
  status_label = ObjectProperty(None)
  toolbar = ObjectProperty(None)

  _state: VaultState = VaultState.LOADED

  def __init__(self, **kwargs) -> None:
    super().__init__(**kwargs)

    # Начальное состояние UI (до загрузки хранилища)
    self.toolbar.download_enabled = True
    self.toolbar.upload_enabled = False
    self.toolbar.add_enabled = False
    self.editor.readonly = True

    self.editor.text = ""
    self.status_label.text = ""

  def download(self) -> None:
    """Скачать хранилище с Яндекс.Диска и показать в редакторе."""

    self._update_ui_by_state(VaultState.LOADING)
    self.editor.text = ""

    try:
      blob = download()
      app = cast("CesarVaultApp", App.get_running_app())

      vault = unpack_vault(blob, app.master_password, primary=True)
      self.editor.text = vault_to_json(vault)

      self.status_label.text = (
        f"Loaded {datetime.now().strftime('%H:%M')} - {len(vault.entries)} entries"
      )
      self._update_ui_by_state(VaultState.LOADED)

    except FileNotFoundError:
      self._update_ui_by_state(VaultState.LOADED)
      self.status_label.text = "Vault not found. Create a new one."

    except json.JSONDecodeError as e:
      self._update_ui_by_state(VaultState.ERROR)
      self.status_label.text = (
        f"JSON error during decryption: line {e.lineno}, column {e.colno} (char {e.pos})"
      )

    except YaConnectionError as e:
      self._update_ui_by_state(VaultState.ERROR)
      self.status_label.text = f"Connection error: {e}"

    except Exception as e:
      self._update_ui_by_state(VaultState.ERROR)
      self.status_label.text = f"Error: {e}"

  def upload(self) -> None:
    """Зашифровать содержимое редактора и загрузить на Яндекс.Диск."""

    json_str = self.editor.text.strip()

    if not json_str:
      self.status_label.text = "Nothing to upload: editor is empty"
      return

    try:
      vault = json_to_vault(json_str)

    except json.JSONDecodeError as e:
      self.status_label.text = f"JSON error: line {e.lineno}, column {e.colno}"
      return

    self._update_ui_by_state(VaultState.LOADING)

    try:
      app = cast("CesarVaultApp", App.get_running_app())
      pw = app.master_password

      # Основное хранилище - шифрование через cesar_len_key
      primary_blob = pack_vault(vault, pw, primary=True)
      upload(primary_blob)

      # Резервная копия - шифрование через cipher_wrapper
      backup_blob = pack_vault(vault, pw, primary=False)
      upload(backup_blob, path=config.BACKUP_REMOTE_PATH)

      self._update_ui_by_state(VaultState.LOADED)
      self.status_label.text = (
        f"Saved {datetime.now().strftime('%H:%M')} - {len(vault.entries)} entries"
      )

    except YaConnectionError as e:
      self._update_ui_by_state(VaultState.ERROR)
      self.status_label.text = f"Connection error: {e}"

    except Exception as e:
      self._update_ui_by_state(VaultState.ERROR)
      self.status_label.text = f"Error: {e}"

  def add_entry(self) -> None:
    """Открыть попап добавления записи."""

    popup = AddEntryPopup()
    popup.open()

  def open_settings(self) -> None:
    """Открыть попап с настройками."""

    popup = SettingsPopup()
    popup.backup_callback = self._download_backup
    popup.open()

  def _download_backup(self) -> None:
    """Загрузить резервную копию хранилища (cipher_wrapper)."""

    self._update_ui_by_state(VaultState.LOADING)

    try:
      blob = download(path=config.BACKUP_REMOTE_PATH)

      app = cast("CesarVaultApp", App.get_running_app())

      vault = unpack_vault(blob, app.master_password, primary=False)
      self.editor.text = vault_to_json(vault)

      self._update_ui_by_state(VaultState.LOADED)
      self.status_label.text = (
        f"Loaded backup {datetime.now().strftime('%H:%M')} - {len(vault.entries)} entries"
      )

    except FileNotFoundError:
      self._update_ui_by_state(VaultState.ERROR)
      self.status_label.text = "Backup vault not found"

    except YaConnectionError as e:
      self._update_ui_by_state(VaultState.ERROR)
      self.status_label.text = f"Connection error: {e}"

    except Exception as e:
      self._update_ui_by_state(VaultState.ERROR)
      self.status_label.text = f"Error: {e}"

  def _update_ui_by_state(self, state: VaultState) -> None:
    """Переключить состояние экрана и обновить UI."""

    self._state = state

    match state:
      case VaultState.LOADING:
        self.toolbar.download_enabled = False
        self.toolbar.upload_enabled = False
        self.toolbar.add_enabled = False
        self.editor.readonly = True

      case VaultState.LOADED:
        self.toolbar.download_enabled = True
        self.toolbar.upload_enabled = True
        self.toolbar.add_enabled = True
        self.editor.readonly = False

      case VaultState.ERROR:
        self.toolbar.download_enabled = True
        self.toolbar.upload_enabled = False
        self.toolbar.add_enabled = False
        self.editor.readonly = True
