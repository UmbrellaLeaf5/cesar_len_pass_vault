"""
Экран начальной настройки YA_TOKEN и REMOTE_PATH.
"""

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen

from app.screens.mixins import ErrorScreenMixin
from app.utils import resource_path
from cesar_len_pass_vault.config import config


# ----------------------------------------------------------------------------------------

Builder.load_file(resource_path("app/screens/setup.kv"))

# ----------------------------------------------------------------------------------------


class SetupScreen(Screen, ErrorScreenMixin):
  """
  Экран начальной настройки YA_TOKEN и REMOTE_PATH.
  """

  token_input = ObjectProperty(None)
  path_input = ObjectProperty(None)

  # --------------------------------------------------------------------------------------

  def on_enter(self, *args: object) -> None:
    self.token_input.text = ""
    self.path_input.text = ""
    self.token_input.focus = True
    self._clear_error()

  # --------------------------------------------------------------------------------------

  def save_and_continue(self) -> None:
    """Сохранить настройки и перейти к экрану разблокировки."""

    token = self.token_input.text.strip()
    path = self.path_input.text.strip()

    if not token:
      self._set_error("Enter Yandex Disk token")
      return

    if not path:
      self._set_error("Enter remote path")
      return

    # Сохраняем настройки
    config.save_settings(token, path)

    # Переходим к UnlockScreen
    self.manager.current = "unlock"
