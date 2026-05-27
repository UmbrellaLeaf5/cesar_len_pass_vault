"""
Экран ввода мастер-пароля.
"""

from typing import TYPE_CHECKING, cast

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen


if TYPE_CHECKING:
  from app.main import CesarVaultApp


Builder.load_file("app/screens/unlock.kv")


class UnlockScreen(Screen):
  """
  Экран ввода мастер-пароля.
  """

  password_input = ObjectProperty(None)
  error_label = ObjectProperty(None)

  def unlock(self) -> None:
    """Обработчик нажатия кнопки Unlock."""

    password = self.password_input.text.strip()

    if not password:
      self.error_label.text = "Введите пароль"
      self.error_label.opacity = 1

      return

    app = cast("CesarVaultApp", App.get_running_app())
    app.master_password = password
    self.manager.current = "vault"

  def on_enter(self, *args: object) -> None:
    """Сброс состояния при входе на экран."""

    self.password_input.text = ""
    self.error_label.text = ""
    self.error_label.opacity = 0
    self.password_input.focus = True

    cast("CesarVaultApp", App.get_running_app()).master_password = ""
