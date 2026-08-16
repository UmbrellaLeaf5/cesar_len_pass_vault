"""
Попап подтверждения мастер-пароля перед показом паролей.
"""

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup

from app.screens.mixins import ErrorScreenMixin
from app.utils import resource_path


# ----------------------------------------------------------------------------------------

Builder.load_file(resource_path("app/popups/confirm_show_passwords.kv"))

# ----------------------------------------------------------------------------------------


class ConfirmShowPasswordsPopup(Popup, ErrorScreenMixin):
  """Подтвердить мастер-пароль перед переходом в show-режим."""

  password_input = ObjectProperty(None)
  error_label = ObjectProperty(None)
  confirm_callback = ObjectProperty(None)

  master_password: str = ""

  # --------------------------------------------------------------------------------------

  def on_open(self) -> None:
    """Подготовить поле ввода при открытии попапа."""

    self.password_input.text = ""
    self.password_input.focus = True
    self._clear_error()

  # --------------------------------------------------------------------------------------

  def confirm(self) -> None:
    """Проверить пароль и показать пароли после успешного подтверждения."""

    if self.password_input.text != self.master_password:
      self._set_error("Invalid master password")
      self.password_input.select_all()

      return

    if self.confirm_callback:
      self.confirm_callback()

    self.dismiss()

  # --------------------------------------------------------------------------------------

  def cancel(self) -> None:
    """Закрыть попап, не изменяя режим показа паролей."""

    self.dismiss()
