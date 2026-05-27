"""
Экран ввода мастер-пароля.
"""

import json
from typing import TYPE_CHECKING, cast

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.screenmanager import Screen

from cesar_len_pass_vault import unpack_vault, vault_to_json
from cesar_len_pass_vault.exceptions import DecryptionError
from cesar_len_pass_vault.sync import YaConnectionError, download


if TYPE_CHECKING:
  from app.main import CesarVaultApp
  from app.screens.vault import VaultScreen


Builder.load_file("app/screens/unlock.kv")


class UnlockScreen(Screen):
  """
  Экран ввода мастер-пароля.
  """

  password_input = ObjectProperty(None)
  error_label = ObjectProperty(None)

  _bg_color = ListProperty([0, 0, 0, 1])  # Чёрный по умолчанию

  def unlock(self) -> None:
    """Обработчик нажатия кнопки Unlock."""

    password = self.password_input.text.strip()

    if not password:
      self.error_label.text = "Enter password"
      self.error_label.opacity = 1
      self._set_error_background()

      return

    app = cast("CesarVaultApp", App.get_running_app())
    app.master_password = password

    # Пытаемся скачать и расшифровать хранилище
    try:
      blob = download()
      vault = unpack_vault(blob, password, primary=True)
      json_str = vault_to_json(vault)

      # Успех - передаём данные на VaultScreen
      vault_screen = cast("VaultScreen", self.manager.get_screen("vault"))
      vault_screen.preloaded_text = json_str
      self.manager.current = "vault"

    except FileNotFoundError:
      # Хранилище ещё не создано - переходим с пустым редактором
      vault_screen = cast("VaultScreen", self.manager.get_screen("vault"))
      vault_screen.preloaded_text = ""
      self.manager.current = "vault"

    except (json.JSONDecodeError, DecryptionError):
      self.error_label.text = "Invalid master password"
      self.error_label.opacity = 1
      self._set_error_background()

    except YaConnectionError as e:
      self.error_label.text = f"Connection error: {e}"
      self.error_label.opacity = 1
      self._set_error_background()

    except Exception as e:
      self.error_label.text = f"Error: {e}"
      self.error_label.opacity = 1
      self._set_error_background()

  def _set_error_background(self) -> None:
    """Включить/выключить красный фон ошибки."""

    self._bg_color = [0.4, 0.05, 0.05, 1]  # Бледно-красный

  def on_enter(self, *args: object) -> None:
    """Сброс состояния при входе на экран."""

    self.password_input.text = ""
    self.error_label.text = ""
    self.error_label.opacity = 0
    self.password_input.focus = True

    cast("CesarVaultApp", App.get_running_app()).master_password = ""
