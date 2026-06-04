"""
Основной экран работы с хранилищем.
"""

import json
import re
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
from cesar_len_pass_vault import json_to_vault, vault_to_json
from cesar_len_pass_vault.enums import VaultState
from cesar_len_pass_vault.exceptions import DecryptionError
from cesar_len_pass_vault.models import Vault
from cesar_len_pass_vault.sync import YaConnectionError


# ----------------------------------------------------------------------------------------

Builder.load_file(resource_path("app/screens/vault.kv"))

# ----------------------------------------------------------------------------------------


class VaultScreen(Screen):
  """
  Основной экран работы с хранилищем.
  """

  editor = ObjectProperty(None)
  backup_editor = ObjectProperty(None)
  primary_scroll = ObjectProperty(None)
  backup_scroll = ObjectProperty(None)
  status_label = ObjectProperty(None)
  toolbar = ObjectProperty(None)
  hide_button = ObjectProperty(None)

  preloaded_text: str = ""
  _state: VaultState = VaultState.EMPTY

  _primary_visible_json: str = ""
  _backup_visible_json: str = ""
  _passwords_masked: bool = True

  # --------------------------------------------------------------------------------------

  def on_enter(self, *args: object) -> None:
    if self.preloaded_text:
      self._primary_visible_json = self.preloaded_text
      vault = json_to_vault(self.preloaded_text)

      self.status_label.text = (
        f"Loaded {datetime.now().strftime('%H:%M')} - {len(vault.entries)} entries"
      )

      self._update_ui_by_state(VaultState.LOADED)
      self.preloaded_text = ""

    else:
      self._update_ui_by_state(VaultState.EMPTY)
      self.editor.text = ""
      self.status_label.text = ""

  # MARK: download
  # --------------------------------------------------------------------------------------

  def download(self) -> None:
    """Скачать хранилище с Яндекс.Диска и показать в редакторе."""

    self._update_ui_by_state(VaultState.LOADING)
    self.editor.text = ""

    try:
      primary_json_str, amount = download_primary(self._get_password())
      self._primary_visible_json = primary_json_str

      self._collapse_backup_editor()
      self._update_ui_by_state(VaultState.LOADED)
      self.status_label.text = (
        f"Loaded {datetime.now().strftime('%H:%M')} - {amount} entries"
      )

    except FileNotFoundError:
      self._collapse_backup_editor()
      self._update_ui_by_state(VaultState.LOADED)
      self.status_label.text = "Vault not found. Create a new one."

    except json.JSONDecodeError:
      self._update_ui_by_state(VaultState.EMPTY)
      self.status_label.text = "Invalid master password"

    except (YaConnectionError, Exception) as e:
      self._handle_error(e)

  # MARK: backup
  # --------------------------------------------------------------------------------------

  def _download_backup(self) -> None:
    """Загрузить резервную копию хранилища (cipher_wrapper)."""

    self._update_ui_by_state(VaultState.LOADING)

    try:
      backup_json_str, _count = download_backup(self._get_password())
      self._backup_visible_json = backup_json_str

      # Показываем split: основной редактор остаётся, backup справа
      comparison = self._compare_vaults(self._primary_visible_json, backup_json_str)
      self._update_ui_by_state(VaultState.SPLIT)
      self.status_label.text = comparison

    except FileNotFoundError:
      self._update_ui_by_state(VaultState.EMPTY)
      self.status_label.text = "Backup vault not found"

    except (json.JSONDecodeError, DecryptionError):
      self._update_ui_by_state(VaultState.EMPTY)
      self.status_label.text = "Invalid master password"

    except (YaConnectionError, Exception) as e:
      self._handle_error(e)

  # MARK: upload
  # --------------------------------------------------------------------------------------

  def upload(self) -> None:
    """Открыть попап, проверить рассинхрон и загрузить на Яндекс.Диск."""

    if (
      self._state == VaultState.SPLIT
      and self._primary_visible_json != self._backup_visible_json
    ):
      self.open_sync()
      return

    self._do_upload()

  # --------------------------------------------------------------------------------------

  def _validate_editor_json(self) -> tuple[Vault | None, Vault | None, bool]:
    """Валидирует JSON из редакторов.

    Returns:
      (primary_vault, backup_vault, is_split).
      Если ошибка - (None, None, False), статус уже выставлен.
    """

    primary_json = self._primary_visible_json.strip()

    if not primary_json:
      self.status_label.text = "Nothing to upload: editor is empty"

      return None, None, False

    try:
      primary_vault = json_to_vault(primary_json)

    except json.JSONDecodeError as e:
      self.status_label.text = f"JSON error: line {e.lineno}, column {e.colno}"

      return None, None, False

    is_split = self._state == VaultState.SPLIT
    backup_vault: Vault | None = None

    if is_split:
      backup_json = self._backup_visible_json.strip()

      if not backup_json:
        self.status_label.text = "Backup editor is empty"
        return None, None, False

      try:
        backup_vault = json_to_vault(backup_json)

      except json.JSONDecodeError as e:
        self.status_label.text = (
          f"JSON error in backup: line {e.lineno}, column {e.colno}"
        )

        return None, None, False

    return primary_vault, backup_vault, is_split

  # --------------------------------------------------------------------------------------

  def _do_upload(self) -> None:
    """Зашифровать содержимое редактора и загрузить на Яндекс.Диск."""

    primary_vault, backup_vault, is_split = self._validate_editor_json()

    if primary_vault is None:
      return

    self._update_ui_by_state(VaultState.LOADING)

    try:
      pw = self._get_password()

      upload_vault(
        primary_vault,
        backup_vault if (is_split and backup_vault is not None) else primary_vault,
        pw,
      )

      self._primary_visible_json = vault_to_json(primary_vault)

      if is_split and backup_vault is not None:
        self._backup_visible_json = vault_to_json(backup_vault)

      else:
        self._backup_visible_json = self._primary_visible_json

      self.status_label.text = (
        f"Saved {datetime.now().strftime('%H:%M')} - {len(primary_vault.entries)} entries"
      )

      self._update_ui_by_state(VaultState.SPLIT if is_split else VaultState.LOADED)

    except (YaConnectionError, Exception) as e:
      self._handle_error(e)

  # MARK: popup
  # --------------------------------------------------------------------------------------

  def open_add_entry(self) -> None:
    """Открыть попап добавления записи."""

    was_masked = self._passwords_masked

    if was_masked:
      self._toggle_passwords()

    popup = AddEntryPopup()
    popup.target_editor = (
      self.backup_editor if self._state == VaultState.SPLIT else self.editor
    )

    popup.bind(on_dismiss=lambda *args: self._on_add_entry_dismissed(was_masked))  # type: ignore[arg-type]
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

  def _compare_vaults(self, primary_json: str, backup_json: str) -> str:
    """Сравнить primary и backup, вернуть сообщение для статус-бара."""

    primary_data = json.loads(primary_json)
    backup_data = json.loads(backup_json)

    primary_map: dict[str, dict] = {}
    for e in primary_data.get("entries", []):
      primary_map[e["service"].casefold()] = e

    backup_map: dict[str, dict] = {}
    for e in backup_data.get("entries", []):
      backup_map[e["service"].casefold()] = e

    diffs: list[str] = []

    for svc_key, p_entry in primary_map.items():
      b_entry = backup_map.get(svc_key)

      if b_entry is None:
        diffs.append(f"{p_entry['service']}: missing in backup")
        continue

      differing_fields: list[str] = []

      for field in ("login", "password", "notes"):
        if p_entry.get(field) != b_entry.get(field):
          differing_fields.append(field)

      if differing_fields:
        diffs.append(f"{p_entry['service']}: {', '.join(differing_fields)}")

    for svc_key, b_entry in backup_map.items():
      if svc_key not in primary_map:
        diffs.append(f"{b_entry['service']}: missing in primary")

    if not diffs:
      return "Backup matches primary - no differences"

    if len(diffs) <= 3:
      return "Backup differs: " + "; ".join(diffs)

    shown = diffs[:3]
    remaining = len(diffs) - 3

    return f"Backup differs: {'; '.join(shown)}; +{remaining} more"

  # --------------------------------------------------------------------------------------

  def _handle_sync_choice(self, choice: str) -> None:
    """Синхронизировать редакторы по выбору пользователя и загрузить."""

    if choice == "primary":
      self._backup_visible_json = self._primary_visible_json

    elif choice == "backup":
      self._primary_visible_json = self._backup_visible_json

    self._do_upload()

  # --------------------------------------------------------------------------------------

  def _handle_error(self, error: Exception) -> None:
    """Обработать ошибку сети или общую ошибку."""

    if isinstance(error, YaConnectionError):
      self.status_label.text = f"Connection error: {error}"

    else:
      self.status_label.text = f"Error: {error}"

    self._update_ui_by_state(VaultState.EMPTY)

  # --------------------------------------------------------------------------------------

  def _get_password(self) -> str:
    """Получить мастер-пароль из приложения."""

    app = cast("CesarVaultApp", App.get_running_app())

    return app.master_password

  # --------------------------------------------------------------------------------------

  def _collapse_backup_editor(self) -> None:
    """Скрыть backup редактор (возврат к одному редактору)."""

    self.backup_editor.text = ""
    self.backup_scroll.size_hint_x = 0
    self.backup_scroll.opacity = 0
    self.backup_editor.readonly = True

    self.primary_scroll.size_hint_x = 1

  # --------------------------------------------------------------------------------------

  def _on_add_entry_dismissed(self, was_masked: bool) -> None:
    """После закрытия попапа добавить записи - обновить _primary/_backup_visible_json."""

    if self._state == VaultState.SPLIT:
      self._backup_visible_json = self.backup_editor.text
    else:
      self._primary_visible_json = self.editor.text

    if was_masked:
      self._toggle_passwords()

  # --------------------------------------------------------------------------------------

  def _toggle_passwords(self) -> None:
    """Переключить режим show/hide для всех редакторов."""

    self._passwords_masked = not self._passwords_masked
    self._apply_hide_state()

  # --------------------------------------------------------------------------------------

  def _apply_hide_state(self) -> None:
    """Применить текущее состояние _passwords_masked к редакторам."""

    self.hide_button.text = "Show" if self._passwords_masked else "Hide"
    is_split = self._state == VaultState.SPLIT

    if self._passwords_masked:
      hidden_primary = self._mask_passwords(self._primary_visible_json)
      hidden_backup = self._mask_passwords(self._backup_visible_json)

      if self.editor.text != hidden_primary:
        self.editor.text = hidden_primary

      self.editor.readonly = True

      if is_split:
        if self.backup_editor.text != hidden_backup:
          self.backup_editor.text = hidden_backup

        self.backup_editor.readonly = True

    else:
      if self.editor.text != self._primary_visible_json:
        self.editor.text = self._primary_visible_json

      self.editor.readonly = False
      self.editor.focus = True

      if is_split:
        if self.backup_editor.text != self._backup_visible_json:
          self.backup_editor.text = self._backup_visible_json

        self.backup_editor.readonly = False

  # --------------------------------------------------------------------------------------

  def _mask_passwords(self, json_str: str) -> str:
    """Заменить все значения password на ***."""

    return re.sub(r'("password"\s*:\s*)"[^"]*"', r'\1"***"', json_str)

  # --------------------------------------------------------------------------------------

  def _on_editor_text(self) -> None:
    """При изменении текста в show-режиме - обновить _primary_visible_json."""

    if not self._passwords_masked:
      self._primary_visible_json = self.editor.text

  # --------------------------------------------------------------------------------------

  def _on_backup_editor_text(self) -> None:
    """При изменении текста backup в show-режиме - обновить _backup_visible_json."""

    if not self._passwords_masked and self._state == VaultState.SPLIT:
      self._backup_visible_json = self.backup_editor.text

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

        self.primary_scroll.size_hint_x = 1
        self._collapse_backup_editor()

      case VaultState.LOADING:
        self.toolbar.download_enabled = False
        self.toolbar.upload_enabled = False
        self.toolbar.add_enabled = False
        self.editor.readonly = True

        self.primary_scroll.size_hint_x = 1

      case VaultState.LOADED:
        self.toolbar.download_enabled = True
        self.toolbar.upload_enabled = True
        self.toolbar.add_enabled = True

        self._collapse_backup_editor()
        self._apply_hide_state()

      case VaultState.SPLIT:
        self.toolbar.download_enabled = True
        self.toolbar.upload_enabled = True
        self.toolbar.add_enabled = True

        self.primary_scroll.size_hint_x = 0.5
        self.backup_scroll.size_hint_x = 0.5
        self.backup_scroll.opacity = 1

        self._apply_hide_state()
