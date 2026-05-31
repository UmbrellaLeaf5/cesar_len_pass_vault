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

from app.utils import resource_path


if TYPE_CHECKING:
  from main import CesarVaultApp

from app.popups.add_entry import AddEntryPopup
from app.popups.settings import SettingsPopup
from app.popups.sync import SyncPopup
from app.services.vault_ops import download_backup, download_primary, upload_vault
from cesar_len_pass_vault import json_to_vault
from cesar_len_pass_vault.enums import VaultState
from cesar_len_pass_vault.exceptions import DecryptionError
from cesar_len_pass_vault.models import Vault
from cesar_len_pass_vault.sync import YaConnectionError


# --------------------------------------------------------------------------------------

Builder.load_file(resource_path("app/screens/vault.kv"))

# --------------------------------------------------------------------------------------


class VaultScreen(Screen):
  """
  Основной экран работы с хранилищем.
  """

  editor = ObjectProperty(None)
  backup_editor = ObjectProperty(None)
  status_label = ObjectProperty(None)
  toolbar = ObjectProperty(None)

  preloaded_text: str = ""

  _state: VaultState = VaultState.EMPTY

  # --------------------------------------------------------------------------------------

  def on_enter(self, *args: object) -> None:
    if self.preloaded_text:
      self.editor.text = self.preloaded_text
      vault = json_to_vault(self.preloaded_text)

      self.status_label.text = (
        f"Loaded {datetime.now().strftime('%H:%M')} - {len(vault.entries)} entries"
      )

      self._update_ui_by_state(VaultState.LOADED)
      self.preloaded_text = ""

    else:
      self.toolbar.download_enabled = True
      self.toolbar.upload_enabled = False
      self.toolbar.add_enabled = False
      self.editor.readonly = True
      self.editor.text = ""
      self.status_label.text = ""

      self._hide_backup_editor()

  # MARK: download
  # --------------------------------------------------------------------------------------

  def download(self) -> None:
    """Скачать хранилище с Яндекс.Диска и показать в редакторе."""

    self._update_ui_by_state(VaultState.LOADING)
    self.editor.text = ""

    try:
      primary_json_str, amount = download_primary(self._get_password())
      self.editor.text = primary_json_str

      self._hide_backup_editor()
      self._update_ui_by_state(VaultState.LOADED)
      self.status_label.text = (
        f"Loaded {datetime.now().strftime('%H:%M')} - {amount} entries"
      )

    except FileNotFoundError:
      self._hide_backup_editor()
      self._update_ui_by_state(VaultState.LOADED)
      self.status_label.text = "Vault not found. Create a new one."

    except json.JSONDecodeError:
      self._update_ui_by_state(VaultState.EMPTY)
      self.status_label.text = "Invalid master password"

    except YaConnectionError as e:
      self._update_ui_by_state(VaultState.EMPTY)
      self.status_label.text = f"Connection error: {e}"

    except Exception as e:
      self._update_ui_by_state(VaultState.EMPTY)
      self.status_label.text = f"Error: {e}"

  # MARK: backup
  # --------------------------------------------------------------------------------------

  def _download_backup(self) -> None:
    """Загрузить резервную копию хранилища (cipher_wrapper)."""

    self._update_ui_by_state(VaultState.LOADING)

    try:
      backup_json_str, count = download_backup(self._get_password())
      self.backup_editor.text = backup_json_str

      # Показываем split: основной редактор остаётся, backup справа
      self._update_ui_by_state(VaultState.SPLIT)
      self.status_label.text = (
        f"Loaded backup {datetime.now().strftime('%H:%M')} - {count} entries"
      )

    except FileNotFoundError:
      self._update_ui_by_state(VaultState.EMPTY)
      self.status_label.text = "Backup vault not found"

    except (json.JSONDecodeError, DecryptionError):
      self._update_ui_by_state(VaultState.EMPTY)
      self.status_label.text = "Invalid master password"

    except YaConnectionError as e:
      self._update_ui_by_state(VaultState.EMPTY)
      self.status_label.text = f"Connection error: {e}"

    except Exception as e:
      self._update_ui_by_state(VaultState.EMPTY)
      self.status_label.text = f"Error: {e}"

  # MARK: upload
  # --------------------------------------------------------------------------------------

  def upload(self) -> None:
    """Открыть попап, проверить рассинхрон и загрузить на Яндекс.Диск."""

    if self._state == VaultState.SPLIT and self.editor.text != self.backup_editor.text:
      self.open_sync()
      return

    self._do_upload()

  # --------------------------------------------------------------------------------------

  def _do_upload(self) -> None:
    """Зашифровать содержимое редактора и загрузить на Яндекс.Диск."""

    primary_json = self.editor.text.strip()

    if not primary_json:
      self.status_label.text = "Nothing to upload: editor is empty"

      return

    try:
      primary_vault = json_to_vault(primary_json)

    except json.JSONDecodeError as e:
      self.status_label.text = f"JSON error: line {e.lineno}, column {e.colno}"

      return

    # В split режиме - валидируем и backup редактор
    is_split = self._state == VaultState.SPLIT
    backup_vault: Vault | None = None

    if is_split:
      backup_json = self.backup_editor.text.strip()

      if not backup_json:
        self.status_label.text = "Backup editor is empty"
        return

      try:
        backup_vault = json_to_vault(backup_json)

      except json.JSONDecodeError as e:
        self.status_label.text = (
          f"JSON error in backup: line {e.lineno}, column {e.colno}"
        )

        return

    self._update_ui_by_state(VaultState.LOADING)

    try:
      pw = self._get_password()

      # Загружаем оба хранилища
      upload_vault(
        primary_vault,
        backup_vault if (is_split and backup_vault is not None) else primary_vault,
        pw,
      )

      self.status_label.text = (
        f"Saved {datetime.now().strftime('%H:%M')} - {len(primary_vault.entries)} entries"
      )

      self._update_ui_by_state(VaultState.SPLIT if is_split else VaultState.LOADED)

    except YaConnectionError as e:
      self._update_ui_by_state(VaultState.EMPTY)
      self.status_label.text = f"Connection error: {e}"

    except Exception as e:
      self._update_ui_by_state(VaultState.EMPTY)
      self.status_label.text = f"Error: {e}"

  # MARK: popup
  # --------------------------------------------------------------------------------------

  def open_add_entry(self) -> None:
    """Открыть попап добавления записи."""

    popup = AddEntryPopup()

    popup.target_editor = (
      self.backup_editor if self._state == VaultState.SPLIT else self.editor
    )

    popup.open()

  # --------------------------------------------------------------------------------------

  def open_settings(self) -> None:
    """Открыть попап с настройками."""

    popup = SettingsPopup()
    popup.backup_callback = self._download_backup
    popup.open()

  # --------------------------------------------------------------------------------------

  def open_sync(self) -> None:
    """Открыть попап с синхронизацией."""

    popup = SyncPopup()
    popup.on_choice = self._handle_sync_choice
    popup.open()

  # MARK: private
  # --------------------------------------------------------------------------------------

  def _handle_sync_choice(self, choice: str) -> None:
    """Синхронизировать редакторы по выбору пользователя и загрузить."""

    if choice == "primary":
      self.backup_editor.text = self.editor.text

    elif choice == "backup":
      self.editor.text = self.backup_editor.text

    self._do_upload()

  # --------------------------------------------------------------------------------------

  def _get_password(self) -> str:
    """Получить мастер-пароль из приложения."""

    app = cast("CesarVaultApp", App.get_running_app())

    return app.master_password

  # --------------------------------------------------------------------------------------

  def _hide_backup_editor(self) -> None:
    """Скрыть backup редактор (возврат к одному редактору)."""

    self.backup_editor.text = ""
    self.backup_editor.size_hint_x = 0
    self.backup_editor.opacity = 0
    self.backup_editor.readonly = True

    self.editor.size_hint_x = 1

  # MARK: state
  # --------------------------------------------------------------------------------------

  def _update_ui_by_state(self, state: VaultState) -> None:
    """Переключить состояние экрана и обновить UI."""

    self._state = state

    match state:
      case VaultState.EMPTY:
        self.toolbar.download_enabled = True
        self.toolbar.upload_enabled = False
        self.toolbar.add_enabled = False
        self.editor.readonly = True

        self._hide_backup_editor()

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

        self._hide_backup_editor()

      case VaultState.SPLIT:
        self.toolbar.download_enabled = True
        self.toolbar.upload_enabled = True
        self.toolbar.add_enabled = True
        self.editor.readonly = False

        self.editor.size_hint_x = 0.5
        self.backup_editor.size_hint_x = 0.5
        self.backup_editor.opacity = 1
        self.backup_editor.readonly = False
