"""
Экран ввода мастер-пароля.
"""

import json
from typing import TYPE_CHECKING, cast

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen

from app.screens.mixins import ErrorScreenMixin
from app.services.vault_ops import download_primary
from app.utils import resource_path
from cesar_len_pass_vault.exceptions import DecryptionError
from cesar_len_pass_vault.sync import YaConnectionError


# ----------------------------------------------------------------------------------------

if TYPE_CHECKING:
  from app.screens.vault import VaultScreen
  from main import CesarVaultApp


# ----------------------------------------------------------------------------------------

Builder.load_file(resource_path("app/screens/unlock.kv"))

# ----------------------------------------------------------------------------------------


class UnlockScreen(Screen, ErrorScreenMixin):
  """
  Экран ввода мастер-пароля.
  """

  password_input = ObjectProperty(None)
  unlock_button = ObjectProperty(None)

  _failed_attempts: int = 0

  # --------------------------------------------------------------------------------------

  def on_enter(self, *args: object) -> None:
    self.password_input.text = ""
    self.password_input.focus = True
    self._failed_attempts = 0

    self._clear_error()

    cast("CesarVaultApp", App.get_running_app()).master_password = ""

  # --------------------------------------------------------------------------------------

  def unlock(self) -> None:
    """Обработчик нажатия кнопки Unlock."""

    if self.password_input.readonly:
      return

    password = self.password_input.text.strip()

    if not password:
      self._set_error("Enter password")
      return

    app = cast("CesarVaultApp", App.get_running_app())
    app.master_password = password

    vault_screen = cast("VaultScreen", self.manager.get_screen("vault"))

    # Пытаемся скачать и расшифровать хранилище
    try:
      primary_json_str, _ = download_primary(password)

      # Успех - передаём данные на VaultScreen
      self._failed_attempts = 0
      vault_screen.preloaded_text = primary_json_str
      self.manager.current = "vault"

    except FileNotFoundError:
      # Хранилище ещё не создано - переходим с пустым редактором
      self._failed_attempts = 0
      vault_screen.preloaded_text = ""
      self.manager.current = "vault"

    except (json.JSONDecodeError, DecryptionError):
      delay = min(2**self._failed_attempts, 16)
      self._failed_attempts += 1

      self._set_error(f"Invalid master password - wait {delay}s")

      self.password_input.readonly = True
      self.unlock_button.disabled = True

      Clock.schedule_once(self._enable_unlock, delay)

    except YaConnectionError as e:
      self._set_error(f"Connection error: {e}")

    except Exception as e:
      self._set_error(f"Error: {e}")

  # MARK: private
  # --------------------------------------------------------------------------------------

  def _enable_unlock(self, dt: float) -> None:
    """Разблокировать ввод после задержки."""

    self.password_input.readonly = False
    self.unlock_button.disabled = False
    self.password_input.text = ""
    self.password_input.focus = True
