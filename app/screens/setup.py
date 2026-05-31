"""
Экран начальной настройки YA_TOKEN и REMOTE_PATH.
"""

from typing import TYPE_CHECKING

from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.screenmanager import Screen

from app.utils import resource_path
from cesar_len_pass_vault.config import config


if TYPE_CHECKING:
  pass


# --------------------------------------------------------------------------------------

Builder.load_file(resource_path("app/screens/setup.kv"))

# --------------------------------------------------------------------------------------


class SetupScreen(Screen):
  """
  Экран начальной настройки YA_TOKEN и REMOTE_PATH.
  """

  token_input = ObjectProperty(None)
  path_input = ObjectProperty(None)
  error_label = ObjectProperty(None)
  _bg_color = ListProperty([0, 0, 0, 1])  # Чёрный по умолчанию

  # --------------------------------------------------------------------------

  def on_enter(self, *args: object) -> None:
    self.token_input.text = ""
    self.path_input.text = ""
    self.error_label.text = ""
    self.error_label.opacity = 0
    self._bg_color = [0, 0, 0, 1]  # Сброс фона к чёрному
    self.token_input.focus = True

  # --------------------------------------------------------------------------

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

  # MARK: private
  # --------------------------------------------------------------------------

  def _set_error(self, error_text: str) -> None:
    """Включить красный фон ошибки с текстом."""

    self._bg_color = [0.4, 0.05, 0.05, 1]  # Бледно-красный
    self.error_label.opacity = 1
    self.error_label.text = error_text
