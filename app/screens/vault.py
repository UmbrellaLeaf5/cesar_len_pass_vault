"""
Основной экран работы с хранилищем.
"""

import json
from datetime import datetime
from typing import TYPE_CHECKING, cast

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen

from app.popups.add_entry import AddEntryPopup
from app.popups.settings import SettingsPopup
from app.popups.sync import SyncPopup
from app.popups.unsaved_changes import UnsavedChangesPopup
from app.services.vault_ops import download_backup, download_primary, upload_vault
from app.utils import resource_path
from cesar_len_pass_vault import json_to_vault, vault_to_json
from cesar_len_pass_vault.enums import VaultState
from cesar_len_pass_vault.exceptions import DecryptionError
from cesar_len_pass_vault.models import Vault
from cesar_len_pass_vault.sync import YaConnectionError


if TYPE_CHECKING:
  from main import CesarVaultApp

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
  preloaded_modified_at: datetime | None = None
  _state: VaultState = VaultState.EMPTY

  _primary_visible_json: str = ""
  _backup_visible_json: str = ""
  _last_saved_primary_json: str = ""
  _last_saved_backup_json: str = ""
  _passwords_masked: bool = True

  _unsaved_popup: UnsavedChangesPopup | None = None

  _FULL_WIDTH: float = 1.0
  _HALF_WIDTH: float = 0.5
  _HIDDEN: float = 0.0
  _MAX_DIFFS_SHOWN: int = 3

  # --------------------------------------------------------------------------------------

  def on_enter(self, *args: object) -> None:
    Window.unbind(on_request_close=self._on_request_close)

    if self.preloaded_text:
      self._primary_visible_json = self.preloaded_text
      self._last_saved_primary_json = self.preloaded_text

      try:
        vault = json_to_vault(self.preloaded_text)

      except json.JSONDecodeError:
        self._update_ui_by_state(VaultState.EMPTY)
        self.editor.text = ""
        self.status_label.text = "Failed to parse vault data"
        self.preloaded_text = ""
        Window.bind(on_request_close=self._on_request_close)

        return

      self.status_label.text = self._format_download_status(
        len(vault.entries), self.preloaded_modified_at
      )

      self._update_ui_by_state(VaultState.LOADED)
      self.preloaded_text = ""
      self.preloaded_modified_at = None

    else:
      self._update_ui_by_state(VaultState.EMPTY)
      self.editor.text = ""
      self.status_label.text = ""

    Window.bind(on_request_close=self._on_request_close)

  # MARK: download
  # --------------------------------------------------------------------------------------

  def _format_download_status(self, amount: int, modified_at: datetime | None) -> str:
    """Сформировать статус скачивания с временем последнего upload."""

    downloaded_at = datetime.now().strftime("%H:%M")

    if modified_at is None:
      return f"Downloaded: {downloaded_at} - {amount} entries"

    last_uploaded_at = modified_at.astimezone().strftime("%H:%M - %d.%m.%Y")

    return f"Downloaded: {downloaded_at} - {amount} entries\nUploaded: {last_uploaded_at}"

  # --------------------------------------------------------------------------------------

  def download(self) -> None:
    """Скачать хранилище с Яндекс.Диска и показать в редакторе."""

    self._update_ui_by_state(VaultState.LOADING)
    self.editor.text = ""

    try:
      primary_json_str, amount, modified_at = download_primary(self._get_password())
      self._primary_visible_json = primary_json_str
      self._last_saved_primary_json = primary_json_str

      self._collapse_backup_editor()
      self._update_ui_by_state(VaultState.LOADED)
      self.status_label.text = self._format_download_status(amount, modified_at)

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
      backup_json_str, _count, _modified_at = download_backup(self._get_password())
      self._backup_visible_json = backup_json_str

      # Показываем split: основной редактор остаётся, backup справа
      comparison = self._compare_vaults(self._primary_visible_json, backup_json_str)
      self._update_ui_by_state(VaultState.SPLIT)
      self.status_label.text = comparison

    except FileNotFoundError:
      self._collapse_backup_editor()
      self._update_ui_by_state(VaultState.LOADED)
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

    if self._state == VaultState.SPLIT and self._primary_visible_json != self._backup_visible_json:
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

    primary_vault = self._parse_vault_from_json(self._primary_visible_json, "editor")

    if primary_vault is None:
      return None, None, False

    is_split = self._state == VaultState.SPLIT
    backup_vault: Vault | None = None

    if is_split:
      backup_vault = self._parse_vault_from_json(self._backup_visible_json, "Backup editor")

      if backup_vault is None:
        return None, None, False

    return primary_vault, backup_vault, is_split

  # --------------------------------------------------------------------------------------

  def _parse_vault_from_json(self, json_str: str, label: str) -> Vault | None:
    """Распарсить JSON-строку в Vault с сообщением об ошибке в status_label."""

    text = json_str.strip()

    if not text:
      self.status_label.text = f"{label} is empty"

      return None

    try:
      return json_to_vault(text)

    except json.JSONDecodeError as e:
      self.status_label.text = f"JSON error in {label.lower()}: line {e.lineno}, column {e.colno}"

      return None

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

      self._last_saved_primary_json = self._primary_visible_json
      self._last_saved_backup_json = self._backup_visible_json

      self.status_label.text = (
        f"Uploaded {datetime.now().strftime('%H:%M')} - {len(primary_vault.entries)} entries"
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
    popup.target_editor = self.backup_editor if self._state == VaultState.SPLIT else self.editor

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

  @property
  def _has_unsaved_changes(self) -> bool:
    """True если _visible_json отличается от последнего сохранённого."""

    return (
      self._primary_visible_json != self._last_saved_primary_json
      or self._backup_visible_json != self._last_saved_backup_json
    )

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

    if len(diffs) <= self._MAX_DIFFS_SHOWN:
      return "Backup differs: " + "; ".join(diffs)

    shown = diffs[: self._MAX_DIFFS_SHOWN]
    remaining = len(diffs) - self._MAX_DIFFS_SHOWN

    return f"Backup differs: {'; '.join(shown)}; +{remaining} more"

  # --------------------------------------------------------------------------------------

  def _handle_sync_choice(self, choice: str) -> None:
    """Синхронизировать редакторы по выбору пользователя и загрузить."""

    if choice == "primary":
      self._backup_visible_json = self._primary_visible_json

    elif choice == "backup":
      self._primary_visible_json = self._backup_visible_json

    else:
      return

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

  def _on_request_close(self, *args: object) -> bool:
    """Перехват закрытия окна — проверить несохранённые изменения."""

    if self._has_unsaved_changes:
      self._unsaved_popup = UnsavedChangesPopup()

      self._unsaved_popup.on_save_close = self._save_and_close
      self._unsaved_popup.on_discard = self._discard_and_close

      self._unsaved_popup.open()

      return True

    return False

  # --------------------------------------------------------------------------------------

  def _save_and_close(self) -> None:
    """Сохранить изменения и закрыть приложение."""

    before = self._last_saved_primary_json
    self._do_upload()

    if self._last_saved_primary_json != before:
      self._discard_and_close()

  # --------------------------------------------------------------------------------------

  def _discard_and_close(self) -> None:
    """Закрыть без сохранения."""

    self._unsaved_popup = None

    app = App.get_running_app()
    assert app is not None
    app.stop()

  # --------------------------------------------------------------------------------------

  def _get_password(self) -> str:
    """Получить мастер-пароль из приложения."""

    app = cast("CesarVaultApp", App.get_running_app())

    return app.master_password

  # --------------------------------------------------------------------------------------

  def _collapse_backup_editor(self) -> None:
    """Скрыть backup редактор (возврат к одному редактору)."""

    self.backup_editor.text = ""
    self.backup_scroll.size_hint_x = self._HIDDEN
    self.backup_scroll.opacity = self._HIDDEN
    self.backup_editor.readonly = True

    self.primary_scroll.size_hint_x = self._FULL_WIDTH

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
      self._set_editor_display(self.editor, hidden_primary, readonly=True, focus=False)

      if is_split:
        hidden_backup = self._mask_passwords(self._backup_visible_json)
        self._set_editor_display(self.backup_editor, hidden_backup, readonly=True, focus=False)

    else:
      self._set_editor_display(self.editor, self._primary_visible_json, readonly=False, focus=True)

      if is_split:
        self._set_editor_display(
          self.backup_editor,
          self._backup_visible_json,
          readonly=False,
          focus=False,
        )

  # --------------------------------------------------------------------------------------

  def _set_editor_display(self, editor, text: str, readonly: bool, focus: bool) -> None:
    """Установить текст и состояние одного редактора с защитой от лишнего on_text."""

    if editor.text != text:
      editor.text = text

    editor.readonly = readonly

    if focus:
      editor.focus = True

  # --------------------------------------------------------------------------------------

  def _mask_passwords(self, json_str: str) -> str:
    """Заменить все значения password на ***."""

    try:
      data = json.loads(json_str)

    except json.JSONDecodeError:
      return json_str

    for entry in data.get("entries", []):
      if "password" in entry:
        entry["password"] = "***"

    return json.dumps(data, ensure_ascii=False, indent=2)

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

        self._collapse_backup_editor()

      case VaultState.LOADING:
        self.toolbar.download_enabled = False
        self.toolbar.upload_enabled = False
        self.toolbar.add_enabled = False
        self.editor.readonly = True

        self.primary_scroll.size_hint_x = self._FULL_WIDTH

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

        self.primary_scroll.size_hint_x = self._HALF_WIDTH
        self.backup_scroll.size_hint_x = self._HALF_WIDTH
        self.backup_scroll.opacity = self._FULL_WIDTH

        self._apply_hide_state()
