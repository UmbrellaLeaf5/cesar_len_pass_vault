"""
Экран ввода мастер-пароля.
"""

import json
from typing import TYPE_CHECKING, cast

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen

from app.screens.mixins import ErrorScreenMixin
from app.services.vault_ops import download_primary
from app.utils import resource_path
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

  # --------------------------------------------------------------------------------------

  def on_enter(self, *args: object) -> None:
    self.password_input.text = ""
    self.password_input.focus = True
    self._clear_error()

    cast("CesarVaultApp", App.get_running_app()).master_password = ""

  # --------------------------------------------------------------------------------------

  def unlock(self) -> None:
    """Обработчик нажатия кнопки Unlock."""

    password = self.password_input.text.strip()

    if not password:
      self._set_error("Enter password")
      return

    app = cast("CesarVaultApp", App.get_running_app())
    app.master_password = password

    # Пытаемся скачать и расшифровать хранилище
    try:
      primary_json_str, _ = download_primary(password)

      # Успех - передаём данные на VaultScreen
      vault_screen = cast("VaultScreen", self.manager.get_screen("vault"))
      vault_screen.preloaded_text = primary_json_str
      self.manager.current = "vault"

    except FileNotFoundError:
      # Хранилище ещё не создано - переходим с пустым редактором
      vault_screen = cast("VaultScreen", self.manager.get_screen("vault"))
      vault_screen.preloaded_text = ""
      self.manager.current = "vault"

    except json.JSONDecodeError:
      self._set_error("Invalid master password")

    except YaConnectionError as e:
      self._set_error(f"Connection error: {e}")

    except Exception as e:
      self._set_error(f"Error: {e}")
